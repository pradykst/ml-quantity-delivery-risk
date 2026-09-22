import os
import sys
import gc
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from catboost import CatBoostClassifier
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss, log_loss
from sklearn.calibration import CalibratedClassifierCV
try:
    from sklearn.frozen import FrozenEstimator
except ImportError:
    class FrozenEstimator:
        def __init__(self, estimator=None):
            self.estimator = estimator
        def predict_proba(self, X):
            return self.estimator.predict_proba(X)
        def fit(self, X, y=None, **kwargs):
            return self
        @property
        def classes_(self):
            return self.estimator.classes_
        def __call__(self, estimator):
            self.estimator = estimator
            return self
from sklearn.isotonic import IsotonicRegression
from src.t2c_data import load_and_split_t2c
from src.t2c_features import construct_quantity_features

def wilson_ci(k, n, z=1.96):
    if n == 0: return 0.0, 0.0
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2*n)) / denom
    spread = z * np.sqrt(p*(1-p)/n + z**2/(4*n**2)) / denom
    return max(0.0, center - spread), min(1.0, center + spread)

STRICT_CATS = [
    "Country", "Order Type", "Item Tracer Category", "Product Category", 
    "Product ID", "UOM", "D365 Health Element", "D365 Funding Source", 
    "Fiscal_Year_Funding", "calendar_month"
]
EXTENDED_CATS = STRICT_CATS + ["Transportation Mode", "Framework Contract", "Vendor Incoterm", "Destination Incoterm"]
EXTENDED_NUMS = ["Illustrative Price", "Estimated Lead Time in Days"]

def ensure_columns(df):
    if "calendar_month" not in df.columns:
        df["calendar_month"] = df["Order Entry Date"].dt.month.fillna(-1).astype(int).astype(str)
    for c in EXTENDED_CATS:
        if c not in df.columns:
            df[c] = "Missing"
        else:
            df[c] = df[c].fillna("Missing").astype(str)
    for c in EXTENDED_NUMS:
        if c not in df.columns:
            df[c] = 0.0
        else:
            df[c] = df[c].fillna(0.0).astype(float)
    return df

def get_calibration_metrics(y_true, y_prob):
    brier = brier_score_loss(y_true, y_prob)
    ll = log_loss(y_true, y_prob)
    bins = np.linspace(0, 1, 11)
    binids = np.digitize(y_prob, bins) - 1
    ece = 0
    for i in range(10):
        mask = binids == i
        if np.any(mask):
            ece += np.abs(y_prob[mask].mean() - y_true[mask].mean()) * np.mean(mask)
    eps = 1e-15
    p_clip = np.clip(y_prob, eps, 1-eps)
    log_odds = np.log(p_clip / (1 - p_clip))
    from sklearn.linear_model import LogisticRegression
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if len(np.unique(y_true)) > 1 and np.var(log_odds) > 0:
            lr = LogisticRegression(penalty=None)
            lr.fit(log_odds.reshape(-1, 1), y_true)
            slope = lr.coef_[0][0]
            intercept = lr.intercept_[0]
        else:
            slope, intercept = np.nan, np.nan
    return brier, ll, ece, slope, intercept

def bootstrap_diff(y_true, p1, p2, p1_cal, p2_cal, groups=None, n=1000, seed=42):
    np.random.seed(seed)
    n_obs = len(y_true)
    diffs_auc, diffs_pr, diffs_brier = [], [], []
    y_true_v = y_true.values if isinstance(y_true, pd.Series) else y_true
    
    if groups is not None:
        # Give every missing value a unique integer
        g_arr = []
        c = -1
        for g in groups:
            if pd.isna(g) or str(g) == 'nan':
                g_arr.append(c)
                c -= 1
            else:
                g_arr.append(g)
        # Factorize to get integers 0...K
        import pandas as pd_local
        group_ids = pd_local.factorize(g_arr)[0]
        unique_groups = np.unique(group_ids)
        group_to_indices = {g: np.where(group_ids == g)[0] for g in unique_groups}
    else:
        unique_groups = None
        group_to_indices = None
        
    for _ in range(n):
        if groups is not None:
            sampled_groups = np.random.choice(unique_groups, size=len(unique_groups), replace=True)
            idx = np.concatenate([group_to_indices[g] for g in sampled_groups])
        else:
            idx = np.random.randint(0, n_obs, n_obs)
            
        yt = y_true_v[idx]
        if len(np.unique(yt)) < 2: continue
        
        pr1, pr2 = p1[idx], p2[idx]
        pc1, pc2 = p1_cal[idx], p2_cal[idx]
        
        diffs_auc.append(roc_auc_score(yt, pr1) - roc_auc_score(yt, pr2))
        diffs_pr.append(average_precision_score(yt, pr1) - average_precision_score(yt, pr2))
        diffs_brier.append(brier_score_loss(yt, pc2) - brier_score_loss(yt, pc1))
        
    return {
        "delta_roc_auc_mean": np.mean(diffs_auc) if diffs_auc else 0,
        "delta_roc_auc_lower": np.percentile(diffs_auc, 2.5) if diffs_auc else 0,
        "delta_roc_auc_upper": np.percentile(diffs_auc, 97.5) if diffs_auc else 0,
        "delta_pr_auc_mean": np.mean(diffs_pr) if diffs_pr else 0,
        "delta_pr_auc_lower": np.percentile(diffs_pr, 2.5) if diffs_pr else 0,
        "delta_pr_auc_upper": np.percentile(diffs_pr, 97.5) if diffs_pr else 0,
        "delta_brier_mean": np.mean(diffs_brier) if diffs_brier else 0,
        "delta_brier_lower": np.percentile(diffs_brier, 2.5) if diffs_brier else 0,
        "delta_brier_upper": np.percentile(diffs_brier, 97.5) if diffs_brier else 0,
        "bootstrap_type": "ORDER_CLUSTER_BOOTSTRAP" if groups is not None else "LINE_ITEM_BOOTSTRAP"
    }

def bootstrap_temporal_contrast(y_true, p_A_raw, p_B_raw, p_A_cal, p_B_cal, p0_A_raw, p0_B_raw, p0_A_cal, p0_B_cal, groups=None, n=1000, seed=42):
    np.random.seed(seed)
    n_obs = len(y_true)
    diffs_auc, diffs_pr, diffs_brier = [], [], []
    y_true_v = y_true.values if isinstance(y_true, pd.Series) else y_true
    
    if groups is not None:
        g_arr = []
        c = -1
        for g in groups:
            if pd.isna(g) or str(g) == 'nan':
                g_arr.append(c)
                c -= 1
            else:
                g_arr.append(g)
        import pandas as pd_local
        group_ids = pd_local.factorize(g_arr)[0]
        unique_groups = np.unique(group_ids)
        group_to_indices = {g: np.where(group_ids == g)[0] for g in unique_groups}
    else:
        unique_groups = None
        group_to_indices = None
        
    for _ in range(n):
        if groups is not None:
            sampled_groups = np.random.choice(unique_groups, size=len(unique_groups), replace=True)
            idx = np.concatenate([group_to_indices[g] for g in sampled_groups])
        else:
            idx = np.random.randint(0, n_obs, n_obs)
            
        yt = y_true_v[idx]
        if len(np.unique(yt)) < 2: continue
        
        prA, prB = p_A_raw[idx], p_B_raw[idx]
        pcA, pcB = p_A_cal[idx], p_B_cal[idx]
        p0_rA, p0_rB = p0_A_raw[idx], p0_B_raw[idx]
        p0_cA, p0_cB = p0_A_cal[idx], p0_B_cal[idx]
        
        lift_A_auc = roc_auc_score(yt, prA) - roc_auc_score(yt, p0_rA)
        lift_B_auc = roc_auc_score(yt, prB) - roc_auc_score(yt, p0_rB)
        diffs_auc.append(lift_B_auc - lift_A_auc)
        
        lift_A_pr = average_precision_score(yt, prA) - average_precision_score(yt, p0_rA)
        lift_B_pr = average_precision_score(yt, prB) - average_precision_score(yt, p0_rB)
        diffs_pr.append(lift_B_pr - lift_A_pr)
        
        lift_A_brier = brier_score_loss(yt, p0_cA) - brier_score_loss(yt, pcA)
        lift_B_brier = brier_score_loss(yt, p0_cB) - brier_score_loss(yt, pcB)
        diffs_brier.append(lift_B_brier - lift_A_brier)
        
    return {
        "contrast_roc_auc_mean": np.mean(diffs_auc) if diffs_auc else 0,
        "contrast_roc_auc_lower": np.percentile(diffs_auc, 2.5) if diffs_auc else 0,
        "contrast_roc_auc_upper": np.percentile(diffs_auc, 97.5) if diffs_auc else 0,
        "contrast_pr_auc_mean": np.mean(diffs_pr) if diffs_pr else 0,
        "contrast_pr_auc_lower": np.percentile(diffs_pr, 2.5) if diffs_pr else 0,
        "contrast_pr_auc_upper": np.percentile(diffs_pr, 97.5) if diffs_pr else 0,
        "contrast_brier_mean": np.mean(diffs_brier) if diffs_brier else 0,
        "contrast_brier_lower": np.percentile(diffs_brier, 2.5) if diffs_brier else 0,
        "contrast_brier_upper": np.percentile(diffs_brier, 97.5) if diffs_brier else 0,
        "bootstrap_type": "ORDER_CLUSTER_BOOTSTRAP" if groups is not None else "LINE_ITEM_BOOTSTRAP"
    }

def main():
    os.makedirs("outputs/tables", exist_ok=True)
    os.makedirs("outputs/figures", exist_ok=True)
    os.makedirs("paper/final_results_tables", exist_ok=True)
    
    usecols = list(set(EXTENDED_CATS + EXTENDED_NUMS + ["Ordered Quantity", "On Time (OTD)", "Fulfillment Method", "Order Entry Date", "Order Number", "OTD OTIF Exclusion Flag"]) - {"calendar_month"})
    splits, raw_df = load_and_split_t2c(usecols=usecols)
    raw_df_N = len(raw_df)
    del raw_df
    gc.collect()
    
    q2_base_map = {"A": {}, "B": {}}
    q4_base_map = {"A": {}, "B": {}}
    
    for k in ["A", "B"]:
        tr, va, te = splits[k]
        tr = ensure_columns(tr)
        va = ensure_columns(va)
        te = ensure_columns(te)
        
        for pid, grp in tr.groupby("Product ID"):
            q2_base_map[k][pid] = grp["Ordered Quantity"].median()
        for trc, grp in tr.groupby("Item Tracer Category"):
            q4_base_map[k][trc] = grp["Ordered Quantity"].median()
            
        tr = construct_quantity_features(tr, tr)
        va = construct_quantity_features(va, tr)
        te = construct_quantity_features(te, tr)
        splits[k] = (tr, va, te)
        
    assert np.array_equal(splits["A"][2].index, splits["B"][2].index), "Test sets must be identical"
    te_full = splits["A"][2]

    results, manifest, trained_models = [], [], {}
    np.random.seed(42)

    for feature_set_name, cats, nums in [("STRICT_ORDER_ENTRY", STRICT_CATS, []), ("EXTENDED_PLANNING_INFORMATION", EXTENDED_CATS, EXTENDED_NUMS)]:
        for protocol in ["A", "B"]:
            tr, va, te = splits[protocol]
            for rep in ["Q0", "Q2", "Q4"]:
                model_id = f"{feature_set_name}_{protocol}_{rep}"
                model_features = cats + nums + (["q2_prod_rel"] if rep=="Q2" else (["q4_tracer_rel"] if rep=="Q4" else []))
                X_tr, y_tr = tr[model_features], tr["late_delivery"]
                X_va, y_va = va[model_features], va["late_delivery"]
                X_te, y_te = te[model_features], te["late_delivery"]
                
                raw = CatBoostClassifier(iterations=150, depth=6, learning_rate=0.1, verbose=0, random_seed=42)
                raw.fit(X_tr, y_tr, eval_set=(X_va, y_va), early_stopping_rounds=20, cat_features=cats)
                
                sig = CalibratedClassifierCV(FrozenEstimator(raw), method="sigmoid")
                sig.fit(X_va, y_va)
                
                iso = IsotonicRegression(out_of_bounds="clip")
                iso.fit(raw.predict_proba(X_va)[:, 1], y_va)
                
                # Keep them memory efficient
                trained_models[model_id] = (raw, sig, iso, list(X_tr.columns), cats)
                
                for subset, X_eval, y_eval in [("test_full", X_te, y_te), ("test_2023", X_te[te["Entry_Year"]==2023], y_te[te["Entry_Year"]==2023])]:
                    p_r, p_s = raw.predict_proba(X_eval)[:, 1], sig.predict_proba(X_eval)[:, 1]
                    auc = roc_auc_score(y_eval, p_r)
                    prauc = average_precision_score(y_eval, p_r)
                    brier, ll, ece, slope, icept = get_calibration_metrics(y_eval, p_s)
                    results.append({
                        "feature_set": feature_set_name, "protocol": protocol, "representation": rep, 
                        "test_subset": subset, "ROC-AUC": auc, "PR-AUC": prauc, "Brier": brier, 
                        "log_loss": ll, "ECE": ece, "calibration_slope": slope, "calibration_intercept": icept
                    })
                
                manifest.append({
                    "feature_set": feature_set_name, "protocol": protocol, "representation": rep, 
                    "iterations": raw.tree_count_, "depth": 6, "learning_rate": 0.1, "random_seed": 42, 
                    "calibration_method": "sigmoid + isotonic", "feature_names": "|".join(list(X_tr.columns)), 
                    "training_N": len(tr), "validation_N": len(va)
                })
                gc.collect()

    print("Writing ablation")
    res_df = pd.DataFrame(results)
    res_df.to_csv("outputs/tables/final_predictive_ablation.csv", index=False)
    res_df.to_csv("paper/final_results_tables/table2_predictive_results.csv", index=False)
    
    # OTD Flag sensitivity
    flag_results = []
    
    flagged_mask = te_full["OTD OTIF Exclusion Flag"] == "Y"
    n_flagged = flagged_mask.sum()
    if n_flagged > 0:
        te_flagged = te_full[flagged_mask]
        late_rate_flagged = te_flagged["late_delivery"].mean()
        
        te_clean = te_full[~flagged_mask]
        
        for protocol in ["A", "B"]:
            for rep in ["Q0", "Q2", "Q4"]:
                raw, _, _, m_feats, _ = trained_models[f"STRICT_ORDER_ENTRY_{protocol}_{rep}"]
                
                pr = raw.predict_proba(te_clean[m_feats])[:, 1]
                auc = roc_auc_score(te_clean["late_delivery"], pr)
                
                flag_results.append({
                    "feature_set": "STRICT_ORDER_ENTRY",
                    "protocol": protocol,
                    "representation": rep,
                    "subset": "Excluding OTIF Exclusion Flag Y",
                    "ROC-AUC": auc
                })
                
        flag_summary = [{
            "number_flagged": n_flagged,
            "target_late_rate_in_flagged": late_rate_flagged
        }]
        pd.DataFrame(flag_summary).to_csv("outputs/tables/final_otd_exclusion_sensitivity_stats.csv", index=False)
        pd.DataFrame(flag_results).to_csv("outputs/tables/final_otd_exclusion_sensitivity.csv", index=False)
    pd.DataFrame(manifest).to_csv("outputs/tables/final_model_manifest.csv", index=False)

    print("Running bootstrap")
    boot_results = []
    contrast_results = []
    
    for feature_set_name in ["STRICT_ORDER_ENTRY", "EXTENDED_PLANNING_INFORMATION"]:
        p0_A_raw = trained_models[f"{feature_set_name}_A_Q0"][0].predict_proba(te_full[trained_models[f"{feature_set_name}_A_Q0"][3]])[:, 1]
        p0_B_raw = trained_models[f"{feature_set_name}_B_Q0"][0].predict_proba(te_full[trained_models[f"{feature_set_name}_B_Q0"][3]])[:, 1]
        p0_A_cal = trained_models[f"{feature_set_name}_A_Q0"][1].predict_proba(te_full[trained_models[f"{feature_set_name}_A_Q0"][3]])[:, 1]
        p0_B_cal = trained_models[f"{feature_set_name}_B_Q0"][1].predict_proba(te_full[trained_models[f"{feature_set_name}_B_Q0"][3]])[:, 1]
        
        for protocol in ["A", "B"]:
            p0_r = p0_A_raw if protocol == "A" else p0_B_raw
            p0_c = p0_A_cal if protocol == "A" else p0_B_cal
            
            for rep in ["Q2", "Q4"]:
                X_te_r = te_full[trained_models[f"{feature_set_name}_{protocol}_{rep}"][3]]
                pr_r = trained_models[f"{feature_set_name}_{protocol}_{rep}"][0].predict_proba(X_te_r)[:, 1]
                pr_c = trained_models[f"{feature_set_name}_{protocol}_{rep}"][1].predict_proba(X_te_r)[:, 1]
                
                b_diff = bootstrap_diff(te_full["late_delivery"], pr_r, p0_r, pr_c, p0_c, groups=None)
                b_diff_c = bootstrap_diff(te_full["late_delivery"], pr_r, p0_r, pr_c, p0_c, groups=te_full["Order Number"].values)
                b_diff.update(b_diff_c)
                
                b_diff.update({"feature_set": feature_set_name, "protocol": protocol, "comparison": f"{rep}_vs_Q0", "ranking_probability_source": "raw", "calibration_probability_source": "sigmoid"})
                boot_results.append(b_diff)
                
        for rep in ["Q2", "Q4"]:
            X_te_rA = te_full[trained_models[f"{feature_set_name}_A_{rep}"][3]]
            pr_rA = trained_models[f"{feature_set_name}_A_{rep}"][0].predict_proba(X_te_rA)[:, 1]
            pr_cA = trained_models[f"{feature_set_name}_A_{rep}"][1].predict_proba(X_te_rA)[:, 1]
            
            X_te_rB = te_full[trained_models[f"{feature_set_name}_B_{rep}"][3]]
            pr_rB = trained_models[f"{feature_set_name}_B_{rep}"][0].predict_proba(X_te_rB)[:, 1]
            pr_cB = trained_models[f"{feature_set_name}_B_{rep}"][1].predict_proba(X_te_rB)[:, 1]
            
            c_diff = bootstrap_temporal_contrast(te_full["late_delivery"], pr_rA, pr_rB, pr_cA, pr_cB, p0_A_raw, p0_B_raw, p0_A_cal, p0_B_cal, groups=None)
            c_diff_c = bootstrap_temporal_contrast(te_full["late_delivery"], pr_rA, pr_rB, pr_cA, pr_cB, p0_A_raw, p0_B_raw, p0_A_cal, p0_B_cal, groups=te_full["Order Number"].values)
            c_diff.update(c_diff_c)
            
            c_diff.update({"feature_set": feature_set_name, "representation": rep})
            contrast_results.append(c_diff)
            
    print("Writing bootstrap")
    pd.DataFrame(boot_results).to_csv("outputs/tables/final_bootstrap_differences.csv", index=False)
    pd.DataFrame(contrast_results).to_csv("outputs/tables/final_protocol_contrast.csv", index=False)

    tr_B = splits["B"][0]
    print(f"tr_B columns: {list(tr_B.columns)}")
    te_B = splits["B"][2]
    
    pid_counts = tr_B.groupby("Product ID")["late_delivery"].agg(['count', 'sum'])
    eligible_prods = pid_counts[(pid_counts['count'] >= 100) & (pid_counts['sum'] >= 10)].index.tolist()
    
    ice_rows = []
    stability = []
    emp_rows = []
    out_of_support_counts = []
    
    grid_pcts = [10, 25, 50, 75, 90]
    
    for pid in eligible_prods:
        p_trB = tr_B[tr_B["Product ID"] == pid]
        p_qtys_B = p_trB["Ordered Quantity"]
        
        p_trA = splits["A"][0][splits["A"][0]["Product ID"] == pid]
        p_qtys_A = p_trA["Ordered Quantity"]
        
        if p_qtys_A.empty or p_qtys_B.empty: continue
        
        min_B, max_B = p_qtys_B.min(), p_qtys_B.max()
        min_A, max_A = p_qtys_A.min(), p_qtys_A.max()
        support_min = max(min_A, min_B)
        support_max = min(max_A, max_B)
        
        if support_min >= support_max: continue
        
        q_grid_raw = np.percentile(p_qtys_B.dropna().values, grid_pcts)
        q_grid = np.clip(q_grid_raw, support_min, support_max)
        
        te_p = te_B[te_B["Product ID"] == pid].copy()
        if len(te_p) > 0:
            out_of_support = (te_p["Ordered Quantity"] < support_min) | (te_p["Ordered Quantity"] > support_max)
            out_of_support_counts.append({
                "product_id": pid, "test_n": len(te_p), "excluded_n": out_of_support.sum(),
                "excluded_pct": out_of_support.mean() * 100
            })
            te_p = te_p[~out_of_support]
        else:
            out_of_support_counts.append({"product_id": pid, "test_n": 0, "excluded_n": 0, "excluded_pct": 0.0})

        b_q2_A = q2_base_map["A"].get(pid, q2_base_map["A"].get("Missing", 1.0))
        b_q2_B = q2_base_map["B"].get(pid, q2_base_map["B"].get("Missing", 1.0))
        
        tracer_A = p_trA["Item Tracer Category"].iloc[0] if not p_trA.empty else "Missing"
        b_q4_A = q4_base_map["A"].get(tracer_A, q4_base_map["A"].get("Missing", 1.0))
        
        tracer_B = p_trB["Item Tracer Category"].iloc[0] if not p_trB.empty else "Missing"
        b_q4_B = q4_base_map["B"].get(tracer_B, q4_base_map["B"].get("Missing", 1.0))
        
        p_tr_sample = p_trB.sample(n=min(200, len(p_trB)), random_state=42)
        
        for rep, b_A, b_B in [("Q2", b_q2_A, b_q2_B), ("Q4", b_q4_A, b_q4_B)]:
            col_name = "q2_prod_rel" if rep == "Q2" else "q4_tracer_rel"
            
            # Vectorize the creation of X_A and X_B
            repeated_rows = p_tr_sample.iloc[np.repeat(np.arange(len(p_tr_sample)), len(q_grid))].copy()
            tiled_grid = np.tile(q_grid, len(p_tr_sample))
            tiled_pcts = np.tile(grid_pcts, len(p_tr_sample))
            
            X_A = repeated_rows.copy()
            X_A["Ordered Quantity"] = tiled_grid
            X_A[col_name] = np.log1p(tiled_grid / b_A)
            
            X_B = repeated_rows.copy()
            X_B["Ordered Quantity"] = tiled_grid
            X_B[col_name] = np.log1p(tiled_grid / b_B)
            
            curves_raw_A, curves_raw_B = [], []
            
            for protocol, X_cand in [("A", X_A), ("B", X_B)]:
                raw, sig, iso, m_feats, cats = trained_models[f"STRICT_ORDER_ENTRY_{protocol}_{rep}"]
                
                if len(X_cand) == 0:
                    print(f"X_cand is empty! len(p_tr_sample)={len(p_tr_sample)}, len(q_grid)={len(q_grid)}, pid={pid}")
                pr = raw.predict_proba(X_cand[m_feats])[:, 1]
                ps = sig.predict_proba(X_cand[m_feats])[:, 1]
                pi = iso.predict(pr)
                
                if protocol == "A":
                    curves_raw_A = pr.reshape(len(p_tr_sample), len(q_grid))
                else:
                    curves_raw_B = pr.reshape(len(p_tr_sample), len(q_grid))
                
                for i in range(len(X_cand)):
                    cid = repeated_rows.index[i]
                    ice_rows.append({
                        "context_id": cid, "product_id": pid, "representation": rep, "protocol": protocol,
                        "candidate_quantity": tiled_grid[i], "training_percentile": tiled_pcts[i],
                        "raw_probability": pr[i], "sigmoid_probability": ps[i], "isotonic_probability": pi[i],
                        "valid_support": True
                    })
                    
            raw_A = curves_raw_A
            raw_B = curves_raw_B
            
            med_A = np.median(raw_A, axis=0)
            med_B = np.median(raw_B, axis=0)
            
            rs_jr_B = np.max(raw_B, axis=1) - np.min(raw_B, axis=1)
            
            sp = pd.Series(med_A).corr(pd.Series(med_B), method='spearman')
            sp = sp if pd.notna(sp) else "uninformative_constant_curve"
                
            dir_A = np.sign(med_A[-1] - med_A[0])
            dir_B = np.sign(med_B[-1] - med_B[0])
            
            stability.append({
                "product_id": pid, "representation": rep,
                "median_R": np.median(rs_jr_B), "mean_R": np.mean(rs_jr_B),
                "p90_R": np.percentile(rs_jr_B, 90), "max_R": np.max(rs_jr_B),
                "support_min": support_min, "support_max": support_max,
                "raw_spearman": sp, "raw_max_abs_diff": np.max(np.abs(med_A - med_B)),
                "direction_match": 1 if dir_A == dir_B else 0,
                "direction_B": dir_B
            })
            
            if len(te_p) > 0:
                pcts_all = [0, 10, 25, 50, 75, 90, 100]
                bins = sorted(list(set(np.percentile(p_qtys_B, pcts_all).tolist())))
                if len(bins) == 1: bins = [bins[0] - 1, bins[0] + 1]
                te_p_band = te_p.copy()
                te_p_band["band"] = pd.cut(te_p_band["Ordered Quantity"], bins=bins, include_lowest=True, duplicates='drop')
                
                raw, sig, iso, m_feats, cats = trained_models[f"STRICT_ORDER_ENTRY_B_{rep}"]
                te_p_band["raw"] = raw.predict_proba(te_p_band[m_feats])[:, 1]
                
                for band in te_p_band["band"].dropna().unique():
                    bdf = te_p_band[te_p_band["band"] == band]
                    n = len(bdf)
                    if n > 0:
                        kl = bdf["late_delivery"].sum()
                        lb, ub = wilson_ci(kl, n)
                        emp_rows.append({
                            "product_id": pid, "representation": rep, "band": str(band), "test_n": n, "late_n": kl,
                            "emp_late_rate": kl/n, "emp_ci_lower": lb, "emp_ci_upper": ub,
                            "pred_mean_raw": bdf["raw"].mean(), "q_mid": bdf["Ordered Quantity"].mean()
                        })

    ice_df = pd.DataFrame(ice_rows)
    agg_df = ice_df.groupby(["product_id", "representation", "protocol", "candidate_quantity", "training_percentile"]).agg(
        raw_mean=('raw_probability', 'mean'),
        raw_median=('raw_probability', 'median'),
        raw_p10=('raw_probability', lambda x: np.percentile(x, 10)),
        raw_p25=('raw_probability', lambda x: np.percentile(x, 25)),
        raw_p75=('raw_probability', lambda x: np.percentile(x, 75)),
        raw_p90=('raw_probability', lambda x: np.percentile(x, 90))
    ).reset_index()
    ice_df.to_csv("outputs/tables/final_ice_curves_raw.csv", index=False)
    agg_df.to_csv("outputs/tables/final_ice_curves.csv", index=False)
    
    pd.DataFrame(out_of_support_counts).to_csv("outputs/tables/final_out_of_support_exclusions.csv", index=False)
    
    stab_df = pd.DataFrame(stability)
    stab_df.to_csv("outputs/tables/final_temporal_response_stability.csv", index=False)
    
    print(f"emp_rows length: {len(emp_rows)}")
    emp_df = pd.DataFrame(emp_rows)
    emp_df.to_csv("outputs/tables/final_empirical_holdout.csv", index=False)
    
    # Generate final_empirical_product_summary.csv
    emp_summary = []
    for pid in emp_df["product_id"].unique():
        for rep in ["Q2", "Q4"]:
            sub = emp_df[(emp_df["product_id"] == pid) & (emp_df["representation"] == rep) & (emp_df["test_n"] >= 5)]
            if len(sub) >= 3:
                model_sp = sub["pred_mean_raw"].corr(sub["emp_late_rate"], method="spearman")
                qty_sp = sub["q_mid"].corr(sub["emp_late_rate"], method="spearman")
                
                sub_sorted = sub.sort_values("q_mid")
                model_dir = np.sign(sub_sorted.iloc[-1]["pred_mean_raw"] - sub_sorted.iloc[0]["pred_mean_raw"])
                emp_dir = np.sign(sub_sorted.iloc[-1]["emp_late_rate"] - sub_sorted.iloc[0]["emp_late_rate"])
                
                emp_summary.append({
                    "product_id": pid,
                    "representation": rep,
                    "supported_bands": len(sub),
                    "supported_test_N": sub["test_n"].sum(),
                    "late_events": sub["late_n"].sum(),
                    "spearman_model_vs_empirical": model_sp,
                    "spearman_quantity_vs_empirical": qty_sp,
                    "endpoint_direction_agreement": 1 if model_dir == emp_dir else 0,
                    "note": "Interpret with caution; wide Wilson CIs at band level."
                })
    pd.DataFrame(emp_summary).to_csv("outputs/tables/final_empirical_product_summary.csv", index=False)
    
    sens_rows = []
    for r_thresh in [0.005, 0.010, 0.015, 0.020]:
        for sp_thresh in [0.3, 0.5, 0.7]:
            for mad_thresh in [0.02, 0.05]:
                for (n_req, b_req) in [(5, 3), (10, 3)]:
                    passed_pairs = 0
                    unique_prods = set()
                    if not stab_df.empty and not emp_df.empty:
                        for rep in ["Q2", "Q4"]:
                            sdf = stab_df[stab_df["representation"]==rep]
                            for pid in sdf["product_id"]:
                                sr = sdf[sdf["product_id"]==pid].iloc[0]
                                if sr["median_R"] >= r_thresh and sr["raw_spearman"] != "uninformative_constant_curve" and float(sr["raw_spearman"]) >= sp_thresh and sr["raw_max_abs_diff"] <= mad_thresh:
                                    edf = emp_df[(emp_df["product_id"]==pid) & (emp_df["representation"]==rep)]
                                    b_count = len(edf[edf["test_n"]>=n_req])
                                    if b_count >= b_req:
                                        passed_pairs += 1
                                        unique_prods.add(pid)
                    sens_rows.append({"min_median_R": r_thresh, "min_spearman": sp_thresh, "max_mad": mad_thresh, "n_req": n_req, "bands_req": b_req, "passed_product_representation_pairs": passed_pairs, "unique_products": len(unique_prods)})
    
    sens_df = pd.DataFrame(sens_rows)
    sens_df.to_csv("paper/final_results_tables/table4_sensitivity_summary.csv", index=False)
    
    t1_data = [
        {"metric": "Raw GHSC rows", "count": 43396},
        {"metric": "Direct Drop rows", "count": 39306},
        {"metric": "Direct Drop valid OTD Y/N", "count": 39289},
        {"metric": "Protocol A train", "count": len(splits["A"][0])},
        {"metric": "Protocol B train", "count": len(splits["B"][0])},
        {"metric": "Validation 2022", "count": len(splits["B"][1])},
        {"metric": "Test 2023", "count": len(splits["B"][2][splits["B"][2]["Entry_Year"] == 2023])},
        {"metric": "Available 2024", "count": len(splits["B"][2][splits["B"][2]["Entry_Year"] == 2024])},
        {"metric": "Combined test", "count": len(splits["B"][2])}
    ]
    pd.DataFrame(t1_data).to_csv("paper/final_results_tables/table1_dataset_protocol.csv", index=False)
    
    if not stab_df.empty:
        t3_data = stab_df[["product_id", "representation", "median_R", "raw_spearman", "raw_max_abs_diff"]].copy()
        t3_data.to_csv("paper/final_results_tables/table3_actionability_screen.csv", index=False)
    else:
        pd.DataFrame(columns=["product_id", "representation", "median_R"]).to_csv("paper/final_results_tables/table3_actionability_screen.csv", index=False)

    plt.figure()
    for prot, ls, m in [("A", "--", "s"), ("B", "-", "o")]:
        sub = res_df[(res_df["feature_set"]=="STRICT_ORDER_ENTRY") & (res_df["test_subset"]=="test_full") & (res_df["protocol"]==prot)]
        plt.plot(sub["representation"], sub["ROC-AUC"], marker=m, linestyle=ls, label=f"Strict Protocol {prot}")
    plt.title("Predictive ROC-AUC Sensitivity")
    plt.legend()
    plt.savefig("outputs/figures/final_predictive_ablation.png", dpi=300)
    plt.savefig("outputs/figures/final_predictive_ablation.pdf")
    plt.close()
    
    if not agg_df.empty:
        pid = agg_df["product_id"].iloc[0]
        sub = agg_df[(agg_df["product_id"] == pid) & (agg_df["representation"] == "Q4")]
        if not sub.empty:
            plt.figure()
            for prot in ["A", "B"]:
                psub = sub[sub["protocol"]==prot]
                plt.plot(psub["candidate_quantity"], psub["raw_median"], label=f"{prot} median")
                plt.fill_between(psub["candidate_quantity"], psub["raw_p10"], psub["raw_p90"], alpha=0.3)
            plt.legend()
            plt.title(f"ICE Response Curve (Raw Q4 envelope) - {pid}")
            plt.savefig("outputs/figures/final_ice_response_curves.png", dpi=300)
            plt.savefig("outputs/figures/final_ice_response_curves.pdf")
            plt.close()

    plt.figure()
    plt.title("Temporal Response Stability")
    if not stab_df.empty:
        sdf = stab_df[stab_df["raw_spearman"] != "uninformative_constant_curve"]
        if not sdf.empty:
            plt.hist(sdf["raw_spearman"].astype(float), bins=20)
    plt.savefig("outputs/figures/final_temporal_response_stability.png", dpi=300)
    plt.savefig("outputs/figures/final_temporal_response_stability.pdf")
    plt.close()

    plt.figure()
    plt.title("Empirical Alignment vs Predictions (Supported Bands)")
    if not emp_df.empty:
        supported = emp_df[emp_df["test_n"] >= 5].copy()
        if not supported.empty:
            plt.errorbar(supported["pred_mean_raw"], supported["emp_late_rate"],
                         yerr=[supported["emp_late_rate"] - supported["emp_ci_lower"], supported["emp_ci_upper"] - supported["emp_late_rate"]],
                         fmt='o', alpha=0.6)
            plt.plot([0, 0.5], [0, 0.5], 'r--')
            plt.xlabel("Predicted mean raw prob")
            plt.ylabel("Empirical late rate (Wilson 95% CI)")
            plt.xlim(0, max(0.1, supported["pred_mean_raw"].max() * 1.1))
            plt.ylim(0, max(0.1, supported["emp_ci_upper"].max() * 1.1))
    plt.savefig("outputs/figures/final_empirical_alignment.png", dpi=300)
    plt.savefig("outputs/figures/final_empirical_alignment.pdf")
    plt.close()
    
    with open("END_OF_SCRIPT.txt", "w") as f:
        f.write("I REACHED THE END!")

if __name__ == "__main__":
    main()
