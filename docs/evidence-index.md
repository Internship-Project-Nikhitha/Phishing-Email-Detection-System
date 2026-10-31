# Evidence index

Where a reviewer can verify each Qveto deliverable. Status is as of 2026-10-27; update a row only after you
ran its command and saw it pass.

| Deliverable | Where | Command / how to verify | Status |
|---|---|---|---|
| Email schema + preprocessing | `src/preprocessing.py`, `tests/test_preprocessing.py` | `python -m pytest tests/test_preprocessing.py` | Done |
| Content keys | `src/keys.py`, `tests/test_keys.py` | `python -m pytest tests/test_keys.py` | Done |
| Dataset research and candidates | `docs/dataset-research.md`, `docs/dataset-candidates.md` | read; `python scripts/check_pending.py` | Done (research); no dataset approved yet |
| Dataset selection and `configs/dataset.json` | `docs/dataset-selection.md` | read | *(pending: decision needed)* |
| Dataset loader + error counts | `src/dataset.py` | `python -m pytest tests/test_dataset.py tests/test_dataset_errors.py` | Done |
| Duplicate removal + quality audit | `src/quality.py`, `src/audit_dataset.py` | `python -m pytest tests/test_quality.py tests/test_dataset_audit.py` | Done (code); real audit report *(pending dataset)* |
| Leakage-safe split + fingerprint | `src/splitting.py`, `src/data_prep.py` | `python -m pytest tests/test_splitting.py tests/test_data_prep.py tests/test_data_prep_dedupe.py` | Done (code); real split report *(pending dataset)* |
| Metrics + baseline | `src/metrics.py`, `src/baseline.py` | `python -m pytest tests/test_metrics.py tests/test_baseline.py` | Done (code); real baseline report *(pending dataset)* |
| Feature registry | `src/features/base.py` | `python -m pytest tests/test_features_base.py` | Done |
| Sender / URL / text features | `src/features/` | | *(pending)* |
| Model comparison, model card | `reports/`, `docs/model-card.md` | | *(pending)* |
| Explanations, history, upload validation, API, web app | | | *(pending)* |
| Final evaluation and test log | `reports/final_evaluation.md`, `reports/test_log.txt` | | *(pending)* |
