# T1 Data Audit Report

## 1. Feature Availability
Features audited and classified in `outputs/tables/feature_availability_audit.csv`.

## 2. Data Quality Audit
- Duplicates: 0
- Zero/Negative Quantity: 0
- Missing values:
  - Shipment Mode: 48
  - PQ First Sent to Client Date: 1021
  - PO Sent to Vendor Date: 328
  - Dosage: 1557
  - Line Item Insurance (USD): 118

## 3. Cohort Rules
Used Fulfill Via == 'Direct Drop'. 'From RDC' is internal and excluded.
`late_delivery = 1 if (Delivered to Client Date - Scheduled Delivery Date).days > 0 else 0`.
This measures delivery-to-client lateness which includes logistics effects, not only supplier manufacturing performance.
