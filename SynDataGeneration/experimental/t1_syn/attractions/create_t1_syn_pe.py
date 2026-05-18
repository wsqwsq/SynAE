import pandas as pd
import numpy as np
import transformers
from pe.llm import HuggingfaceLLM, Request


# Set experiment parameters
blank_probability = 0.5
hf_llm_generation_args = {
    "max_completion_tokens": 800,
    "batch_size": 8,
    "model_name_or_path": "google/gemma-3-12b-it",  # "meta-llama/Llama-3.1-8B-Instruct",
    "temperature": 0.6,
    # "top_p": 0.92,
    # "repetition_penalty": 1.1,
}

# Get list of conversations
real_data_filepath = "output_file_attraction_train_1.csv"
df = pd.read_csv(real_data_filepath)
conv_list = []
for g_name, g_df in df.groupby("ID"):
    conv = "\n".join(g_df["Filled_Template"])
    conv_list.append(conv)


# In each conversation, mask some parts randomly while preserving
# the structure of the conversation
def blank_sample(
    tokenizer, mask_token: int, sample: str, blank_probability: float
) -> str:
    input_ids = np.asarray(tokenizer.encode(sample, add_special_tokens=False))
    masked_indices = np.random.uniform(size=len(input_ids)) < blank_probability
    input_ids[masked_indices] = mask_token
    return tokenizer.decode(input_ids, skip_special_tokens=True)


# Use the same tokenizer as the model that will fill in the blanks
tokenizer = transformers.AutoTokenizer.from_pretrained(
    hf_llm_generation_args["model_name_or_path"]
)
mask_token = tokenizer.encode("_", add_special_tokens=False)[0]
masked_conv_list = []
for i, conv in enumerate(conv_list):
    masked_conv = ""
    for line in conv.split("\n"):
        prefix_part, separator, content = line.partition(": ")
        masked_content = blank_sample(
            tokenizer=tokenizer,
            mask_token=mask_token,
            sample=content,
            blank_probability=blank_probability,
        )
        masked_line = prefix_part + separator + masked_content
        masked_conv += masked_line + "\n"
    masked_conv_list.append(masked_conv)

# Fill in the masked conversations using an LLM
# 1. Create prompts for each masked conv
messages_list = []
system_message = {
    "role": "system",
    "content": "You are a helpful assistant. When given a conversation with blanks (underscores), fill them in naturally. Output only the completed conversation.",
}
for masked_conv in masked_conv_list:
    user_message = {
        "role": "user",
        "content": f"Fill in the blanks to complete this conversation:\n\n"
        f"assistant: H_____ What ____ of attractions are you looking for? Are you interested in _______, a__, or something else?\n"
        f"user: I'm interested in ___ and ____ attractions in __.\n"
        f"assistant: G_ has a lot to offer. Are you looking at specific ______ or re_____?\n"
        f"user: Yeah, I'm thinking of visiting Fre___ and M______.\n"
        f"assistant: Both _____o and ____his have great A__ and S_____ attractions. Let me tell you about some of them.\n"
        f"user: That sounds _____.\n\n"
        f"Completed conversation:\n"
        f"assistant: Hello! What kind of attractions are you looking for? Are you interested in history, art, or something else?\n"
        f"user: I'm interested in Art and Scenic attractions in GA.\n"
        f"assistant: GA has a lot to offer. Are you looking at specific cities or regions?\n"
        f"user: Yeah, I'm thinking of visiting Fresno and Memphis.\n"
        f"assistant: Both Fresno and Memphis have great Art and Scenic attractions. Let me tell you about some of them.\n"
        f"user: That sounds great.\n\n"
        f"Fill in the blanks to complete this conversation:\n\n{masked_conv}\nCompleted conversation:\n",
    }
    messages = [system_message, user_message]
    messages_list.append(messages)

# 2. Get responses from the LLM
llm = HuggingfaceLLM(**hf_llm_generation_args)
requests = [Request(messages=messages) for messages in messages_list]
responses = llm.get_responses(requests)


# Convert into dataframe
syn_ids_list = []
syn_conv_lines_list = []
for i, syn_conv in enumerate(responses):
    syn_conv_lines = syn_conv.split("\n")
    syn_ids_list.extend([i] * len(syn_conv_lines))
    syn_conv_lines_list.extend(syn_conv_lines)

syn_df = pd.DataFrame({"ID": syn_ids_list, "Filled_Template": syn_conv_lines_list})
syn_df.to_csv("syn_attractions_pe_gemma.csv", index=False)
