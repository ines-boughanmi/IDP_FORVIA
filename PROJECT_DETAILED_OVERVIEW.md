# PROJECT DETAILED OVERVIEW

## Table of Contents
- 1. Project Overview
- 2. System Architecture
- 3. Backend (FastAPI)
- 4. Frontend (React)
- 5. Machine Learning Pipeline
- 6. Risk Scoring System
- 7. Data Flow (Step-by-step)
- 8. Key Features
- 9. Strengths of the Project
- 10. Limitations
- 11. Jury Preparation
- 12. Final Summary

---

## 1. Project Overview

- What is the project?
  - A Supplier Risk Monitoring and Analytics platform for SAP P2P (Procure-to-Pay) data designed to detect, prioritize and surface transactional and supplier-level risks through a web dashboard and APIs.

- Problem it solves
  - Provides continuous monitoring of purchase-to-pay transactions to surface anomalous or risky behaviours (supplier anomalies, suspicious transactions, aging/GR-IR issues) to reduce manual review and support decision-making.

- Business context
  - Operates in the SAP P2P domain where organizations need operational controls, supplier oversight and early detection of process issues or fraud risk in procurement and payments.
  - Integrates with typical SAP extracts or CSV dumps representing purchase orders, goods receipts, invoices and payment runs.

- Final objective of the system
  - Deliver an end-to-end monitoring stack: ingest SAP P2P data, compute risk indicators and scores, produce dashboards and APIs for investigation and alerting, and support analyst workflows with Supplier 360 and transaction drill-downs.

---

## 2. System Architecture

- High-level components
  - Frontend: Single Page Application (React + Vite) for dashboards, visualizations and investigator UI.
  - Backend: FastAPI application exposing REST endpoints, orchestrating data loading, scoring and serving analytics.
  - ML Layer: Offline/online model components for scoring transactions and suppliers (classification, clustering, anomaly detection).
  - Storage: Lightweight development DB (SQLite) and file-based artifacts for model persistence; production would use RDBMS/warehouse.

- Data flow (summary)
  1. Data ingestion: CSV / SAP extracts uploaded or scheduled ingestion into backend.
  2. Preprocessing & feature engineering: backend services transform raw records into features required by ML.
  3. Scoring: ML models compute risk and labels; caching layer stores results.
  4. Serving: APIs deliver aggregated metrics, drill-downs and time series to the frontend.
  5. Presentation: React UI visualizes scores, trends and supports analyst actions.

- Inter-layer communication
  - Frontend ⇄ Backend: HTTPS REST calls (JSON), environment-driven base URL.
  - Backend ⇄ ML: Direct invocation of local model objects or loading serialized artifacts; background batch jobs handle training and re-scoring.
  - Backend ⇄ Storage: ORM or direct DB access for metadata; file system for model artifacts and cached results.

- API structure overview
  - Routers grouped by domain (analytics, transactions, suppliers, auth). Endpoints provide aggregates (risk distributions), entity detail (supplier 360), and time-series.

---

## 3. Backend (FastAPI)

- Modules and responsibilities
  - `main`/app: Application bootstrap, middleware, router inclusion and CORS/security settings.
  - `routers`: HTTP route handlers grouped by functional area (analytics, transactions, auth, etc.). They validate input and return formatted responses.
  - `services`: Business logic layer — data loaders, scoring orchestration, caching and aggregation helpers.
  - `models` (Pydantic / ORM models): Request/response schemas and persistent model definitions.
  - `db`: Database connection and simple persistence utilities (development uses SQLite).
  - `auth` (if present): Authentication endpoints and token management.

- Key endpoints and purposes (representative)
  - GET /analytics/risk-distribution — returns risk buckets and counts for dashboards.
  - GET /suppliers/{id} — Supplier 360: profiles, aggregated metrics, recent transactions.
  - GET /transactions — filtered transaction listing with risk score and metadata.
  - POST /auth/token (if implemented) — returns JWT for protected endpoints.

- Authentication
  - If JWT or token-based authentication exists, a typical pattern is: login endpoint issues token; middleware verifies token and injects user identity into requests. For sandbox deployments access may be open.

- Data loading and caching logic
  - Data ingestion service parses SAP extracts and normalizes fields (PO, GR, Invoice, supplier id, amounts, dates).
  - Feature caches: computed feature vectors and scoring outputs are cached to speed repeated API responses and dashboards.
  - Aggregation cache: precomputed summaries (daily, weekly) reduce on-the-fly computation for charts.

---

## 4. Frontend (React)

- Pages structure
  - Login / Landing (if auth present)
  - Dashboard (overview with KPIs and risk distribution)
  - Supplier 360 (detailed view of a supplier)
  - Transactions list and drill-down page
  - Settings / Data upload page

- Dashboard explanation
  - Top-level KPIs: total transactions, flagged count, high risk count, trending risk.
  - Visual panels: risk distribution (pie/bar), time series of risk volume, top risky suppliers, and recent alerts.
  - Quick filters by time, supplier group, or transaction type.

- Components architecture
  - Page containers coordinate data fetch and state.
  - Reusable UI components: KPI cards, data tables, filters, charts (chart wrappers), and detail modals.
  - Services layer: `apiClient` centralizes API URL and fetch helpers (reads `import.meta.env` for base URL).

- Data fetching logic
  - Client uses REST calls to backend endpoints; each page requests the minimal set of endpoints for its visualizations.
  - Caching and optimistic UI patterns are applied in small scope (component-level caching or state libraries if used).

- Visualization
  - Charts (line, bar, pie) show temporal trends and distributions.
  - Tables present sortable, pageable transaction lists with risk scores and links to supplier 360.
  - Maps or network graphs may be used for supplier relationships if available.

---

## 5. Machine Learning Pipeline

- Dataset description
  - Source: SAP P2P extracts (purchase orders, goods receipts, invoices, payments) and supplier master data.
  - Typical fields: PO number, invoice number, supplier id, amounts, line items, GR/IR dates, posting dates, payment terms, GL accounts, tax codes.

- Feature engineering (major features)
  - Temporal features: invoice-to-GR lag, invoice aging, payment delays, frequency of invoices per supplier.
  - Monetary features: average invoice amount, variance, large one-off transactions.
  - Behavioral features: number of different vendors with similar bank accounts, sudden jumps in volume.
  - Categorical encoding: supplier categories, GL account mappings, tax codes.
  - Aggregates: rolling averages, counts per time window, supplier-level aggregates (mean, std).

- Models used and purposes
  - Logistic Regression
    - Purpose: baseline supervised classifier when labeled examples or proxy labels exist; interpretable coefficients for features.
  - Random Forest
    - Purpose: non-linear supervised classifier to capture complex interactions; robust to noisy features and useful for feature importance.
  - KMeans
    - Purpose: unsupervised clustering to segment suppliers/transactions into behavior groups for profiling (e.g., typical vs outlier clusters).
  - Isolation Forest
    - Purpose: unsupervised anomaly detector to surface anomalous transactions or supplier behaviors when labels are unavailable.

- Training approach
  - Offline training on historical extracts; cross-validation for hyperparameter selection.
  - When no ground truth exists, use proxy labels (rules-based flags) or anomaly detection as pseudo-supervision.
  - Models persisted to disk as serialized artifacts for fast loading by backend.

- Evaluation metrics
  - Supervised models: precision, recall, F1, ROC-AUC; emphasis on precision at top-k for analyst triage.
  - Unsupervised models: anomaly rate analysis, manual inspection of top anomalies, cluster cohesion metrics (silhouette) for clustering.

---

## 6. Risk Scoring System

- How `risk_score` is computed
  - Composite score combining model outputs and deterministic business rules.
  - Typical formula: weighted sum of ML anomaly score + supervised probability + rule-based points (e.g., GR/IR mismatch, very old invoices, high amounts).
  - Scores normalized to a 0–100 scale or bucketed into discrete levels.

- Meaning of risk levels
  - LOW: score below threshold — routine transactions.
  - MEDIUM: merits review but low urgency.
  - HIGH: likely problematic; analyst review recommended.
  - CRITICAL: immediate action or stop payment recommended.

- Business rules used
  - GR/IR mismatch: invoices not matched to goods receipts flagged.
  - Aging thresholds: invoices older than X days without resolution add risk points.
  - Supplier risk: suppliers with prior anomalies or suspicious patterns accrue points.
  - Amount thresholds: large single transactions above configured limits escalate risk.

---

## 7. Data Flow (Step-by-step)

- Input data
  1. SAP extracts (POs, GRs, Invoices, Payments) are uploaded or fetched by the ingestion process.

- Processing
  2. Normalization: unify date fields, currency conversion, and standardize supplier identifiers.
  3. Feature engineering: compute lags, aggregates, ratios and categorical encodings.
  

- ML
  4. Scoring: run Isolation Forest for anomalies, Random Forest/Logistic Regression for supervised risk probabilities, KMeans for cluster labels.
  5. Risk scoring: combine ML outputs with rule-based checks into a final `risk_score` and `risk_level`.

- Serving
  6. Cache/persist scored results and aggregates.
  7. API endpoints expose summaries, top anomalies, and entity-level detail.

- Frontend display
  8. Dashboard queries API to render KPIs, charts and lists; analysts drill into Supplier 360 and transactions for triage.

---

## 8. Key Features

- Supplier 360 view
  - Consolidated supplier profile with history, risk score trend, top transactions and propensity indicators for risk.

- Transaction analysis
  - List and filter transactions by score, date, amount, and rule triggers; drill-down to raw transaction metadata.

- Alert system
  - Automated flags for newly scored critical/high transactions; exportable lists for workflows.

- Analytics dashboard
  - Time series of risk volume, distribution by supplier groups, top contributing rules and feature importances.

---

## 9. Strengths of the Project

- Technical strengths
  - Clear separation of concerns (frontend, backend, ML).
  - Use of multiple ML methods (supervised + unsupervised + clustering) to provide complementary signals.

- Business value
  - Accelerates detection and prioritization of risky transactions, reduces manual effort and supports audit/compliance activities.

- Scalability
  - Architecture allows replacing SQLite with a production RDBMS and moving model scoring to batch/stream processing.

- ML usage
  - Ensemble approach increases robustness; interpretable baseline (logistic) plus stronger non-linear models (random forest).

---

## 10. Limitations (IMPORTANT)

- No fraud ground truth
  - Lack of labeled fraud events forces reliance on proxy labels and unsupervised methods; limits supervised model accuracy.

- Risk scoring vs fraud detection
  - Risk scoring surfaces anomalies and policy breaches but is not definitive proof of fraud.

- Batch processing vs real-time
  - Current pipeline is primarily batch-oriented; real-time detection requires streaming ingestion and low-latency scoring.

- Model limitations
  - Potential concept drift as supplier behaviour changes; need for periodic retraining and monitoring of model performance.

---

## 11. Jury Preparation

- Most likely questions
  - How do you validate the models without labeled fraud? Suggested answer: use proxy labels from rule-based heuristics, analyst feedback loops and manual review of top anomalies; track precision at top-k.
  - Can the system run in real-time? Suggested answer: architecture supports it conceptually; productionizing requires streaming ingestion, a model serving layer (e.g., Triton or FastAPI model endpoints) and a message queue.
  - How do you prevent false positives from disrupting operations? Suggested answer: tune thresholds, use multi-signal consensus (ML + rules), and provide human-in-the-loop workflows with clear overrides.

- Suggested concise answers
  - Emphasize the platform’s role as a prioritization and monitoring tool, not an arresting mechanism.
  - Clarify that models augment analyst capacity; final decisions remain with humans.

- Common traps and responses
  - Trap: "Your models must be 100% accurate." Response: "No model is perfect; we aim for actionable precision at the top results and continuous improvement."  
  - Trap: "How do you handle data quality issues?" Response: "We standardize and validate ingested extracts, have data-quality checks, and surface missing/invalid records for remediation."  
  - Trap: "Is this deployable in enterprise SAP landscapes?" Response: "Yes—ingestion adapters and secure connectors would be added; persistence can be moved to enterprise DB/warehouse and models deployed in scalable infrastructure."

---

## 12. Final Summary (Executive, 10 lines)

- A Supplier Risk Monitoring platform for SAP P2P that ingests transactional data, computes features and applies an ensemble of ML and rules to score risk.  
- Provides a React dashboard and FastAPI backend to surface prioritized anomalies and supplier profiles.  
- Uses supervised classifiers for probability estimates, Isolation Forest for anomaly detection and clustering for profiling.  
- Combines ML outputs with deterministic business rules (GR/IR, aging, thresholds) to compute `risk_score`.  
- Designed to support analyst workflows with Supplier 360, transaction drill-downs and alert lists.  
- Strengths: modular architecture, ensemble ML approach, clear business alignment for procurement risk.  
- Limitations: lack of labeled fraud ground truth, batch-oriented processing and potential model drift.  
- Productionization requires secure connectors, scalable persistence and an operational model-serving layer.  
- Goal: reduce manual review effort and accelerate detection of high-priority procurement risks.  
- Outcome: a pragmatic, extensible monitoring stack ready for enterprise adaptation and iterative improvement.

---

*Document generated to provide a detailed, structured overview for presentation and technical review.*

---

**ML DEEP DIVE — `src/` (file-by-file, pipeline, models, features, critique)**

This section enriches the existing overview with a focused, technical analysis of the `src/` folder and the ML logic found in the project. It is written for an academic jury and assumes the reader will present, defend, and operationalize the ML components.

## STEP 1 — File-by-file analysis (src/)

Note: below each entry contains: (1) file name, (2) short purpose, (3) role in ML pipeline, (4) principal functions/classes, (5) data used, (6) outputs produced, (7) key connections to other files.

- `src/README.md`
  - Purpose: Project-specific notes and quick start for the `src` ML workspace.
  - Role: Human-oriented onboarding; documents notebooks, scripts and data layout used by the ML pipeline.
  - Functions/classes: N/A (documentation).
  - Data used: references raw/ and processed/ CSVs.
  - Outputs: instructions to reproduce EDA, anomaly detection and clustering outputs.
  - Connections: points to `src/scripts/*` and `src/notebooks/*` (orchestrates pipeline understanding).

- `src/models/` (directory)
  - Purpose: Persisted ML artifacts (models and preprocessing objects).
  - Role: Model registry for inference and optional redeployment; contains both supervised models and preprocessors.
  - Files found and role:
    - `logistic_regression_model.pkl` — trained LogisticRegression estimator (supervised classifier).
    - `random_forest_model.pkl` — trained RandomForestClassifier (supervised classifier, used for prediction and feature importance).
    - `xgboost_model.pkl` / `lightgbm_model.pkl` — optional boosted-tree models if trained; improve predictive accuracy.
    - `scaler.pkl` — StandardScaler used to normalize features at inference/training time.
    - `label_encoder.json` — mapping between label names and encoded integers.
  - Data used: trained on `src/data/processed` feature files (see below).
  - Outputs: binary model files and scaler used in inference and scoring.
  - Connections: loaded by `src/scripts/execute_ml_pipeline.py`, by notebooks (`07_model_evaluation.ipynb`, `08_deployment_pipeline.ipynb`) and by any inference wrapper.

- `src/notebooks/` (directory)
  - Purpose: Interactive notebooks for the project lifecycle: business understanding, EDA, preparation, feature engineering, model training, evaluation and deployment pipeline.
  - Role: Canonical record of exploratory analysis and the reproducible training steps. Notebooks document training procedures used to create artifacts in `src/models/`.
  - Key notebooks: `06_model_training.ipynb` (training), `07_model_evaluation.ipynb` (metrics), `08_deployment_pipeline.ipynb` (examples to load and use saved models), `02_data_understanding.ipynb`, `04_feature_engineering.ipynb`.
  - Data used: `src/data/processed/*.csv` and label files in `src/data/rule_based_labels/`.
  - Outputs: artifacts saved to `src/models/`, reporting files and CSVs in `src/data/processed` or `outputs/`.
  - Connections: demonstrate how `scripts/execute_ml_pipeline.py` replicates notebook logic programmatically.

- `src/data/` (directory)
  - Purpose: central data store used by ML routines.
  - Subfolders and role:
    - `raw/` — original SAP extracts (Ariba CSVs) used as source-of-truth for ingestion.
    - `processed/` — CSVs with cleaned rows, engineered features and final ML-ready X/y. Examples include `p2p_monitoring_dataset.csv`, `ml_features_phase2_X.csv`, `ml_features_phase2_y.csv`, `documents_with_labels_and_features_*.csv`.
    - `rule_based_labels/` — CSVs that provide labels derived from deterministic rules (used as weak / proxy supervision): e.g. `documents_labels_*.csv`.
    - `risk_scores/` — storing generated scores (when pipeline executed).
  - Role in pipeline: `raw/` → cleaning → `processed/` → feature engineering → training/inference.

- `src/scripts/feature_engineering.py`
  - Purpose: central FeatureEngineer class that implements all feature creation steps.
  - Role: deterministic transformation layer that converts SAP fields into model-ready numerical and categorical features; used in both training and inference to guarantee feature parity.
  - Key functions/classes: `FeatureEngineer` with methods: `create_financial_features`, `create_temporal_features`, `create_supplier_features`, `create_operational_features`, `create_categorical_features`, and `create_all_features` (pipeline wrapper). Also `get_feature_list`, `get_numeric_features`, `get_categorical_features`.
  - Data used: raw SAP columns (many prefixed with SAP-like keys, e.g. `amount_|_wrbtr_sum`, `posting_date_|_budat_min`, `supplier_|_lifnr`).
  - Outputs: enriched DataFrame with features used by models and by risk scoring engine; feature lists used to build X for training.
  - Connections: used by `execute_ml_pipeline.py`, notebooks, `supplier_intelligence_core.py`, `risk_scoring_engine.py` and any script producing `ml_features_*.csv`.

- `src/scripts/model_anomaly.py`
  - Purpose: multi-method anomaly detection: IsolationForest (unsupervised), Z-score and IQR detectors plus consistency checks.
  - Role: provides unsupervised signals to augment rule-based checks and supervised model outputs (used in component scoring and supplier features).
  - Key class/methods: `AnomalyDetector` with `fit`, `predict`, `zscore_detection`, `iqr_detection`, `consistency_check`, `get_summary`.
  - Data used: numeric features extracted by FeatureEngineer (or any numeric columns), often aggregated per transaction or supplier.
  - Outputs: anomaly flags (`anomaly_if_flag`), anomaly scores, zscore/IQR flags and consistency flags; CSVs or DataFrames used downstream for `supplier_anomaly_rate` and scoring.
  - Connections: invoked in notebooks and in `supplier_intelligence_core.py` or in production-like pipelines for anomaly supplement.

- `src/scripts/model_clustering.py`
  - Purpose: supplier segmentation using K-Means, cluster profiling and labeling (Tier assignment).
  - Role: groups suppliers into behavioral segments used by analysts and by supplier-level scoring.
  - Key class/methods: `SupplierClustering` with `create_supplier_features`, `prepare_data`, `find_optimal_k`, `fit`, `predict`, `get_cluster_profiles`, `label_clusters`.
  - Data used: aggregated supplier-level features (counts, total/avg amounts, std, CV) produced by FeatureEngineer or by `SupplierBehavioralFeatures`.
  - Outputs: cluster labels for suppliers, cluster profiles summary CSV, labeled `suppliers_segmented.csv`.
  - Connections: used by notebooks, and the clustering output is optionally consumed by `supplier_intelligence_core.py` and by the dashboard as supplier segments.

- `src/scripts/execute_ml_pipeline.py`
  - Purpose: production-like, non-interactive orchestration of the full ML pipeline: load features, QC, train models, save models & registry, run predictions and save outputs.
  - Role: canonical training script used to generate `src/models/*.pkl` and `model_registry.json`.
  - Key steps implemented: load X/y (`ML_FEATURES_X_FILE`, `ML_FEATURES_Y_FILE`), preprocessing (StandardScaler), resampling (SMOTE), training (LogisticRegression, RandomForest, optional XGBoost/LightGBM), cross-validation, saving models/scaler/encoder, generating predictions and saving summary.
  - Data used: `src/data/processed/ml_features_phase2_X.csv` and label files in `src/data/processed`.
  - Outputs: saved models in `src/models/`, `ml_predictions.csv`, `ml_pipeline_summary.json`, and `model_registry.json`.
  - Connections: central link between notebooks, model artifacts and subsequent inference code.

- `src/scripts/risk_scoring_engine.py` and `risk_scoring_engine_v2.py`
  - Purpose: deterministic, explainable scoring engines that combine rule signals, ML probability (when available), financial and temporal metrics into a final `risk_score_transaction` and `risk_level_transaction` and similarly for suppliers.
  - Role: orchestrates how ML outputs (probabilities / confidences) and rule-engine outputs are combined into a business-friendly risk score and risk tier.
  - Key classes/methods: `TransactionRiskScorer` (`score_ruleengine_signal`, `score_ml_probability`, `score_amount_anomaly`, `score_temporal_signal`, `compute_transaction_scores`), `SupplierRiskScorer` (aggregates transaction scores), `RiskExplainer` (human-friendly explanations).
  - Data used: full enriched DataFrame with features, `anomaly_class` (rule outputs), `ml_prediction_confidence` (if produced) and outputs from `FeatureEngineer` and anomaly detectors.
  - Outputs: `risk_score_transaction`, `risk_level_transaction`, `supplier_risk_score`, `supplier_risk_level`, explanation texts.
  - Connections: central to API output and to frontend displays, it is the business translation of ML outputs into actionable signals.

- `src/scripts/supplier_intelligence_core.py`
  - Purpose: advanced supplier-level behavioral feature engineering and an alternate supplier risk engine (phase 2).
  - Role: computes temporal, financial, behavioral and business features per supplier and contains `AdvancedSupplierRiskEngine` that computes composite supplier risk using weighted components and percentiles.
  - Key classes/methods: `SupplierBehavioralFeatures`, `AdvancedSupplierRiskEngine` (`create_supplier_feature_matrix`, `compute_supplier_risk`).
  - Data used: scored transactions (with `risk_score_transaction`) and raw transaction histories from `processed/` files.
  - Outputs: supplier feature matrix and `supplier_risk_score` per supplier; tiers computed by percentiles (LOW/MEDIUM/HIGH/CRITICAL).
  - Connections: used in Phase 2 notebooks and for supplier-level dashboards, can re-compute supplier risk independently of `risk_scoring_engine.py`.

- `src/scripts/phase*_*.py` and `run_ml_validation.py`, `ml_validation_clean.py` etc.
  - Purpose: orchestration scripts that implement project-specific phases (phase1 risk scoring, phase2 recalibration, validation and data productization steps).
  - Role: glue code that runs the pipeline in stage-specific sequences and produces outputs and validation artifacts.
  - Functions: often call `FeatureEngineer`, `AnomalyDetector`, `SupplierClustering`, `TransactionRiskScorer` and save results to `src/data/processed` or `outputs/`.
  - Connections: operationalizes the training/prediction workflows for different project phases.

- `src/scripts/utils.py`, `logger.py`, `config.py`
  - Purpose: utility functions, logging and configuration constants (file paths, MODEL_DIR and feature file names).
  - Role: shared helpers that ensure consistent paths and logging across scripts.
  - Connections: imported by `execute_ml_pipeline.py` and many scripts.

## STEP 2 — ML pipeline global view (raw → features → models → score)

- Full pipeline (operational view)
  1. Data ingestion: raw SAP/Ariba extracts placed into `src/data/raw/`.
 2. Data cleaning & normalization: Jupyter notebooks or `scripts/sap_p2p_pipeline.py` / cleaning scripts transform raw columns and save processed CSVs in `src/data/processed/`.
 3. Feature engineering: `FeatureEngineer.create_all_features()` produces transactional and supplier features (financial, temporal, supplier aggregates, categorical encodings).
 4. Labeling: if supervised training is desired, rule-based labels from `src/data/rule_based_labels/` are merged to create `y`. This creates weak / proxy labels (e.g., INVOICED_NOT_DELIVERED).
 5. Training (if executed): `scripts/execute_ml_pipeline.py` loads `ml_features_X` and `ml_features_y`, applies scaling (StandardScaler), class balancing (SMOTE), trains multiple models (LogisticRegression, RandomForest, XGBoost/LightGBM), cross-validates and saves artifacts to `src/models/`.
 6. Unsupervised analysis: `model_anomaly.py` (IsolationForest / Z-score / IQR) is trained (IsolationForest.fit) on numeric features for anomaly scoring and used to produce anomaly flags.
 7. Supplier-level processing: `model_clustering.py` and `supplier_intelligence_core.py` generate supplier clusters and behavioral features; these feed supplier risk scoring.
 8. Risk scoring: `risk_scoring_engine.py` consumes rule outputs, ML probability/confidence, anomaly flags and deterministic features to compute `risk_score_transaction` and `risk_level_transaction`, and aggregates per supplier.
 9. Serving: the results CSVs or persisted DB rows are then consumed by backend services (`api/` folder) and shown in the frontend.

---

## AI Risk Assistant – RAG Chatbot Module

This section documents the newly integrated AI Risk Assistant, a lightweight Retrieval-Augmented Generation (RAG) chatbot embedded into the existing dashboard.

Architecture overview
- Frontend Chat UI (React) → FastAPI endpoint POST `/api/chatbot/query` → `RAGService` (ChromaDB + sentence-transformers) for retrieval → Local Ollama LLM (`llama3.2:1b`) for answer generation → Result returned to frontend.

Data flow
- `RAGService` builds a compact document index from the project's existing `suppliers_df` and `transactions_df` (no new datasets). Documents include supplier id, supplier_name (if present), risk_score and risk_level; transaction id, amount, risk_score and risk_level; anomaly classification when available.
- Embeddings are generated with `sentence-transformers` (default `all-MiniLM-L6-v2`) and stored in an in-memory ChromaDB collection (`p2p_rag`).

Retrieval process
- User question → semantic embedding → ChromaDB top-K retrieval (K=5) → compact context built from returned metadatas (one-line summaries) → prompt assembled for Ollama.

ChromaDB usage
- Lightweight, in-memory Chroma client used to avoid new infrastructure. The collection is constructed at startup (or on first request) and cached on the FastAPI app state to minimize rebuilds.

Embedding generation
- Uses `sentence-transformers` to compute embeddings for documents and queries. Batch encoding is used to reduce memory spikes. Default encoder: `all-MiniLM-L6-v2` (configurable via `RAG_EMBED_MODEL`).

Ollama integration
- Local Ollama endpoint: `http://127.0.0.1:11434/api/generate` (configurable via `OLLAMA_URL`).
- Model used: `llama3.2:1b` (configurable via `OLLAMA_MODEL`).
- Generation params: `temperature=0.2`, `max_tokens=512`.
- Prompt template instructs the model to answer in professional business English, explain risks, mention KPIs, highlight anomalies and give concise recommendations.

Fallback behavior
- If Ollama is unavailable or the call fails, the API returns a deterministic summary constructed from the retrieved records (top suppliers / transactions with scores). The endpoint never crashes and always returns `{ answer, results }`.

Frontend integration
- New page: `frontend/src/pages/ChatbotPage.tsx` (route `/chatbot`) integrates into the sidebar as `AI Risk Assistant` and reuses existing `SectionCard` and theme styles.
- UI features: modern chat interface, user/assistant messages, auto-scroll, loading indicator, and error handling. Mobile-friendly layout using existing CSS.

Business value
- Allows analysts to ask natural language questions about suppliers, transactions, anomalies and KPIs and get concise, actionable explanations referencing real dataset records and ML-derived signals.

Limitations
- In-memory ChromaDB is not persistent across process restarts; for production, persist storage or external vector DB is recommended.
- Embedding model (`all-MiniLM-L6-v2`) trades accuracy for speed and low memory; swap for larger models if needed.

Future improvements
- Persist Chroma to disk or connect to a production vector DB for scale.
- Add index refresh strategy to update the collection when datasets change.
- Add prompt templates, chain-of-thought control or retrieval filtering for higher precision.

- Where training happens
  - Training is performed by `src/scripts/execute_ml_pipeline.py` (and notebooks `06_model_training.ipynb`). This script explicitly trains supervised models and persists them in `src/models/`.

- Where inference happens
  - Inference can happen in two locations:
    - Offline/batch: `execute_ml_pipeline.py` and phase scripts produce batch predictions (`ml_predictions.csv`) and persist scored datasets in `src/data/processed`.
    - At-serving time: deployment notebooks show how to load models and apply them to new records; project structure supports loading pickled models + `scaler.pkl` to compute `ml_prediction_confidence` and feed `risk_scoring_engine`.

- Batch vs Real-time
  - The implemented pipeline and scripts are batch-oriented (CSV-based ingestion, offline training, SMOTE resampling). There is no indication of a streaming, low-latency model-serving component in `src/` (no Kafka/streaming or REST model server). Real-time is conceptually supported but not implemented.

- How models interact
  - Models play complementary roles: supervised classifiers (LogReg, RF, XGBoost/LGBM) produce class probabilities and predictions; unsupervised IsolationForest and statistical detectors produce anomaly flags; clustering (KMeans) segments suppliers. The risk engine combines these signals deterministically (weights in `risk_thresholds_config.py`). The models are therefore independent components whose outputs are combined by rules, not tightly-coupled ensembles.

## STEP 3 — Models (deep explanation)

- Logistic Regression
  - Role: interpretable supervised baseline for classification of transaction states (or risk proxies when labels exist).
  - Input: scaled numeric features (from FeatureEngineer.get_numeric_features + encoded categoricals), typically via `scaler.pkl`.
  - Output: class prediction and probability (used to compute `ml_prediction_confidence`).
  - Usage: model included as a trained artifact; useful as a transparent comparator when explaining coefficients to stakeholders.

- Random Forest
  - Role: stronger non-linear supervised model trained to maximize predictive performance; used as the "default" best performer in notebooks and in `execute_ml_pipeline.py` for generating predictions.
  - Input/Output: same as logistic but with tree-based output and `feature_importances_` available for explainability.
  - Redundancy: RandomForest provides robust signal and feature importance; logistic regression remains for interpretation. Their simultaneous presence is deliberate: accuracy vs interpretability trade-off.

- KMeans
  - Role: unsupervised clustering of suppliers into behavioral tiers for profiling; not used for direct fraud detection but to enrich supplier features and contextualize risk.
  - Input: supplier-level aggregated features (counts, average amounts, CVs, frequencies).
  - Output: cluster assignment (e.g., Tier-1/Tier-2/Tier-3) and cluster profiles used in dashboards.
  - Why present: clustering helps prioritize by business segment and to separate expected behaviour from anomalies within cluster context.

- Isolation Forest
  - Role: unsupervised anomaly detector operating on numeric transaction features; flags rare/atypical transactions.
  - Correctness of use: implemented correctly as an unsupervised detector and combined with robust statistical tests (z-score and IQR). IsolationForest is appropriate where labels are scarce. However, care must be taken to ensure feature scaling is consistent and that contamination rates are tuned to avoid high false-positive rates.

- Training vs Preloaded
  - Models are trained by `execute_ml_pipeline.py` and notebooks; trained artefacts are saved into `src/models/`. At inference time code loads these pickles (see notebooks). So both training and inference are supported: training is offline/batch, inference is by loading serialized models.

- Model independence and combination
  - Models operate mostly independently: supervised models produce probabilities; anomaly detector and Z/IQR provide additional flags; KMeans assigns cluster labels. Combination is deterministic and orchestrated by `risk_scoring_engine.py` where weighted contributions are defined in configuration.

## STEP 4 — Feature engineering (exhaustive summary)

- Feature categories (implemented in `FeatureEngineer`):
  - Financial features: `total_gr_amount`, `total_ir_amount`, `gr_ir_difference`, `abs_gr_ir_diff`, `invoice_ratio`, `unit_price`, `total_quantity`, `amount_per_qty`, `gr_ir_gap_pct`, `blocked_amount`.
    - Importance: these capture the monetary discrepancies (GR vs IR), blocked amounts, and per-unit economics which are direct signals for accounting issues.
    - Example: `gr_ir_gap_pct` measures percent difference between goods receipt total and invoice total — central to detecting mismatches.

  - Temporal features: `posting_date`, `days_in_system`, `posting_month`, `posting_quarter`, `posting_day_of_week`, `gr_ir_delay_flag`, `gr_ir_critical_delay`, `planned_delay_days`.
    - Importance: aging and delays are key leading indicators; older unresolved invoices often indicate broken process flows or disputed amounts.
    - Example: `days_in_system` distinguishes recent vs stale transactions; thresholds feed temporal scoring.

  - Supplier features: supplier aggregates (transaction counts, supplier_total_spend, supplier_avg_amount, supplier_std_amount, supplier_anomaly_rate, supplier_avg_aging, supplier_high_risk, supplier_high_volume).
    - Importance: supplier history contextualizes transaction risk; high anomaly rates or high volume can increase priority.
    - Example: `supplier_anomaly_rate` derived from anomaly detector flags is directly used by `SupplierRiskScorer`.

  - Operational features: flags such as `delivery_completed`, `document_date_known`, `has_outline_agreement`, `has_payment_terms`.
    - Importance: capture process completeness and contractual coverage.

  - Categorical encodings: `plant_|_werks_encoded`, `material_group_|_matkl_encoded`, `purch_organization_|_ekorg_encoded`, `supplier_|_lifnr_encoded`, `purchasing_doc_type_|_bsart_encoded`.
    - Importance: provide categorical context for ML models.

  - Advanced behavioral features (in `supplier_intelligence_core`): volatility CV, high-value ratios, abnormal amount ratios, recency_score, temporal_consistency, duplicate transaction ratio, repeat PO ratio, stability_score. Importance: used in advanced supplier risk scoring and cluster profiling.

## STEP 5 — Risk scoring logic (how score is computed)

- Risk signal components (see `risk_thresholds_config.py` / `risk_scoring_engine.py`):
  - `ruleengine_signal` (40% weight): mapping from deterministic RuleEngine outputs to scores (OK→0, INCOMPLETE→20, DELIVERED_NOT_INVOICED→50, INVOICED_NOT_DELIVERED→100).
  - `ml_probability` (20% weight): inverse of model confidence: `score = (1 - confidence) * 100` so lower confidence → higher risk contribution.
  - `amount_anomaly` (15% weight): composite of gap percentage (GR/IR), invoice ratio deviations, and blocked amount percentage; uses thresholds in `AMOUNT_THRESHOLDS`.
  - `temporal_signal` (15% weight): aging buckets produce increasing risk with time unresolved.
  - `supplier_inherited` (10% weight): supplier-level score inherited to transactions (default 25 if absent).

- Final computation (in `compute_transaction_scores`):
  - Each component computed as a 0–100 score; components assembled into a weighted sum using `TRANSACTION_RISK_WEIGHTS`; normalized and clipped to 0–100.
  - Risk level mapping: 0–25 LOW, 25–50 MEDIUM, 50–75 HIGH, 75–100 CRITICAL.

## STEP 6 — Full data flow (step-by-step)

1. Data ingestion: Raw CSV files stored in `src/data/raw/` are loaded and standardized.
2. Cleaning & normalization: Date parsing, numeric coercion and column-variant mapping happen in preprocessing scripts and notebooks (e.g., `sap_p2p_pipeline.py`, `ml_validation_clean.py`).
3. Feature engineering: `FeatureEngineer.create_all_features()` produces transaction-level features; advanced supplier features computed by `SupplierBehavioralFeatures`.
4. Unsupervised anomaly detection: `AnomalyDetector.fit()`/`predict()` (Isolation Forest) and statistical outliers (Z-score, IQR) tag rows — flags saved into processed CSVs.
5. Labeling: Rule-based labels (files in `src/data/rule_based_labels/`) are used to provide supervised labels when ground truth is absent.
6. Training: `execute_ml_pipeline.py` loads ML features and rule-derived labels, applies scaling, SMOTE, trains multiple models (LR, RF, optionally XGBoost/LightGBM), evaluates with cross-validation, saves models and scaler.
7. Inference: Persisted models are loaded from `src/models/` by deployment notebooks; predictions and confidence scores are written back to datasets.
8. Risk scoring: `risk_scoring_engine` consumes features, rule signals and ML confidence to compute `risk_score_transaction` and `risk_level_transaction` and supplier aggregates.
9. Export/Serve: Final CSVs and registries are saved to `outputs/` or consumed by the backend/dashboard for visualization.

## STEP 7 — Critical analysis (honest assessment)

- Is this real ML training or just inference?
  - The repository contains a full training script (`execute_ml_pipeline.py`) and pre-saved models. Therefore it performs real supervised ML training. In addition, unsupervised components (Isolation Forest, K-Means) are trained when invoked.

- Is there real labeled fraud data?
  - No explicit verified fraud ground-truth is visible. Labels appear to be rule-based proxies stored under `src/data/rule_based_labels/` and derived from GR/IR logic. This is common in procurement analytics but means supervised models are trained on proxy labels, which limits the ability to claim verified fraud detection accuracy.

- Risk of circular validation?
  - Potential: if the same rule-derived signals used to create labels are also present among input features (e.g., `anomaly_class` used in features and also used to derive labels), models may learn to reproduce labeling rules rather than find independent signals. The pipeline should ensure features used for training do not trivially duplicate label logic to avoid leakage.

- Are models redundant or necessary?
  - The presence of logistic regression (interpretability) and random forest / boosted trees (accuracy) is appropriate. Redundancy is intentional (accuracy vs interpretability). IsolationForest and statistical tests are complementary for anomalies. KMeans is orthogonal (profiling). None appear strictly unnecessary, but governance is required to avoid over-weighting overlapping signals.

- Is Isolation Forest correctly used or forced?
  - Implementation is appropriate: IsolationForest is trained on scaled numeric features and combined with Z-score/IQR and consistency checks. However, success depends on feature selection, contamination parameter tuning, and post-hoc validation (manual review of top anomalies). Without evaluation against labeled anomalies the IsolationForest thresholding can produce high false positives.

- Hidden weaknesses
  - Proxy labels: weak supervision yields noisy labels and undermines supervised model generalization.
  - Leakage: variables derived from rules used to label can cause models to memorize labeling rules.
  - Drift & maintenance: no explicit retraining schedule or monitoring in production; models will degrade without periodic recalibration.
  - Class imbalance: addressed via SMOTE in training, but SMOTE can introduce synthetic patterns not present in real data; validation on holdout is necessary.
  - Explainability at scale: only basic explainers exist (feature importance, simple textual explanations). For enterprise adoption consider SHAP-based local explanations.

---

### 🔥 1. SIMPLE EXPLANATION (for beginner — 5–10 lines)

- The ML system transforms raw SAP/Ariba transaction extracts into structured features (financial, temporal, supplier), uses rule-based labels as proxies to train supervised models and also runs unsupervised anomaly detection. Trained models (RandomForest, LogisticRegression) and an IsolationForest are persisted. A deterministic scoring engine combines rule signals, ML confidence and financial/temporal indicators to produce a single `risk_score` per transaction, which is aggregated at supplier level for monitoring.

### 🧠 2. TECHNICAL SUMMARY (for jury — master thesis style)

- This project implements a reproducible batch ML stack for procurement risk monitoring. The pipeline is fully reproducible via `src/scripts/execute_ml_pipeline.py` and associated notebooks: data ingestion → deterministic feature engineering (`FeatureEngineer`) → weak supervision using rule-based labels → resampling and supervised model training (LogisticRegression, RandomForest, optional XGBoost/LightGBM) → unsupervised anomaly detection (IsolationForest + z-score/IQR) → supplier clustering (K-Means) → deterministic risk scoring engine (`risk_scoring_engine.py`) that merges ML and business rules into explainable risk scores. Persisted artifacts under `src/models/` allow inference by the backend. The approach balances explainability (rule engine, logistic baseline, deterministic weights) with predictive power (random forest and boosting), while addressing label scarcity through rule-based proxies and unsupervised anomaly detection.

### 🎤 3. JURY-READY INSIGHT (one strong paragraph)

- The system is a pragmatic and academically defensible approach to procurement risk: it acknowledges label scarcity by combining rule-based weak supervision and unsupervised anomaly detection with supervised learners trained where proxies exist. Its core strength is the explicit separation between statistical signals (ML models and anomaly detectors) and deterministic business logic (GR/IR rules, aging thresholds). For a jury, the central message is that the platform is designed as a prioritization and monitoring tool — not an automated adjudication system — and that its value lies in surfacing actionable investigative leads, offering interpretable scores, and being readily extensible toward production-grade retraining, real-time serving and stronger ground-truth labeling pipelines.

---

*End of ML deep-dive append.*
