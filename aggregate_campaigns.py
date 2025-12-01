import pandas as pd

# 1. Load raw ad-group level data
df = pd.read_csv("data/processed/marketing/campaigns_v1.csv")

# 2. Clean column names (remove whitespace)
df.columns = df.columns.str.strip()

# 3. Set up aggregation for pivot
# Use sum for numeric columns, use first value for other columns
numeric_cols = [
    "budget", "actual_spend", "impressions", "clicks", "views",
    "sessions", "conversions", "revenue"
]

# Filter numeric columns to include only those that actually exist in the dataframe
numeric_cols = [c for c in numeric_cols if c in df.columns]

# 4. Pivot (use pivot_table instead of groupby)
agg_dict = {col: "sum" for col in numeric_cols}
text_cols = ["campaign_name", "brand_name", "category", "country", "objective", "currency"]
for col in text_cols:
    if col in df.columns:
        agg_dict[col] = "first"

df_summary = df.pivot_table(
    index="campaign_id",
    values=list(agg_dict.keys()),
    aggfunc=agg_dict,
    fill_value=0
).reset_index()

# 5. Export summarized dataset
output_path = "data/processed/marketing/campaigns_summary.csv"
df_summary.to_csv(output_path, index=False)

print(f"[OK] Pivoted to {len(df_summary)} campaigns and saved as {output_path}")