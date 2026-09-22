import pandas as pd
import numpy as np

def robust_parse_date(series):
    s = series.replace({"Date Not Captured": np.nan, "Pre-PQ Process": np.nan, "Not Applicable": np.nan})
    formats = ["%A, %B %d, %Y", "%m/%d/%Y", "%Y-%m-%d", "%d-%b-%y"]
    parsed = pd.Series(pd.NaT, index=s.index)
    for fmt in formats:
        mask = parsed.isna()
        if not mask.any():
            break
        parsed_fmt = pd.to_datetime(s[mask], format=fmt, errors="coerce")
        parsed.loc[mask] = parsed_fmt
    return parsed

def load_and_split_t2c(usecols=None):
    if usecols is not None:
        # ensure required columns for filtering and target creation are included
        req_base = ["Fulfillment Method", "On Time (OTD)", "Order Entry Date", "Order Number", "OTD OTIF Exclusion Flag"]
        for c in req_base:
            if c not in usecols:
                usecols.append(c)
        # remove duplicates
        usecols = list(dict.fromkeys(usecols))
        
    df = pd.read_csv("data/USAID_GHSC_PSM_Health_Commodity_Delivery_Dataset.csv", low_memory=False, usecols=usecols)
    
    df = df[df["Fulfillment Method"] == "Direct Drop"].copy()
    
    df["late_delivery"] = np.where(df["On Time (OTD)"] == "N", 1, 0)
    df = df[df["On Time (OTD)"].isin(["Y", "N"])].copy()
    
    df["Order Entry Date"] = robust_parse_date(df["Order Entry Date"])
    df = df.dropna(subset=["Order Entry Date"]).copy()
    df = df.sort_values("Order Entry Date").reset_index(drop=True)
    df["Entry_Year"] = df["Order Entry Date"].dt.year
    
    # Protocol A
    train_A = df[df["Entry_Year"] <= 2021].copy()
    val_A = df[df["Entry_Year"] == 2022].copy()
    test_A = df[df["Entry_Year"].isin([2023, 2024])].copy()
    
    # Protocol B
    train_B = df[df["Entry_Year"].between(2018, 2021)].copy()
    val_B = df[df["Entry_Year"] == 2022].copy()
    test_B = test_A.copy()
    
    # Summarize annual stats
    summary = df.groupby("Entry_Year")["late_delivery"].agg(['count', 'mean']).rename(columns={"count": "total_orders", "mean": "OTD_failure_rate"})
    summary.reset_index().to_csv("outputs/tables/t2c_temporal_summary.csv", index=False)
    
    return {"A": (train_A, val_A, test_A), "B": (train_B, val_B, test_B)}, df
