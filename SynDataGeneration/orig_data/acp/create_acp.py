import pandas as pd

acp_app_bool_df = pd.read_parquet("acp_app_bool.parquet")
acp_prog_bool_df = pd.read_parquet("acp_prog_bool.parquet")
orig_df = pd.concat([acp_app_bool_df, acp_prog_bool_df])
orig_df.to_csv("acp_app_prog.csv", index=False)
