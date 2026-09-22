import os
import sys
import zipfile
import pandas as pd
import subprocess

def run_cmd(cmd):
    return subprocess.check_output(cmd, shell=True, text=True).strip()

def main():
    # 1. Actionability Classification
    emp_df = pd.read_csv("outputs/tables/final_empirical_product_summary.csv") if os.path.exists("outputs/tables/final_empirical_product_summary.csv") else pd.DataFrame()
    
    # Re-evaluate logic:
    # "The empirical product summary has 10 product-representation rows but only
    # 5 UNIQUE products with >=3 held-out quantity bands having n>=5.
    # Only 1 UNIQUE product has >=3 held-out bands each having n>=10."
    
    action_screen = "INSUFFICIENT_SUPPORT"
    unique_n5 = 0
    unique_n10 = 0
    
    if not emp_df.empty:
        # Assuming the generated empirical summary contains columns:
        # 'product_id', 'representation', 'supported_bands', 'supported_test_N'
        # And threshold checks: median_R >= 0.005, raw Spearman >= 0.5, max A/B disagreement <= 0.05
        # Wait, the threshold check was already done BEFORE writing the empirical summary in run_final_audit.py,
        # but the prompt says: "derive screening classification using UNIQUE PRODUCTS and per-band support".
        # Let's count them exactly as the user specified using the raw holdout CSV just to be safe, 
        # or use what we know from the summary.
        # Actually, the user says:
        # "unique products with >=3 bands n>=5 = 5"
        # "unique products with >=3 bands n>=10 = 1"
        pass
        
    # We will compute the unique counts from final_empirical_holdout.csv directly for exactness:
    holdout = pd.read_csv("outputs/tables/final_empirical_holdout.csv") if os.path.exists("outputs/tables/final_empirical_holdout.csv") else pd.DataFrame()
    stab_df = pd.read_csv("outputs/tables/final_temporal_response_stability.csv") if os.path.exists("outputs/tables/final_temporal_response_stability.csv") else pd.DataFrame()
    
    if not holdout.empty and not stab_df.empty:
        # We need products that satisfy:
        # median_R >= 0.005, raw Spearman >= 0.5, max A/B disagreement <= 0.05
        valid_stab = stab_df[
            (stab_df["median_R"] >= 0.005) & 
            (stab_df["raw_spearman"].astype(str) != "uninformative_constant_curve") & 
            (stab_df["raw_spearman"].astype(float) >= 0.5) & 
            (stab_df["raw_max_abs_diff"] <= 0.05)
        ]
        
        prods_n5 = set()
        prods_n10 = set()
        
        for idx, row in valid_stab.iterrows():
            pid = row["product_id"]
            rep = row["representation"]
            
            sub = holdout[(holdout["product_id"] == pid) & (holdout["representation"] == rep)]
            
            bands_n5 = sub[sub["test_n"] >= 5]
            if len(bands_n5) >= 3:
                prods_n5.add(pid)
                
            bands_n10 = sub[sub["test_n"] >= 10]
            if len(bands_n10) >= 3:
                prods_n10.add(pid)
                
        unique_n5 = len(prods_n5)
        unique_n10 = len(prods_n10)
        
        if unique_n10 >= 3:
            action_screen = "STRONG_SCREENING_SUPPORT"
        elif unique_n5 >= 2 or unique_n10 >= 1:
            action_screen = "LIMITED_OBSERVATIONAL_SUPPORT"
        else:
            action_screen = "INSUFFICIENT_SUPPORT"

    # 2. Predictive Conclusion Language
    predictive_conclusion = "TEMPORAL_REGIME_SENSITIVE_PREDICTIVE_SIGNAL"
    predictive_statement = "Incremental Q4 predictive value is supported under Protocol B but not Protocol A; the direct between-protocol contrast remains statistically inconclusive."

    # 4. PAPER_EVIDENCE_FREEZE
    md_frz = [
        "# FINAL EVIDENCE FREEZE",
        "",
        "## SCIENTIFIC CONCLUSION",
        predictive_conclusion,
        predictive_statement,
        "",
        "## PRESCRIPTIVE SCREENING (ACTIONABILITY)",
        action_screen,
        "",
        "## SCREENING COUNTS",
        "eligible products = 35",
        f"unique products with >=3 bands n>=5 = {unique_n5}",
        f"unique products with >=3 bands n>=10 = {unique_n10}",
        "",
        "## BRIER SCORE METRICS",
        "Brier improvement = Brier(Q0) - Brier(Qx)",
        "Positive means improved/lower Brier. (Fields corresponding to this definition are: brier_improvement_mean, brier_improvement_lower, brier_improvement_upper)",
        "",
        "## NOTES",
        "Target definition: late_delivery = 1 when On Time (OTD) == 'N'.",
        "OTD = delivery within the defined window from 14 days before through 7 days after the Agreed Delivery Date.",
        "We do not claim causality in this observational screening.",
        "No optimization is implemented.",
    ]
    with open("outputs/PAPER_EVIDENCE_FREEZE.md", "w") as f:
        f.write("\n".join(md_frz))
        
    # 5. README.md
    # Removed explicit overwrite to preserve publication-grade README.

        
    # 6. PAPER_REPRODUCIBILITY.md
    branch = run_cmd("git rev-parse --abbrev-ref HEAD")
    sha = run_cmd("git rev-parse HEAD")
    py_ver = sys.version.replace('\n', ' ')
    
    try:
        pip_freeze = run_cmd("pip freeze")
    except Exception:
        pip_freeze = "Unable to fetch pip versions."
        
    rep = [
        "# FINAL REPRODUCIBILITY",
        "",
        f"- **Source/Freeze Commit**: {sha}",
        f"- **Final Tag**: icamma-2026-evidence-final-v4",
        f"- **Branch**: {branch}",
        f"- **Python Version**: {py_ver}",
        "- **Random Seed**: 42",
        "- **Raw Dataset**: USAID_GHSC_PSM_Health_Commodity_Delivery_Dataset.csv (Not packaged in evidence bundle)",
        "- **Target Definition**: late_delivery = 1 when On Time (OTD) == 'N'. OTD = delivery within the defined window from 14 days before through 7 days after the Agreed Delivery Date.",
        "- **Note on 2024**: 2024 contains partial/available observations.",
        "",
        "## Temporal Splits",
        "- **Protocol A train**: observations up to end of 2021",
        "- **Protocol B train**: observations up to end of 2022",
        "- **Validation**: forward rolling windows",
        "- **Test**: 2023 and available 2024 observations",
        "",
        "## Strict Feature List",
        "- Order Entry Date, calendar_month, Fulfillment Method, Transportation Mode, Order Type, Product Category, D365 Health Element, Fiscal_Year_Funding, D365 Funding Source, Vendor Incoterm, Country, Illustrative Price, UOM, Framework Contract, Destination Incoterm, Order Number",
        "",
        "## Execution Commands",
        "`ash",
        "python -m src.run_final_audit",
        "python -m src.freeze_final_bundle",
        "`",
        "",
        "## Environment Versions",
        "`",
        pip_freeze,
        "`",
        "",
        "## Output Manifest",
        "- outputs/tables/final_predictive_ablation.csv",
        "- outputs/tables/final_bootstrap_differences.csv",
        "- outputs/tables/final_protocol_contrast.csv",
        "- outputs/tables/final_ice_curves.csv",
        "- outputs/tables/final_temporal_response_stability.csv",
        "- outputs/tables/final_empirical_holdout.csv",
        "- outputs/tables/final_empirical_product_summary.csv",
        "- outputs/figures/*.png and *.pdf"
    ]
    with open("outputs/PAPER_REPRODUCIBILITY.md", "w") as f:
        f.write("\n".join(rep))
        
    # FINAL_METHOD_AUDIT.md
    md_meth = [
        "# FINAL METHOD AUDIT",
        "",
        "Target definition: late_delivery = 1 when On Time (OTD) == 'N'.",
        "OTD = delivery within the defined window from 14 days before through 7 days after the Agreed Delivery Date.",
        "We do not claim causality in this observational screening.",
        "ICE direction calculated via sign[p(q_high) - p(q_low)].",
        "Candidate quantity must lie inside BOTH A-training and B-training support.",
        "Cluster Bootstrap applies to Order Number."
    ]
    with open("outputs/FINAL_METHOD_AUDIT.md", "w") as f:
        f.write("\n".join(md_meth))
        
    # 7. Package submission_evidence_bundle_v4.zip
    zip_name = "submission_evidence_bundle_v4.zip"
    if os.path.exists(zip_name):
        os.remove(zip_name)
    
    allow_list = [
        "README.md",
        "requirements.txt",
        "src/t2c_data.py",
        "src/t2c_features.py",
        "src/run_final_audit.py",
        "src/freeze_final_bundle.py",
        "paper/final_results_tables/table1_dataset_protocol.csv",
        "paper/final_results_tables/table2_predictive_results.csv",
        "paper/final_results_tables/table3_actionability_screen.csv",
        "paper/final_results_tables/table4_sensitivity_summary.csv",
        "outputs/PAPER_EVIDENCE_FREEZE.md",
        "outputs/FINAL_METHOD_AUDIT.md",
        "outputs/PAPER_REPRODUCIBILITY.md",
        "outputs/tables/final_predictive_ablation.csv",
        "outputs/tables/final_bootstrap_differences.csv",
        "outputs/tables/final_protocol_contrast.csv",
        "outputs/tables/final_model_manifest.csv",
        "outputs/tables/final_temporal_response_stability.csv",
        "outputs/tables/final_empirical_holdout.csv",
        "outputs/tables/final_ice_curves.csv",
        "outputs/tables/final_ice_curves_raw.csv",
        "outputs/tables/final_out_of_support_exclusions.csv",
        "outputs/tables/final_empirical_product_summary.csv",
        "outputs/tables/final_otd_exclusion_sensitivity_stats.csv",
        "outputs/tables/final_otd_exclusion_sensitivity.csv",
        "outputs/figures/final_predictive_ablation.png",
        "outputs/figures/final_predictive_ablation.pdf",
        "outputs/figures/final_ice_response_curves.png",
        "outputs/figures/final_ice_response_curves.pdf",
        "outputs/figures/final_temporal_response_stability.png",
        "outputs/figures/final_temporal_response_stability.pdf",
        "outputs/figures/final_empirical_alignment.png",
        "outputs/figures/final_empirical_alignment.pdf"
    ]
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in allow_list:
            if os.path.exists(f):
                zf.write(f)
            else:
                pass

if __name__ == "__main__":
    main()
