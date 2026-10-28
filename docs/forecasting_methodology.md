# MarketLens AI — Demand Forecasting Methodology

**Document Version:** 1.0.0  
**Phase:** Phase 2 (Canonical Modeling & Demand Forecasting)  
**Status:** Approved & Implemented  
**Date:** 2026-10-28  

---

## 1. Mathematical Formulation

Let $\mathcal{I} = \{1, \dots, N\}$ denote the set of canonical products (SKUs), and let $t \in \{1, \dots, T\}$ denote discrete, weekly periods aligned to Mondays (`W-MON`).

For any SKU $i \in \mathcal{I}$ at forecast origin $t$, our objective is to predict total unit sales $h$ periods ahead:
$$\hat{Q}_{i, t+h} = f(\mathbf{x}_{i, t}; \boldsymbol{\theta})$$

In Phase 2, the primary forecast horizon is **$h = 1$ week ahead**.

The feature vector $\mathbf{x}_{i, t}$ is conditioned strictly on observations up to and including time $t$:
$$\mathbf{x}_{i, t} \in \sigma\big(\{Q_{i, \tau}, P_{i, \tau}\}_{\tau \le t}\big)$$

No information from periods $t+1, \dots, t+h$ is ever permitted into $\mathbf{x}_{i, t}$.

---

## 2. Feature Engineering & Anti-Leakage Protocol

To ensure 100% leakage-safe predictions across arbitrary horizons $h \ge 1$:

### A. Lag Features
Lagged sales are shifted by at least $h$:
$$\text{lag\_k}(t) = Q_{i, t - (h - 1) - (k - 1)} = Q_{i, t - k + 1}$$
For $h=1$:
- $\text{lag\_1} = Q_{i, t}$ (sales of the week just ended)
- $\text{lag\_2} = Q_{i, t-1}$
- $\text{lag\_3} = Q_{i, t-2}$
- $\text{lag\_4} = Q_{i, t-3}$

### B. Rolling Summary Statistics
Summary statistics are computed over trailing windows shifted by $h$:
$$\text{rolling\_mean\_4w}(t) = \frac{1}{4} \sum_{k=1}^4 Q_{i, t - k + 1}$$
$$\text{rolling\_std\_4w}(t) = \sqrt{\frac{1}{3} \sum_{k=1}^4 \left(Q_{i, t - k + 1} - \text{rolling\_mean\_4w}(t)\right)^2}$$

### C. Exogenous Price Signals
$$\text{price\_ratio\_to\_avg}(t) = \frac{P_{i, t}}{\bar{P}_{i, \text{hist}}}$$
where $\bar{P}_{i, \text{hist}}$ is computed strictly over the historical training window to prevent future price contamination.

### D. Automated Perturbation Leakage Proof
As implemented in [temporal.py](file:///d:/Professional%20Projects/Agentic_Dynammic_Intelligence_Platform/src/marketlens/features/temporal.py):
If target $y_{i, t+h}$ is perturbed by $+10^6$, the feature matrix $\mathbf{X}_t$ remains bitwise identical. Any drift raises an immediate `RuntimeError`.

---

## 3. Evaluated Forecasting Models

MarketLens AI implements four distinct baseline and statistical models to establish rigorous performance bounds:

### 1. Naive Baseline (Last Observed Value)
$$\hat{Q}_{i, t+h}^{\text{naive}} = Q_{i, t}$$
Carries forward the most recently completed period's demand. Serves as the critical benchmark for assessing value-add from statistical and ML models.

### 2. Moving Average (4-Week Window)
$$\hat{Q}_{i, t+h}^{\text{MA4}} = \frac{1}{4} \sum_{k=0}^{3} Q_{i, t-k}$$
Smooths high-frequency weekly noise by averaging the preceding 4 weeks.

### 3. Ridge Regression ($L_2$ Regularization)
Minimizes regularized mean squared error over engineered temporal features:
$$\min_{\mathbf{w}, b} \sum_{k} \left(y_k - \mathbf{w}^T \mathbf{x}_k - b\right)^2 + \alpha \|\mathbf{w}\|_2^2$$
Features are standardized using `StandardScaler` fitted strictly on the training partition.

### 4. Random Forest Regressor
Non-linear ensemble of decision trees with bootstrap aggregation:
- Estimators: 100 trees
- Max Depth: 10
- Non-negativity clip: $\hat{Q} = \max(0, \hat{y})$

---

## 4. Evaluation Metrics

All metrics are implemented in [metrics.py](file:///d:/Professional%20Projects/Agentic_Dynammic_Intelligence_Platform/src/marketlens/forecasting/metrics.py) with full zero-division safety:

### Mean Absolute Error (MAE)
$$\text{MAE} = \frac{1}{N} \sum_{k=1}^N |y_k - \hat{y}_k|$$

### Root Mean Squared Error (RMSE)
$$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{k=1}^N (y_k - \hat{y}_k)^2}$$

### Weighted Absolute Percentage Error (WAPE)
Scale-independent and robust to intermittent zero-demand periods:
$$\text{WAPE} = \frac{\sum_{k=1}^N |y_k - \hat{y}_k|}{\sum_{k=1}^N y_k}$$

### Mean Absolute Scaled Error (MASE)
Normalizes MAE against the in-sample naive benchmark step:
$$\text{MASE} = \frac{\text{MAE}}{\frac{1}{T_{\text{train}}-1} \sum_{t=2}^{T_{\text{train}}} |y_t - y_{t-1}|}$$
$\text{MASE} < 1.0$ indicates superior performance relative to the one-step naive benchmark.

### Coefficient of Determination ($R^2$)
$$R^2 = 1 - \frac{\sum_{k=1}^N (y_k - \hat{y}_k)^2}{\sum_{k=1}^N (y_k - \bar{y})^2}$$
*Note:* In out-of-sample temporal holdout testing under volatile retail demand, $R^2$ may legitimately be negative when models perform worse than predicting the test-set mean.

---

## 5. Chronological Validation Architecture

To strictly mirror real-world production forecasting, data is partitioned chronologically across all products:
- **Training Window:** Oldest 70% of chronological weekly timestamps.
- **Validation Window:** Middle 15% of chronological timestamps.
- **Test Window:** Most recent 15% of chronological timestamps (strictly held out).

Random shuffling, future cross-validation, and k-fold cross validation across time are prohibited.
