# Module interfaces (the team contract)

These are the public functions that exist on `main` today and that other modules rely on.
If you must change one, tell the lead and update this file in the same pull request.

## Data records

A **cleaned record** is a dict with four string fields produced by `src/preprocessing.py`:

```
{"subject": str, "body": str, "sender": str, "label": "phishing" | "legitimate"}
```

`preprocess_emails(records)` returns `BatchResult(valid, errors)`; `errors` is a list of
`RecordError(index, message)`.

## Dataset config (`configs/dataset.json`, copied from `configs/dataset.example.json`)

`path`, `columns` (our field -> CSV column; `label` required, `subject` or `body` required),
`label_map` (CSV label text -> `phishing`/`legitimate`), `delimiter`, `encoding`, `max_rows`.
Real config is created only after the dataset is approved (`docs/dataset-selection.md`).

## Functions on `main`

| Module | Owner | Public interface |
|---|---|---|
| `src/preprocessing.py` | Lead (Day 1) | `preprocess_email`, `preprocess_emails`, `normalize_label`, `normalize_text`, `EmailValidationError`, `BatchResult`, `RecordError` |
| `src/keys.py` | Lead | `exact_key(record)`, `near_key(record)`, `key_function(level)`, `record_id(record)` (levels `"exact"`, `"near"`) |
| `src/dataset.py` | Member 2 | `DatasetConfig`, `DatasetError`, `parse_config`, `load_config(path)`, `load_dataset(config_or_path, *, base_dir=None) -> BatchResult`, `categorize_error(message)`, `count_error_reasons(errors)` |
| `src/quality.py` | Members 3 and 1 | `find_duplicate_groups(records, level)`, `deduplicate(records, level) -> DedupResult(records, removed)`, `RemovedRecord(index, record_id, reason, kept_index)`, `audit_quality(records, level) -> QualityAudit`, `audit_dataset(records, ...) -> dict` (privacy-safe counts) |
| `src/splitting.py` | Member 4 | `split_dataset(records, train_size, validation_size, test_size, random_state, stratify, duplicate_level) -> SplitResult(train, validation, test)`, `audit_split_leakage(result, level) -> LeakageReport`, `assert_no_duplicate_leakage`, `fingerprint_split(result, level)` |
| `src/data_prep.py` | Lead | `prepare_splits(config_or_path, *, base_dir, train_size, validation_size, test_size, random_state, stratify, duplicate_level) -> PreparedData(records, errors, duplicate_groups, splits, dedup)` (loads, removes duplicates and label conflicts, then splits) |
| `src/metrics.py` | Member 5 (done by lead) | `confusion_counts`, `compute_metrics(y_true, y_pred) -> dict`, `format_metrics_markdown(metrics, title)` |
| `src/baseline.py` | Member 5 (done by lead) | `record_text`, `build_baseline`, `train_baseline(train_records)`, `predict_labels(model, records)`, `predict_scores(model, records)` |
| `src/features/base.py` | Lead | `FeatureRegistry(prefix).register(name, description)`, `.names()`, `.descriptions()`, `.extract(record)` |
| `src/audit_dataset.py` | Member 1 | command line: `python -m src.audit_dataset configs/dataset.json` |
| `scripts/check_pending.py` | Member 1 | lists unfinished PENDING / UNVERIFIED / TODO / `<FILL` markers in the dataset documents |

## Planned modules (not on `main` yet)

Features (`src/features/sender.py`, `urls.py`, `text.py`, `pipeline.py`), `src/vectorize.py`, `src/models.py`,
`src/bundle.py`, `src/explain.py`, `src/storage.py`, `src/reports.py`, `src/ingest.py`, `src/analysis_input.py`,
`src/settings.py`, `src/service.py`, `app/api.py`, `app/streamlit_app.py`, scripts for the real runs.
See `docs/work-distribution.md` for owners.

## Safety rules for all code

No module may import network, process-launching or dynamic-execution tools, and no code may open URLs
or attachments found in emails.
