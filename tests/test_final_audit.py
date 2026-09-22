import os
import pandas as pd
import numpy as np

def test_no_placeholders():
    for f in os.listdir("outputs/figures"):
        if f.endswith(".png"):
            size = os.path.getsize(os.path.join("outputs/figures", f))
            assert size > 5000, f"Figure {f} seems like an empty placeholder"

def test_manifest_configuration():
    man = pd.read_csv("outputs/tables/final_model_manifest.csv")
    assert (man["iterations"] <= 150).all()
    assert (man["depth"] == 6).all()
    
def test_quantity_perturbation_support():
    stab = pd.read_csv("outputs/tables/final_temporal_response_stability.csv")
    ice = pd.read_csv("outputs/tables/final_ice_curves.csv")
    if not ice.empty:
        for pid in stab["product_id"]:
            s_min = stab[stab["product_id"]==pid]["support_min"].iloc[0]
            s_max = stab[stab["product_id"]==pid]["support_max"].iloc[0]
            ic_pid = ice[ice["product_id"]==pid]
            assert (ic_pid["candidate_quantity"] >= s_min).all()
            assert (ic_pid["candidate_quantity"] <= s_max).all()

def test_temporal_grids_match():
    ice = pd.read_csv("outputs/tables/final_ice_curves.csv")
    if not ice.empty:
        for pid in ice["product_id"].unique():
            for rep in ice[ice["product_id"]==pid]["representation"].unique():
                df_pid = ice[(ice["product_id"]==pid) & (ice["representation"]==rep)]
                grid_A = df_pid[df_pid["protocol"]=="A"]["candidate_quantity"].sort_values().values
                grid_B = df_pid[df_pid["protocol"]=="B"]["candidate_quantity"].sort_values().values
                if len(grid_A) > 0 and len(grid_B) > 0:
                    assert len(grid_A) == len(grid_B)
                    assert np.allclose(grid_A, grid_B)

def test_direction_calculation():
    stab = pd.read_csv("outputs/tables/final_temporal_response_stability.csv")
    if not stab.empty:
        assert set(stab["direction_match"].unique()).issubset({0, 1})

def test_strict_feature_set():
    man = pd.read_csv("outputs/tables/final_model_manifest.csv")
    strict = man[man["feature_set"] == "STRICT_ORDER_ENTRY"]
    for feats in strict["feature_names"]:
        flist = feats.split("|")
        assert "Estimated Lead Time in Days" not in flist
        assert "Illustrative Price" not in flist
        assert "Transportation Mode" not in flist

def test_brier_sigmoid():
    b_diff = pd.read_csv("outputs/tables/final_bootstrap_differences.csv")
    if not b_diff.empty:
        assert (b_diff["calibration_probability_source"] == "sigmoid").all()

def test_q2_q4_presence():
    stab = pd.read_csv("outputs/tables/final_temporal_response_stability.csv")
    if not stab.empty:
        assert "Q2" in stab["representation"].values
        assert "Q4" in stab["representation"].values

def test_empirical_exclusions():
    exc = pd.read_csv("outputs/tables/final_out_of_support_exclusions.csv")
    if not exc.empty:
        assert "excluded_n" in exc.columns
        assert "excluded_pct" in exc.columns

