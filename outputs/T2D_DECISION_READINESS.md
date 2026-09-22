# T2D: Decision Readiness Results

## 1. Calibration (Test Set)
Quantity features (Q2/Q4) failed to meaningfully improve calibration over the baseline (Q0). Expected Calibration Error (ECE), log loss, and Brier scores remain effectively unchanged when quantity features are included. The slope and intercept for the isotonic-calibrated models are near 1 and 0, confirming successful internal calibration, but out-of-sample calibration shows no structural lift from quantity.

## 2. Risk Curve Stability
Of the tested eligible products, stability between Protocol A and B is extremely weak. Many products show negative Spearman correlation across protocols or conflicting directional effects.

## 3. Candidate Products
The candidate filter identified a few products with some stability, but the risk spread (max_prob - min_prob) driven by quantity is minimal and subject to noise. 

## 4. Final Classification
**Classification: C (NOT READY)**
Probability curves are unstable across temporal protocols and badly calibrated out-of-sample in a structural sense (quantity adds no reliable discriminative power). The models are not decision-ready for use in a downstream optimization where quantity changes are expected to accurately forecast risk changes.
