# Machine-learning-informed supplier selection/order allocation with quantity-dependent delivery risk

This repository contains the official reproducibility artifact for the research paper **"Machine-learning-informed supplier selection/order allocation with quantity-dependent delivery risk"**, targeted for IC-AMMA 2026.

## Research Context and Boundaries

This study investigates the predictability of public health supply chain delivery risk, focusing specifically on whether **relative order quantity** provides incremental future delivery-risk information.

**Important Interpretational Boundaries:**
- **Observational Only**: The final study evaluates observational quantity-response stability. **It does NOT claim a causal effect of quantity.** 
- **No Optimization**: The study evaluates whether the signal is sufficiently stable to warrant *future* causal/prescriptive study. **It does NOT implement a prescriptive MILP optimizer.**
- **No Direct Intervention**: The study does not claim that changing the order quantity for a specific supplier will directly change the delivery risk outcome in the real world.

## Repository Structure

- `src/`: The core scientific pipeline for data processing, feature engineering, and model training.
  - `run_final_audit.py`: The main entry point to run the pipeline.
  - `t2c_data.py`: Data loading, filtering, and train/test splitting logic.
  - `t2c_features.py`: Feature engineering, including strict/extended categorical and numeric features, and quantity transformations.
  - `freeze_final_bundle.py`: Final packaging script.
- `data/`: Directory for the dataset. See `data/README.md` for download and verification instructions.
- `tests/`: Automated unit tests for the pipeline.
- `paper/`: Result tables directly mapping to the manuscript.
- `outputs/`: Generated figures and intermediate CSV artifacts.

## Reproduction Instructions

Verified reproduction environment: Python 3.13.1.
Other Python versions may work but were not validated for the archived reproduction snapshot.
The exact tested dependency versions are listed in `requirements.txt`:
- pandas==2.2.3
- numpy==2.2.6
- scikit-learn==1.9.0
- catboost==1.2.10
- matplotlib==3.10.8
- pytest==9.0.2

### 1. Clone the Repository
```bash
git clone https://github.com/pradykst/ml-quantity-delivery-risk.git
cd ml-quantity-delivery-risk
```

### 2. Create the Environment
Add explicit environment creation commands to ensure a clean state.

**Windows:**
```cmd
py -3.13 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

**POSIX:**
```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Data Acquisition
Due to licensing and size, the dataset is not tracked in this Git repository.
You must download the USAID GHSC-PSM Health Commodity Delivery Dataset and place it in the `data/` folder.
Run the verification script to ensure the checksum matches the exact version used in the study:
```bash
python scripts/download_data.py
```

### 4. Run Tests
```bash
python -m pytest
```

### 5. Run the Pipeline
We provide simple wrapper scripts for reproducibility (`reproduce.bat` / `reproduce.sh`). Alternatively, run directly:
```bash
python -m src.run_final_audit
```

### 6. Mapping to Paper
The pipeline generates CSV files in `paper/final_results_tables/` that map directly to the tables presented in the manuscript:
- `table1_dataset_protocol.csv`: Dataset statistics and protocol metrics.
- `table2_predictive_results.csv`: Out-of-sample predictive performance.
- `table3_actionability_screen.csv`: Stability and actionability metrics for candidate products.
- `table4_sensitivity_summary.csv`: Ablation and sensitivity analysis results.

Figures are generated in `outputs/figures/`.

## Numerical Reproducibility
- Counts, cohort membership, and classifications are expected to reproduce exactly.
- Model-derived floating-point values may differ in insignificant final binary digits across compatible numerical-library/platform builds.
- Reproduction is considered numerically equivalent using `rtol=1e-12` and `atol=1e-12`.
- All metrics at the precision reported in the manuscript must remain unchanged.

## License
The original code in this repository is licensed under the MIT License. Please see the `LICENSE` file. For third-party data and package attributions, see `THIRD_PARTY_NOTICES.md`.