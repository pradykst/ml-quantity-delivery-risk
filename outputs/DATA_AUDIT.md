# Initial SCMS data audit

This is a feasibility audit, not a final paper result.

## Cohort
The raw dataset contains **10,324** records.
`Fulfill Via` splits them exactly into:
- Direct Drop: **4,920**
- From RDC: **5,404**

All `From RDC` rows use `Vendor = SCMS from RDC`, so those observations do not provide
an external supplier identity suitable for supplier selection/order allocation. The primary
research cohort is therefore Direct Drop.

## Direct-drop cohort
- Suppliers: **72**
- Items: **174**
- Countries: **40**
- Late deliveries: **259**
- Late-delivery rate: **5.26%**
- Observation period: **2006-05-02 to 2015-09-14**

## Multi-sourcing support
- Items supplied by >=2 suppliers: **84**
- Items supplied by >=3 suppliers: **55**
- Items where >=2 suppliers each have >=10 historical orders: **25**
- Items where >=2 suppliers each have >=20 historical orders: **15**

This is enough to construct several empirical multi-supplier allocation case studies.

## Quantity and lateness
Median order quantity is **1,235** units and the 95th percentile is
**56,519**, confirming that raw quantity is highly heterogeneous across
products. Quantity must therefore be represented relative to product/supplier context rather than
used naively as a globally comparable value.

The descriptive figure `fig01_relative_quantity_late_rate.png` ranks quantity within each item
before pooling. It is exploratory only and does not establish causality.

## Immediate risks
1. Direct-drop late deliveries are relatively rare, so PR-AUC and calibration are important.
2. Delivery-to-client lateness includes logistics effects, not only supplier production performance.
3. The dataset is observational, so counterfactual quantity changes must stay inside empirical support.
4. Temporal late rates drift substantially; final validation must therefore be temporal.
