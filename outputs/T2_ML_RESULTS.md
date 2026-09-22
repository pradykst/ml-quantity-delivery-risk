# T2 ML Results

## 1. Quantitative Results
| model   | has_qty   | calibration   |   roc_auc |    pr_auc |     brier |   log_loss | cm_threshold_0.05      |
|:--------|:----------|:--------------|----------:|----------:|----------:|-----------:|:-----------------------|
| LR      | False     | isotonic      |  0.525392 | 0.0427944 | 0.0286968 |   0.192368 | [[852, 111], [15, 6]]  |
| LR      | True      | isotonic      |  0.516837 | 0.0410186 | 0.0258463 |   0.27418  | [[869, 94], [17, 4]]   |
| RF      | False     | isotonic      |  0.642462 | 0.0551709 | 0.025236  |   0.235522 | [[622, 341], [11, 10]] |
| RF      | True      | isotonic      |  0.551674 | 0.0712262 | 0.0273052 |   0.642204 | [[850, 113], [15, 6]]  |
| XGB     | False     | isotonic      |  0.624981 | 0.0463995 | 0.0262543 |   0.21005  | [[885, 78], [18, 3]]   |
| XGB     | True      | isotonic      |  0.500396 | 0.0324178 | 0.026573  |   0.171056 | [[768, 195], [16, 5]]  |

## 2. Interpretation
Does quantity add useful out-of-sample predictive information about delivery lateness, conditional on the available context?
Comparing models with and without quantity features, we observe the effect of quantity variables on ROC-AUC, PR-AUC, Brier score, and log-loss on the strictly temporally held-out test set.
