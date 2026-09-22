# Preliminary predictive smoke test

This is **not a paper result**. It is only a feasibility check before final feature engineering, rolling validation, model selection and calibration.

Temporal split: first 70% of Direct Drop observations for training, last 30% for testing.
Test set: 1,476 observations, late-delivery rate 2.57%.

| Logistic model | ROC-AUC | PR-AUC | Brier | Log loss |
|---|---:|---:|---:|---:|
| Without quantity | 0.6447 | 0.1761 | 0.02665 | 0.13380 |
| With log quantity + item-relative quantity | 0.6579 | 0.1521 | 0.02624 | 0.12962 |

Interpretation: quantity features slightly improved ROC-AUC, Brier score and log loss, but reduced PR-AUC. This mixed result is not evidence of a final benefit. It confirms that the quantity ablation must be tested rigorously with stronger models, temporal cross-validation and calibration rather than assumed to help.
