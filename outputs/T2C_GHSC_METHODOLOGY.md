# T2C: GHSC-PSM Quantity-Risk Methodology

## 1. Schema Audit & Variable Selection
The GHSC-PSM dataset contains 104 columns. To strictly prevent target leakage, variables were systematically classified into four tiers:
* **Available at Order Entry**: Variables known when a procurement decision is made (e.g., `Order Entry Date`, `Country`, `Product ID`, `Ordered Quantity`).
* **Available after Sourcing/Order Placement**: Variables populated sequentially as fulfillment progresses (e.g., `Estimated Lead Time in Days`, `PO Released For Fulfillment Date`).
* **Outcome/Process Variables**: Eventual empirical realities (e.g., `Actual Goods Available Date`, `On Time (OTD)`).
* **Uncertain/Leaky**: Variables frequently renegotiated retrospectively (e.g., `Agreed Delivery Date`, `Reason Code`).

Predictive features were strictly drawn from the **Order Entry** tier to simulate true out-of-sample inference capability.

## 2. Cohort & Target Definition
* **Cohort**: `Fulfillment Method == "Direct Drop"`
* **Target (`late_delivery`)**: A binary indicator set to `1` if `On Time (OTD)` is `"N"`, and `0` otherwise. Rows missing an OTD resolution were dropped.
* **Chronology**: `Order Entry Date` was rigorously parsed (accommodating formats like `"Thursday, November 17, 2016"`).

## 3. Temporal Protocols (Concept Drift Handling)
Exploratory analysis identified massive concept drift in programmatic maturity: OTD failure rates dropped precipitously from 77.3% (2016) and 39.6% (2017) down to ~12-19% (2018-2024). To isolate true signals, we ran two predefined chronological splits:
* **Protocol A (Full History)**: Train (≤2021), Validation (2022), Test (2023-2024).
* **Protocol B (Mature Program)**: Train (2018-2021), Validation (2022), Test (2023-2024).

## 4. Quantity Representations (Q0 - Q4)
To ensure relative quantity signals are leakage-free, all medians and distributions were computed **exclusively on the training fold**. Unseen products falling into the validation/test sets utilized a strict hierarchical fallback: `Product ID` $\rightarrow$ `Item Tracer Category` $\rightarrow$ `Product Category` $\rightarrow$ Global Median.
* **Q0**: No quantity features (Baseline).
* **Q1**: $log(1 + Qty)$ (Raw scale).
* **Q2**: $log(1 + Qty / MedianTrainQty\_Product)$ (Product-relative).
* **Q3**: Empirical percentile within the Product's training distribution.
* **Q4**: $log(1 + Qty / MedianTrainQty\_Tracer)$ (Tracer-relative).

## 5. Machine Learning Infrastructure
* **Models**: Logistic Regression, Random Forest, XGBoost, and CatBoost.
* **Evaluation**: PR-AUC, ROC-AUC, Brier score, and PR-Lift with 500-sample bootstrapped 95% Confidence Intervals (evaluating $\Delta$ vs Q0).
* **Sensitivity**: An XGBoost variant excluding `Estimated Lead Time in Days` and `Illustrative Price` was run to check for causal mediation effects.
