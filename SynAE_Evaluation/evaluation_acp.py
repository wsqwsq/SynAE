import ast
from scipy.stats import wasserstein_distance
import numpy as np
import csv
from tqdm import tqdm
from collections import Counter
import torch
from sentence_transformers import SentenceTransformer
from precision_recall import knn_precision_recall_features
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
import seaborn as sns
import re
import random
import faiss
import math
from multiprocessing import Pool
import argparse
import os
from lark import Lark
import sys
import json

from numpy import cov
from numpy import trace
from numpy import iscomplexobj
from collections import defaultdict
from scipy.linalg import sqrtm
from sklearn.decomposition import PCA

from vendi_score import vendi
import Levenshtein

csv.field_size_limit(sys.maxsize)

### -------- CFG -----------
USER = "user:"
ASSIS = "assistant:"

GRAMMAR = fr"""
    bfcl: preamble? conversation (conversation)*
    preamble: /(?s).+?(?={USER})/
    conversation: user
    user: "{USER}" user_string

    user_string: ESCAPED_STRING | /(?s).+?(?=(?:{USER}|$))/

    %import common.ESCAPED_STRING
    %import common.WS
    %ignore WS
"""
### ----------------------------

fr"""
ShareGPT: conversation (conversation)*  // ShareGPT contains one or more conversation rounds
conversation: query response    // Each conversation round contains a query and a response
query: "HUMAN: " query_text     // The query starts with "HUMAN: "
response: "GPT: " response_text     // The response starts with "GPT: "
query_text: /(?s).+?(?=(?:GPT: |$))/    // The query text ends before "GPT: " or the end of the string
response_text: /(?s).+?(?=(?:HUMAN: |$))/   // The response text ends before "HUMAN: " or the end of the string
"""

parser = Lark(GRAMMAR, start="bfcl")

TOTAL_NUM_SAMPLES = 260

current_folder = os.path.dirname(os.path.abspath(__file__))
priv_path = os.path.join(current_folder, '../ori_data')
priv_data_path = os.path.join(priv_path, 'ori_data.csv')
priv_attr_path = os.path.join(priv_path, 'ori_attr.csv')

PRI_EMB, PRI_USER_EMB, PRI_ASSIS_EMB = 'pri_emb', 'pri_human_emb', 'pri_gpt_emb'
PRI_OUTPUT = 'pri_output'

ATTR = ['primary_api', 'secondary_api', 'conv_len']

cached_embedding = {
    PRI_EMB: None,
    PRI_USER_EMB: None,
    PRI_ASSIS_EMB: None,
    PRI_OUTPUT: None
}


attraction_tools = ["search_attractions", 
                    "filter_attractions", 
                    "search_nearest",
                    "sort_results",
                    "get_results_from_cache", 
                    "save_to_cache"]


def get_distance(a, b, tp: str = 'wasserstein') -> float:
    """
    Compute distance between distributions induced by samples a and b.
    tp: 'wasserstein' or 'tv' (total variation).
    Returns np.inf if either input is empty.
    """
    a_list, b_list = list(a), list(b)
    if not a_list or not b_list:
        return np.inf

    count_a, count_b = Counter(a_list), Counter(b_list)
    support = sorted(set(count_a.keys()) | set(count_b.keys()))

    pmf_a = np.array([count_a[k] for k in support], dtype=float)
    pmf_b = np.array([count_b[k] for k in support], dtype=float)
    pmf_a /= pmf_a.sum()
    pmf_b /= pmf_b.sum()

    if tp == 'wasserstein':
        return wasserstein_distance(support, support, u_weights=pmf_a, v_weights=pmf_b)
    # TV distance
    return 0.5 * np.sum(np.abs(pmf_a - pmf_b))


class CallExtractor(ast.NodeVisitor):
    def __init__(self):
        self.calls = []

    def visit_Call(self, node):
        # continue traversal first to capture nested calls
        self.generic_visit(node)
        func = node.func
        if isinstance(func, ast.Name):
            self.calls.append(func.id)
        elif isinstance(func, ast.Attribute):
            self.calls.append(func.attr)


def extract_tool_calls(code: str) -> list[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    extractor = CallExtractor()
    extractor.visit(tree)
    return extractor.calls


def eval_tool_length(func_list1, func_list2):
    lengths1 = [len(funcs) for funcs in func_list1]
    lengths2 = [len(funcs) for funcs in func_list2]
    return get_distance(lengths1, lengths2, tp='wasserstein')


def eval_k_step_tool_calls(func_list1, func_list2, k=1):
    tools = list(set([f for seq in func_list1 for f in seq] + [f for seq in func_list2 for f in seq]))
    tool_set = set(tools)

    if k == 1:
        # collect tool calls in order across all sequences
        a = [f for seq in func_list1 for f in seq if f in tool_set]
        b = [f for seq in func_list2 for f in seq if f in tool_set]
        return get_distance(a, b, tp='tv')

    # k > 1: build conditional counts P(next | history_of_length_k-1)

    def build_conditionals(func_lists):
        hist_counts = Counter()
        cond_counts = defaultdict(Counter)
        total_windows = 0
        for seq in func_lists:
            seq_f = [f for f in seq if f in tool_set]
            L = len(seq_f)
            if L < k:
                continue
            for i in range(L - k + 1):
                hist = tuple(seq_f[i:i + k - 1])
                nxt = seq_f[i + k - 1]
                hist_counts[hist] += 1
                cond_counts[hist][nxt] += 1
                total_windows += 1
        return hist_counts, cond_counts, total_windows

    h1, c1, N1 = build_conditionals(func_list1)
    h2, c2, N2 = build_conditionals(func_list2)
    if (N1 + N2) == 0:
        return np.inf

    all_histories = set(h1.keys()) | set(h2.keys())
    expected_tv = 0.0
    denom = (N1 + N2)
    for hist in all_histories:
        cnts1 = c1.get(hist, Counter())
        cnts2 = c2.get(hist, Counter())

        v1 = np.array([cnts1[t] for t in tools], dtype=float)
        v2 = np.array([cnts2[t] for t in tools], dtype=float)
        if v1.sum() > 0:
            v1 /= v1.sum()
        if v2.sum() > 0:
            v2 /= v2.sum()

        tv = 0.5 * np.sum(np.abs(v1 - v2))
        weight = (h1.get(hist, 0) + h2.get(hist, 0)) / denom
        expected_tv += weight * tv

    return expected_tv



def get_len(dataset, index=None):     # index: [lower, upper)
    length = []
    if index is None:
        for sample in dataset:
            length.append(len(sample.split()))
        return length

    start, end = index
    for i, sample in enumerate(dataset, 1):  # preserve original 1-based counting
        if i < start or i >= end:
            continue
        length.append(len(sample.split()))
    return length


def get_ttr(dataset):
    ttr = []
    token_set = []

    for sample in dataset:
        token_set += sample.strip().split()
    unique_tokens = set(token_set)
    ttr.append(len(unique_tokens) / len(token_set))

    return np.mean(ttr)


def CFG_valid(sample, ignore = False):
    if ignore:
        return True
    if not isinstance(sample, str) or not sample.strip():
        return False
    try:
        parser.parse(sample)
        return True
    except Exception:
        return False


def get_statements(sample):     # get the statement texts of queries and responses; max_num: 10
    return sample.strip().split('\n')[:2]



def get_statement_length(dataset):
    lengths = []
    for sample in dataset:
        statements = get_statements(sample)
        lengths.append(sum(len(s.split()) for s in statements))
    return lengths


def extract_features(
        data,
        batch_size = 100,
        model_name = "stsb-roberta-base-v2",
        cache = None):
    # If available, the model is automatically executed on the GPU. You can specify the device for the model like this:

    if cache and cached_embedding[cache] is not None:
        return cached_embedding[cache]
    
    model = SentenceTransformer(model_name)  # device='cuda',
    model.eval()

    with torch.no_grad():
        sentence_embeddings = []
        for i in tqdm(range(math.ceil(len(data) / batch_size)), desc='Get Embedding'):
            embeddings = model.encode(
                data[i * batch_size:(i + 1) * batch_size])
            if len(embeddings) > 0:
                sentence_embeddings.append(embeddings)
    sentence_embeddings = [] if sentence_embeddings == [] else np.concatenate(sentence_embeddings)
    del model

    if cache:
        cached_embedding[cache] = sentence_embeddings
    return sentence_embeddings


def get_embedding_cosine_similarity(dataset, private = True):
    human_statement = []
    for sample in dataset:
        h_s = get_statements(sample)
        human_statement += h_s
    if private:
        cache_human = PRI_USER_EMB
    else:
        cache_human = None
    embedding_human = extract_features(human_statement, cache=cache_human)
    n = embedding_human.shape[0]
    if n == 0:
        return []
    embedding_pre = embedding_human[:-1]
    embedding_post = embedding_human[1:]
    return [cosine_similarity([embedding_pre[i]], [embedding_post[i]])[0][0] for i in range(0, n-1, 2)]


def get_attr_array(data, category):
    attr = []
    for sample in data:
        found = False
        for word in category:
            if word.lower() in sample.lower():
                attr.append(word)
                found = True
        if not found:
            attr.append('Other')
    return attr


def get_total_attr(total_category):
    total_attr = []
    for cate1, cate2, cate3 in zip(total_category[ATTR[0]], total_category[ATTR[1]], total_category[ATTR[2]]):
        total_attr.append([cate1, cate2, cate3])
    return total_attr


def save_emb_similarity(data_pri, data_syn, path, name, plot=False):
    os.makedirs(path, exist_ok=True)

    priv_file = os.path.join(priv_path, f'{name}.npy')
    syn_file = os.path.join(path, f'{name}.npy')

    if os.path.exists(priv_file):
        cos_pri = np.load(priv_file)
    else:
        cos_pri = np.asarray(get_embedding_cosine_similarity(data_pri, private=True))

    if os.path.exists(syn_file):
        cos_syn = np.load(syn_file)
    else:
        cos_syn = np.asarray(get_embedding_cosine_similarity(data_syn, private=False))

    distance = get_distance(cos_pri, cos_syn)

    if not os.path.exists(priv_file):
        np.save(priv_file, cos_pri)
    if not os.path.exists(syn_file):
        np.save(syn_file, cos_syn)

    if plot:
        plt.hist(cos_pri, bins=50, density=True, alpha=0.5, label='private')
        plt.hist(cos_syn, bins=50, density=True, alpha=0.5, label='synthetic')
        plt.xlim(0, 1)
        plt.legend(fontsize=15)
        plt.title(name, fontsize=19)
        plt.savefig(os.path.join(path, f'{name}.pdf'))
        plt.clf()

    return distance


def knn_precision_recall(main_features, compared_features, 
                         num_nearest_neighbor=3, mode='L2'):
    """
    Args:
        main_features (np.ndarray): NxD array of reference embeddings.
        compared_features (np.ndarray): MxD array of query embeddings.
        num_nearest_neighbor (int): k for k-NN search.
        mode (str): 'L2', 'IP' (inner product), or 'cos_sim' (cosine similarity).

    Returns:
        float: |unique_ids_found| / N
    """
    # Ensure numpy float32 contiguous arrays for faiss
    main_features = np.ascontiguousarray(np.asarray(main_features, dtype=np.float32))
    compared_features = np.ascontiguousarray(np.asarray(compared_features, dtype=np.float32))

    # Normalize if cosine similarity mode
    if mode == 'cos_sim':
        faiss.normalize_L2(main_features)
        faiss.normalize_L2(compared_features)

    # create index on CPU
    if mode == 'L2':
        index = faiss.IndexFlatL2(main_features.shape[1])
    elif mode == 'IP' or mode == 'cos_sim':
        index = faiss.IndexFlatIP(main_features.shape[1])
    else:
        raise Exception(f'Unknown mode {mode}')

    # move index to GPU if available
    if torch.cuda.is_available():
        res = faiss.StandardGpuResources()
        index = faiss.index_cpu_to_gpu(res, 0, index)

    index.add(main_features)

    # batch the search to avoid large memory use
    step = 10
    list_ids = []
    M = len(compared_features)
    if M == 0:
        return 0.0
    for i in range(math.ceil(M / step)):
        start = i * step
        end = min((i + 1) * step, M)
        _, ids = index.search(compared_features[start:end], k=num_nearest_neighbor)
        list_ids.extend(ids.flatten().tolist())

    return len(set(list_ids)) / float(len(main_features))


def calculate_fid(act1, act2):
    """
    Compute the Frechet Inception Distance (FID) between two sets of activations.

    Args:
        act1 (np.ndarray): NxD array of activations from distribution 1.
        act2 (np.ndarray): MxD array of activations from distribution 2.

    Returns:
        float: FID score (lower means more similar). Returns np.inf for invalid inputs.
    """
    act1 = np.asarray(act1, dtype=np.float64)
    act2 = np.asarray(act2, dtype=np.float64)
    if act1.size == 0 or act2.size == 0:
        return np.inf

    # ensure 2D
    if act1.ndim == 1:
        act1 = act1.reshape(1, -1)
    if act2.ndim == 1:
        act2 = act2.reshape(1, -1)

    # calculate mean and covariance statistics
    mu1 = act1.mean(axis=0)
    mu2 = act2.mean(axis=0)
    sigma1 = cov(act1, rowvar=False)
    sigma2 = cov(act2, rowvar=False)

    # numerical stability: add small epsilon to diagonal if needed
    eps = 1e-6
    if sigma1.size == 0 or sigma2.size == 0:
        return np.inf
    sigma1 += np.eye(sigma1.shape[0]) * eps
    sigma2 += np.eye(sigma2.shape[0]) * eps

    # sum squared difference between means
    ssdiff = np.sum((mu1 - mu2) ** 2.0)

    # sqrt of product between covariances
    covmean = sqrtm(sigma1.dot(sigma2))

    # handle numerical issues (small imaginary components)
    if iscomplexobj(covmean):
        # if imaginary parts are negligible, keep real part
        if np.max(np.abs(covmean.imag)) < 1e-6:
            covmean = covmean.real
        else:
            covmean = covmean.real  # fallback to real part

    # calculate FID
    fid = ssdiff + trace(sigma1 + sigma2 - 2.0 * covmean)
    return float(np.real_if_close(fid))


def embedding_distribution(emb_pri, emb_syn_list, path, name_list):
    """
    Compute a joint PCA over a private embedding set and one or more synthetic embedding sets,
    then save 2D scatter plots comparing the private data to each synthetic set.

    The function:
    - Performs joint PCA on [emb_pri] + emb_syn_list.
    - Chooses components 2 and 3 for plotting if at least 4 components are available,
      otherwise falls back to components 0 and 1.
    - Saves one PDF per synthetic dataset to path/name_list[i].pdf (skips if file exists).

    Args:
        emb_pri (np.ndarray): N x D private embeddings.
        emb_syn_list (list[np.ndarray]): list of M_i x D synthetic embeddings.
        path (str): directory to save plots.
        name_list (list[str]): filenames (without extension) for each synthetic set.

    Notes:
        - If any input is empty or incompatible, the function returns without saving.
    """
    os.makedirs(path, exist_ok=True)

    # Basic validation
    if emb_pri is None or emb_syn_list is None or name_list is None:
        return
    if len(emb_syn_list) != len(name_list):
        return

    # Filter out empty synthetic embeddings but keep name mapping consistent
    valid_pairs = [(emb, name) for emb, name in zip(emb_syn_list, name_list) if emb is not None and getattr(emb, "shape", (0,))[0] > 0]
    if len(valid_pairs) == 0:
        return
    emb_syn_list, name_list = zip(*valid_pairs)

    if emb_pri is None or getattr(emb_pri, "shape", (0,))[0] == 0:
        return

    # Combine embeddings for joint PCA
    try:
        combined_embeddings = np.vstack([emb_pri] + list(emb_syn_list))
    except Exception:
        return

    # Determine feasible number of PCA components
    n_samples, n_features = combined_embeddings.shape
    n_comp = min(4, n_samples, n_features)
    if n_comp < 2:
        return

    pca = PCA(n_components=n_comp)
    reduced = pca.fit_transform(combined_embeddings)

    # Choose plot axes: prefer components 2 & 3 when available, else 0 & 1
    if n_comp >= 4:
        x_idx, y_idx = 2, 3
    else:
        x_idx, y_idx = 0, 1

    # Split reduced back into private and synthetic parts
    start = emb_pri.shape[0]
    emb_pri_reduced = reduced[:start]
    emb_syn_reduced_list = []
    for emb in emb_syn_list:
        end = start + emb.shape[0]
        emb_syn_reduced_list.append(reduced[start:end])
        start = end

    # Plot and save each comparison
    for emb_syn_reduced, name in zip(emb_syn_reduced_list, name_list):
        save_path = os.path.join(path, f'{name}.pdf')
        if os.path.exists(save_path):
            continue

        plt.figure(figsize=(8, 8))
        plt.scatter(emb_pri_reduced[:, x_idx], emb_pri_reduced[:, y_idx], alpha=0.5, label='Private Data', color='orange')
        plt.scatter(emb_syn_reduced[:, x_idx], emb_syn_reduced[:, y_idx], alpha=0.5, label='Synthetic Data', color='blue')
        plt.legend(fontsize=15)
        plt.savefig(save_path)
        plt.clf()



### --- EVALUATION --- ###
# Input: private & sythetic datasets; Output: a dictionary of evaluation results

## -- Metrics for Task Instruction -- ##
def evaluate_length(data1, data2):
    len1, len2 = get_statement_length(data1), get_statement_length(data2)
    user_distance = get_distance(len1, len2)
    return {'Task: token length': user_distance}

def evaluate_precision_recall(data_pri, data_syn):
    fea_pri, fea_syn = extract_features(data_pri, cache=PRI_EMB), extract_features(data_syn)
    state = knn_precision_recall_features(fea_pri, fea_syn, nhood_sizes=[3])
    #print(f"Precision: {state['precision']}")
    return {'Task: precision': state['precision'], 'Task: recall': state['recall']}

def evaluate_fid(data_pri, data_syn):
    fea_pri, fea_syn = extract_features(data_pri, cache=PRI_EMB), extract_features(data_syn)
    fid = calculate_fid(fea_syn, fea_pri)
    #print(f"FID: {fid}")
    return {'Task: FID': fid}

def evaluate_pair_similarity(data_pri, data_syn, path):
    name = 'context_user_cos'
    assistant_user_distance = save_emb_similarity(data_pri, data_syn, path, name)
    return {'Task: user-user pair similarity': assistant_user_distance}

def evaluate_CFG_original(data_pri, data_syn):
    cnt, total_num = 0, len(data_syn)
    for sample in data_syn:
        if CFG_valid(sample):
            cnt += 1
    return {'Task: CFG Validity': cnt / total_num}
    
def evaluate_CFG(data_pri, data_syn):
    # The synthetic dataset only contains CFG valid samples after data post-processing
    return {'Task: CFG Validity': len(data_syn) / TOTAL_NUM_SAMPLES}

def evaluate_TTR(data_pri, data_syn):
    return {'Task: TTR': get_ttr(data_syn)}

def evaluate_attr(data_pri, data_syn, attr):
    distance = get_distance(data_pri, data_syn, tp = 'TV')
    return {f'Task: {attr} similarity': distance}


## -- Metrics for Tool Calling -- ##
def evaluate_tool_calling(actuals, predictions):
    func_list1 = [extract_tool_calls(code) for code in actuals]
    func_list2 = [extract_tool_calls(code) for code in predictions]

    length_distance = eval_tool_length(func_list1, func_list2)
    k1_distance = eval_k_step_tool_calls(func_list1, func_list2, k=1)
    k2_distance = eval_k_step_tool_calls(func_list1, func_list2, k=2)
    k3_distance = eval_k_step_tool_calls(func_list1, func_list2, k=3)

    return {
        'Tool Calling: length distance': length_distance,
        'Tool Calling: 1-step TV distance': k1_distance,
        'Tool Calling: 2-step TV distance': k2_distance,
        'Tool Calling: 3-step TV distance': k3_distance
    }


## -- Metrics for Output -- ##
def evaluate_output(data_pri, data_syn):
    fea_pri, fea_syn = extract_features(data_pri, cache=PRI_OUTPUT), extract_features(data_syn)
    state = knn_precision_recall_features(fea_pri, fea_syn, nhood_sizes=[3])
    fid = calculate_fid(fea_syn, fea_pri)
    return {'Output: precision': state['precision'],
            'Output: recall': state['recall'],
            'Output: FID': fid}

## -- Metrics for Diversity -- ##
def evaluate_attr_entropy(data_syn):
    attr_list = get_statement_length(data_syn)
    attr_counts = Counter(attrs for attrs in attr_list)
    total = sum(attr_counts.values())
    attr_proportion = {attrs: count / total for attrs, count in attr_counts.items()}
    entropy = -sum(p * math.log(p) for p in attr_proportion.values())
    return {f'Diversity: attribute entropy': entropy}

def evaluate_vendi(data_syn):
    instruction = data_syn['Data']
    instr_emb = extract_features(instruction)
    sim_matrix = cosine_similarity(instr_emb, instr_emb)
    vendi_instr = float(vendi.score_K(sim_matrix))

    output = data_syn['Output']
    output_emb = extract_features(output)
    sim_matrix = cosine_similarity(output_emb, output_emb)
    vendi_output = float(vendi.score_K(sim_matrix))

    return {'Diversity: Vendi instruction': vendi_instr, 
            'Diversity: Vendi output': vendi_output}



## -- Validity Rate (Placeholder) -- ##
def evaluate_validity_output(data_pri, data_syn):
    # TODO: requires LLM judge (vLLM self-consistency)
    return {'Validity: output rate': None}


## -- Downstream Metrics (Placeholder) -- ##
def evaluate_downstream(data_pri, data_syn):
    # TODO: not yet implemented
    return {
        'Downstream: task difficulty output': None,
        'Downstream: ranking divergence output': None,
    }


### --- End-to-End Evaluation --- ###
# Evaluate the synthetic dataset against the private dataset on all metrics and save results to a json file
FUNC_LIST = [evaluate_length,
             evaluate_precision_recall,
             evaluate_fid,
             evaluate_pair_similarity,
             evaluate_output,
             evaluate_attr_entropy,
             evaluate_vendi,
             evaluate_validity_output,
             evaluate_downstream]

COLUMN = ['Data', 'Output']


def read_data_from_csv(data_path):
    """
    Read CSV file and keep columns:
      'Filled_Template', 'Filled_Plan', 'Output', 'City', 'Attraction'
    Returns a dict with those lists plus 'full_text' which concatenates
    template, plan and output for each row.
    """
    data = {c: [] for c in COLUMN}

    if not os.path.exists(data_path):
        print(f"File not found: {data_path}")
        return data

    with open(data_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            for c in COLUMN:
                val = row.get(c, '') or ''
                val = val.strip()
                data[c].append(val)

    return data


def save_or_update_results_json(save_path, method_name, results):
    """
    Save results to {save_path}/{method_name}.json.
    If the file exists, load it (expects a dict), shallow-merge with `results`, and overwrite.
    Returns the JSON file path.
    """
    os.makedirs(save_path, exist_ok=True)
    json_path = os.path.join(save_path, f"{method_name}.json")

    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            try:
                old = json.load(f)
            except json.JSONDecodeError:
                old = {}

        if old is None:
            old = {}
        if not isinstance(old, dict):
            raise ValueError(f"Expected a JSON object (dict) in {json_path}, got {type(old).__name__}")

        old.update(results)  # shallow merge
        to_write = old
    else:
        to_write = results

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(to_write, f, indent=4)


def evaluate_all(syn_data_path, save_path, method_name = "test"):
    data_pri = read_data_from_csv(priv_data_path)
    data_syn = read_data_from_csv(syn_data_path)

    results = {'Method': method_name}
    for func in FUNC_LIST:
        if func == evaluate_pair_similarity:
            res = func(data_pri['Data'], data_syn['Data'], 
                       path=os.path.dirname(syn_data_path))
        elif func == evaluate_tool_calling:
            res = func(data_pri['Tool Calls'], data_syn['Tool Calls'])
        elif func == evaluate_attr_entropy:
            res = func(data_syn)
        elif func == evaluate_vendi:
            res = func(data_syn)
        else:
            res = func(data_pri['Data'], data_syn['Data'])
        results.update(res)

    save_or_update_results_json(save_path, method_name, results)

    return results



if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--syn_data_path', type=str, default="../syn_data/test/test_data.csv",
                        help='Path to the synthetic data CSV file.')
    arg_parser.add_argument('--save_path', type=str, default="../eval_results",
                        help='Path to save the evaluation results JSON file.')
    arg_parser.add_argument('--attr_category_path', type=str, default="../ori_data/category.csv",
                        help='Path to the attribute category CSV file.')
    arg_parser.add_argument('--method_name', type=str, default="test",
                        help='Name of the evaluation method.')
    args = arg_parser.parse_args()

    #evaluate_all(args.syn_data_path, args.save_path, args.attr_category_path, args.method_name)

    syn_data_path_prefix = "../syn_data/"
    syn_data_method_list = ['oversample_01', 'oversample_03', 'oversample_05', 'oversample_07',
                            'oversample_09', 'oversample_0', 'oversample_1',
                            'blankfilling_01', 'blankfilling_03', 'blankfilling_05', 'blankfilling_07',
                            'blankfilling_09', 'blankfilling_0',
                            'fewshot_0', 'fewshot_1_fix', 'fewshot_3_fix', 'fewshot_5_fix',
                            'fewshot_1_random', 'fewshot_3_random', 'fewshot_5_random']
    syn_data_file_name = 'syn_data.csv'

    for method in syn_data_method_list:
        syn_data_path = os.path.join(syn_data_path_prefix, method, syn_data_file_name)
        evaluate_all(syn_data_path, args.save_path, method_name=method)