import json
from json import JSONEncoder
from datetime import date, datetime
import pandas as pd
import yaml
from pydantic import BaseModel, ConfigDict


# Ideally, the schema should match the original Tau2 Task schema.
# This would let us use synthetic tasks in the Tau2 pipeline without any changes.
# See: https://github.com/sierra-research/tau2-bench/blob/main/src/tau2/data_model/tasks.py
# The version below is a more permissible one, and might cause issues while
# running the Tau2 pipeline.
class Tau2TestSchema(BaseModel):
    id: str
    description: dict
    user_scenario: dict
    ticket: str
    initial_state: dict = {}
    evaluation_criteria: dict = {}

    model_config = ConfigDict(extra="ignore")


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        # Let the base class default method raise the TypeError
        return super().default(obj)


filepath = "results/text/tau2_syn/synthetic_text/000000010.csv"
df = pd.read_csv(filepath)


def tau2_df_to_json(df_data: pd.DataFrame):
    """Convert DataFrame with YAML strings back to JSON objects."""
    json_objects = []
    success_count = 0
    failed_count = 0

    for yaml_str in df_data["text"]:
        try:
            # Parse YAML to Pydantic object
            yaml_data = yaml.safe_load(yaml_str)
            obj = Tau2TestSchema(**yaml_data)
            if obj:
                obj.id = f"task_{success_count}"
                json_objects.append(obj.model_dump())
                success_count += 1
            else:
                failed_count += 1
        except yaml.YAMLError as e:
            print(f"Failed to parse YAML: {e}")
            print(f"Problematic YAML: {yaml_str[:200]}...")
            failed_count += 1

    print(f"Successfully parsed: {len(json_objects)}")
    print(f"Failed to parse: {failed_count}")

    return json_objects


json_data = tau2_df_to_json(df)

# Save JSON objects as a JSON array file
with open("tau2_llama3_syn_mock_tasks.json", "w") as fp:
    json.dump(json_data, fp, indent=2, cls=CustomJSONEncoder)
