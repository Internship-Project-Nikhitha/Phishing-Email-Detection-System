# Evidence index

Where a reviewer can verify each Qveto deliverable. Status is as of the final integration; update a row only after you
ran its command and saw it pass.

| Deliverable | Where | Command / how to verify | Status |
|---|---|---|---|
| Email schema + preprocessing | `src/preprocessing.py`, `tests/test_preprocessing.py` | `python -m pytest tests/test_preprocessing.py` | Done |
| Content keys | `src/keys.py`, `tests/test_keys.py` | `python -m pytest tests/test_keys.py` | Done |
| Dataset research and candidates | `docs/dataset-research.md`, `docs/dataset-candidates.md` | read; `python scripts/check_pending.py` | Done |
| Dataset selection and `configs/dataset.json` | `docs/dataset-selection.md` | read | Done (MeAJOR v2.0, restricted educational use, with documented limitations) |
| Dataset loader + error counts | `src/dataset.py` | `python -m pytest tests/test_dataset.py tests/test_dataset_errors.py` | Done |
| Duplicate removal + quality audit | `src/quality.py`, `src/audit_dataset.py` | `python -m pytest tests/test_quality.py tests/test_dataset_audit.py` | Done; real audit in `reports/dataset_audit.md` and `reports/dataset_sources.md` |
| Leakage-safe split + fingerprint | `src/splitting.py`, `src/data_prep.py` | `python -m pytest tests/test_splitting.py tests/test_data_prep.py tests/test_data_prep_dedupe.py` | Done; real split in `reports/split_summary.md` |
| Metrics + baseline | `src/metrics.py`, `src/baseline.py` | `python -m pytest tests/test_metrics.py tests/test_baseline.py` | Done; real baseline in `reports/baseline_metrics.md` |
| Feature registry | `src/features/base.py` | `python -m pytest tests/test_features_base.py` | Done |
| Sender / URL / text features + pipeline | `src/features/` | `python -m pytest tests/test_features_*.py` | Done |
| Vectorizers, models, saved bundle | `src/vectorize.py`, `src/models.py`, `src/bundle.py` | `python -m pytest tests/test_vectorize.py tests/test_models.py tests/test_bundle.py` | Done; `reports/model_comparison.md`, `docs/model-card.md` |
| Explanations, history, upload validation | `src/explain.py`, `src/storage.py`, `src/ingest.py`, `src/service.py` | `python -m pytest tests/test_explain.py tests/test_storage.py tests/test_ingest.py tests/test_service.py` | Done |
| API and web app | `app/api.py`, `app/streamlit_app.py` | `python -m pytest tests/test_api.py` (needs fastapi, httpx) | Done (API); web app is manual: `streamlit run app/streamlit_app.py` |
| Safety and robustness tests | `tests/test_safety.py`, `tests/test_robustness.py`, `docs/safety.md` | `python -m pytest tests/test_safety.py tests/test_robustness.py` | Done |
| Final evaluation and test log | `reports/final_evaluation.md`, `reports/test_log.txt` | read both; `python -m pytest -q` | Done |
