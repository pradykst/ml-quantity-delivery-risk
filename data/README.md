# Dataset Information

The study relies on the **USAID Global Health Supply Chain (GHSC) Program Health Commodity Delivery Dataset**. 

## Details
- **Exact File Name:** `USAID_GHSC_PSM_Health_Commodity_Delivery_Dataset.csv`
- **Expected Rows:** 43,396
- **Expected Columns:** 104
- **File Size:** ~46.3 MB
- **Expected SHA-256 Hash:** `df9d65337ef30ebf62f32380068d53012975737c366f188cbccb2ddd79b0a83a`
- **Source:** Data.gov / USAID

## Attribution and Role
The dataset is published by the U.S. Agency for International Development (USAID) and cataloged through Data.gov. The raw dataset is externally sourced, and this repository does not claim ownership of it. The raw dataset is not redistributed in this repository. Users should consult the source record and applicable source terms for reuse or redistribution. 

This externally sourced dataset serves as the core empirical basis for predicting delivery risk (delay). It provides historical data on health commodity shipments, including mode of transportation, cost, item categories, order quantities, and delivery dates.

**Important:** The expected SHA-256 hash identifies the exact snapshot used by this study. A newer upstream version with another hash is NOT automatically equivalent.

## How to Acquire
1. Download the dataset from the official USAID / Data.gov portal.
2. Save the file exactly as `USAID_GHSC_PSM_Health_Commodity_Delivery_Dataset.csv` inside this `data/` directory.
3. Run `python ../scripts/download_data.py` to verify the hash matches the study's frozen checksum.
