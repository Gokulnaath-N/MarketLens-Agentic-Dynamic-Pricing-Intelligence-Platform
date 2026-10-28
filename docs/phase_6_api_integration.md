# MarketLens AI — Phase 6 API & Frontend Integration Guide

## 1. Architecture Overview

MarketLens AI connects a **React 19 + Vite + TypeScript** web dashboard natively to a **FastAPI REST API** backend over HTTP/JSON.

```
+-------------------------------------------------------------------------+
|                       Browser Application                               |
|  React 19 + TypeScript + Vite + Tailwind CSS + Lucide + Motion + Recharts |
|  AppShell -> DraggableWidgetGrid -> TanStack Query -> Typed API Client  |
+------------------------------------+------------------------------------+
                                     | HTTP/JSON (REST API)
                                     v
+-------------------------------------------------------------------------+
|                         FastAPI Backend                                 |
|  src/marketlens/api/main.py (CORS: localhost:5173, 127.0.0.1:5173)     |
|  Routers: Health | Datasets | Forecasts | Market Intelligence | Pricing |
+------------------------------------+------------------------------------+
                                     | Service Calls
                                     v
+-------------------------------------------------------------------------+
|                  Core Python Analytics & ML Subsystems                  |
|  - Datasets: Registry, TabularDataProfiler, Manifests                   |
|  - Forecasting: Baseline Models, XGBoost, Artifacts                     |
|  - Agents: ReviewInsightAgent, CompetitorMonitorAgent                   |
|  - Pricing: Constrained PricingOptimizer, Elasticity Adapters           |
|  - Experiments: Phase 5 4-Way Feature Ablation Suite                    |
+-------------------------------------------------------------------------+
```

---

## 2. Verified API Endpoints

| HTTP Method | Endpoint | Description | Status Codes |
|---|---|---|---|
| `GET` | `/` | API root probe and metadata | 200 |
| `GET` | `/api/v1/health` | Liveness health check | 200 |
| `GET` | `/api/v1/system/status` | Subsystem diagnostics and manifest tracking | 200 |
| `GET` | `/api/v1/datasets` | Candidate dataset inventory & acquired files | 200 |
| `GET` | `/api/v1/datasets/{id}/profile` | Statistical data profile report | 200, 404 |
| `GET` | `/api/v1/forecasts/models` | Evaluated models, test metrics & preview series | 200 |
| `POST` | `/api/v1/forecasts` | On-demand scenario demand inference | 200, 422 |
| `GET` | `/api/v1/market-intelligence/summary` | Sentiment distribution, aspects, & competitors | 200 |
| `GET` | `/api/v1/market-intelligence/reviews` | Analyzed review records & grounding summaries | 200 |
| `GET` | `/api/v1/market-intelligence/competitors`| Competitor price tracking feeds | 200 |
| `POST` | `/api/v1/pricing/optimize` | Constrained pricing optimization engine | 200, 422 |
| `GET` | `/api/v1/experiments` | Phase 5 feature ablation study summary | 200 |
| `GET` | `/api/v1/experiments/{run_id}` | Full ablation run manifest and metrics | 200, 404 |

---

## 3. Local Startup Instructions

To run MarketLens AI locally, use two separate terminal windows:

### Terminal A: FastAPI Backend
```bash
# Activate virtual environment
.venv\Scripts\activate

# Start Uvicorn server on port 8000
python -m uvicorn marketlens.api.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive API docs are available at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Terminal B: React + Vite Dashboard
```bash
# Enter frontend directory
cd frontend

# Install dependencies (if not already installed)
npm install

# Start Vite development server
npm run dev
```
Dashboard will open at: [http://127.0.0.1:5173](http://127.0.0.1:5173)

---

## 4. Key Frontend Routes & Pages

1. **`/` or `/overview`**: Executive Overview featuring the interactive `DraggableWidgetGrid` with 8 customizable analytics tiles (revenue decisions, model WAPE, competitor signals, acquired rows, review governance, agent perception, active SKUs, subsystem health).
2. **`/data`**: Dataset Explorer with candidate registry, acquired file checksums (SHA-256), and statistical profile viewer (null ratios, distributions, detected keys).
3. **`/forecasting`**: Demand Forecasting with held-out test benchmarks, actual vs. predicted Recharts time-series curves, and live scenario simulator.
4. **`/market-intelligence`**: Perception aspect categories, customer sentiment extractions, and authorized competitor price tracking feeds.
5. **`/pricing`**: Constrained Price Optimizer with objective selector (Revenue vs Profit), gross margin floor guardrails, candidate grid comparison, and human decision recording.
6. **`/experiments`**: Phase 5 Feature Ablation comparison (E0 Baseline, E1 Reviews, E2 Competitor, E3 Hybrid) with WAPE deltas and bar charts.
7. **`/system`**: Operational status diagnostics, module availability indicators, and REST route specifications.
8. **`*`**: Custom 404 NotFound page with recovery navigation.

---

## 5. Security & Safety Protocols

- **Human-in-the-Loop Constraint**: The platform strictly generates human-supervised pricing decision recommendations. Automatic external store price execution or webhook publication is disabled.
- **Secret Hygiene**: Frontend configuration uses only public variables (`VITE_API_BASE_URL`). No secrets or API credentials are included in client bundles.
- **CORS Protection**: Restricted by default to local origins (`http://localhost:5173`, `http://127.0.0.1:5173`).
