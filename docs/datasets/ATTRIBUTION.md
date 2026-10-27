# MarketLens AI — Dataset Attribution and Licensing Register

This document provides formal citations, licensing terms, source URLs, and acquisition statuses for all public datasets investigated and acquired for **MarketLens AI**.

---

## 1. Primary Acquired Dataset: UCI Online Retail II

- **Dataset Identifier:** `uci_online_retail_ii`
- **Dataset Name:** Online Retail II
- **Acquisition Status:** **Acquired & Verified** (2026-10-27)
- **Publisher / Repository:** UC Irvine Machine Learning Repository
- **Creator / Author:** Daqing Chen (London South Bank University)
- **Official Repository Landing Page:** https://archive.ics.uci.edu/dataset/502/online+retail+ii
- **Direct Download Endpoint:** https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip
- **Digital Object Identifier (DOI):** [https://doi.org/10.24432/C5CG6D](https://doi.org/10.24432/C5CG6D)
- **Applicable License:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)
- **Allowed Uses:** Academic research, modification, distribution, and commercial use with proper attribution.
- **Formal Academic Citation:**
  > Chen, D. (2012). *Online Retail II* [Dataset]. UC Irvine Machine Learning Repository. https://doi.org/10.24432/C5CG6D
- **Acquired Files & Provenance:**
  - `data/raw/uci_online_retail_ii/online_retail_ii.zip` (45,622,418 bytes, SHA-256: `572e36277c2390fbfde10664750731e0a86f55e33470d91919085f0408e67bfb`)
  - `data/raw/uci_online_retail_ii/online_retail_II.xlsx` (45,622,278 bytes, SHA-256: `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`)
- **Known Limitations & Usage Terms:**
  - Contains retail transactions between Dec 2009 and Dec 2011.
  - Cancellations and returns are indicated by invoice numbers starting with `'C'` and negative quantities.
  - Does **not** contain competitor price observations, customer review text, or product unit wholesale costs.

---

## 2. Investigated Candidates (Not Acquired in Phase 1)

### Candidate B: Brazilian E-Commerce Public Dataset by Olist
- **Dataset Identifier:** `olist_brazilian_ecommerce`
- **Publisher:** Olist & Kaggle
- **Official URL:** https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
- **License:** Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)
- **Acquisition Status:** **Blocked (Credentials Required)**
- **Blocking Reason:** Requires local Kaggle API credentials (`~/.kaggle/kaggle.json` or `KAGGLE_USERNAME`/`KAGGLE_KEY`). In accordance with project policy, credentials were not assumed or bypassed.
- **Role:** Supplementary customer review and order-level sentiment benchmark.
- **Cross-Dataset Boundary:** Product IDs are Brazilian e-commerce specific and cannot be merged with UK transactions from UCI.

### Candidate C: M5 Forecasting Accuracy
- **Dataset Identifier:** `m5_forecasting`
- **Publisher:** University of Nicosia / Walmart / Kaggle
- **Official URL:** https://www.kaggle.com/competitions/m5-forecasting-accuracy/data
- **License:** Kaggle Competition Rules
- **Acquisition Status:** **Blocked (Credentials & Size Budget)**
- **Blocking Reason:** Requires Kaggle competition rules acceptance and API credentials; full bundle (>500 MB) exceeds Phase 1 download budget.
- **Role:** High-frequency store-item daily sales forecasting benchmark.

### Candidate D: Amazon Reviews 2023 (Category Subset)
- **Dataset Identifier:** `amazon_reviews_2023`
- **Publisher:** UC San Diego McAuley Lab
- **Official URL:** https://amazon-reviews-2023.github.io/
- **License:** Academic Research Use Only
- **Acquisition Status:** **Deferred / Optional**
- **Decision Reason:** The full corpus exceeds 100 GB; deferred for targeted category streaming in Phase 4 if LLM review benchmarking requires it.
