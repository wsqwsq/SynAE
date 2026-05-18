import csv
import json

from create_t1_syn import syn_conversation_templates, syn_plan_templates_v2

input_fp = open("filled_templates.json", "r")
data = json.load(input_fp)

with open("syn_flights.csv", "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["sample_id", "Template", "Plan", "Filled_Template", "Filled_Plan"])
    for sample_id, content in data.items():
        conv_template_lines = syn_conversation_templates[sample_id].split("\n")
        plan_template_lines = syn_plan_templates_v2[sample_id].split("\n")
        conversation_lines = content["conversation"].split("\n")
        plan_lines = content["plan"].split("\n")

        max_len = max(len(conversation_lines), len(plan_lines))
        conv_template_lines += [""] * (max_len - len(conv_template_lines))
        plan_template_lines += [""] * (max_len - len(plan_template_lines))
        conversation_lines += [""] * (max_len - len(conversation_lines))
        plan_lines += [""] * (max_len - len(plan_lines))

        for conv_template_line, plan_template_line, conv_line, plan_line in zip(
            conv_template_lines, plan_template_lines, conversation_lines, plan_lines
        ):
            writer.writerow(
                [
                    sample_id,
                    conv_template_line,
                    plan_template_line,
                    conv_line,
                    plan_line,
                ]
            )
