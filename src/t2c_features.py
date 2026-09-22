import pandas as pd
import numpy as np

def construct_quantity_features(df, train_df):
    df = df.copy()
    qty = df["Ordered Quantity"].fillna(0)
    train_qty = train_df["Ordered Quantity"].fillna(0)
    
    # Q1: log1p raw
    df["q1_log_raw"] = np.log1p(qty)
    
    # Hierarchical Fallbacks for medians
    global_med = train_qty.median()
    cat_med = train_df.groupby("Product Category")["Ordered Quantity"].median()
    tracer_med = train_df.groupby("Item Tracer Category")["Ordered Quantity"].median()
    prod_med = train_df.groupby("Product ID")["Ordered Quantity"].median()
    
    def get_fallback_median(row, level):
        if level == "Product ID" and row["Product ID"] in prod_med:
            return prod_med[row["Product ID"]]
        elif row["Item Tracer Category"] in tracer_med:
            return tracer_med[row["Item Tracer Category"]]
        elif row["Product Category"] in cat_med:
            return cat_med[row["Product Category"]]
        return global_med

    # Q2: Product relative
    df["q2_base"] = df.apply(lambda r: get_fallback_median(r, "Product ID"), axis=1).clip(lower=1)
    df["q2_prod_rel"] = np.log1p(qty / df["q2_base"])
    
    # Q3: Empirical Percentile
    # Pre-group training quantities
    prod_groups = train_df.groupby("Product ID")["Ordered Quantity"].apply(lambda x: np.sort(x.values)).to_dict()
    tracer_groups = train_df.groupby("Item Tracer Category")["Ordered Quantity"].apply(lambda x: np.sort(x.values)).to_dict()
    global_sorted = np.sort(train_qty.values)
    
    def get_percentile(row):
        q = row["Ordered Quantity"]
        if row["Product ID"] in prod_groups:
            arr = prod_groups[row["Product ID"]]
        elif row["Item Tracer Category"] in tracer_groups:
            arr = tracer_groups[row["Item Tracer Category"]]
        else:
            arr = global_sorted
            
        if len(arr) == 0:
            return 0.5
        return np.searchsorted(arr, q) / len(arr)
        
    df["q3_prod_pct"] = df.apply(get_percentile, axis=1)
    
    # Q4: Item Tracer Category relative
    df["q4_base"] = df.apply(lambda r: get_fallback_median(r, "Item Tracer Category"), axis=1).clip(lower=1)
    df["q4_tracer_rel"] = np.log1p(qty / df["q4_base"])
    
    return df
