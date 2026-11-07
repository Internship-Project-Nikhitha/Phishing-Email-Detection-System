# Module interfaces (the team contract)

These are the public functions that exist on `main` and that other modules rely on.
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

## Functions on `main` (core)

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

## Modules added in the final weeks

| Module | Owner | Public interface |
|---|---|---|
| `src/features/sender.py` | Member 1 | `extract(record)`, `descriptions()` (sender address and display name features) |
| `src/features/urls.py` | Member 2 | `extract(record)`, `descriptions()` (link features; links are never opened) |
| `src/features/text.py` | Member 3 | `extract(record)`, `descriptions()` (wording, markup, formatting) |
| `src/features/pipeline.py` | Member 4 | `feature_names()`, `feature_descriptions()`, `extract_all(record)`, `extract_many(records)`, `check_pipeline()` |
| `src/vectorize.py` | Member 5 | `TextFeatures`, `EngineeredFeatures`, `FeatureBuilder` (scikit-learn transformers) |
| `src/models.py` | Member 5 | `available_models()`, `train_model(spec, train_records, seed, params, max_features)`, `tune_model(spec, train, validation, ...)`, `evaluate_model(model, records, threshold)`, `contributions(model, record)` |
| `src/bundle.py` | Member 5 | `ModelBundle`, `make_version`, `save_bundle(bundle, directory)`, `load_bundle(directory)` |
| `src/explain.py` | Member 1 | `validate_thresholds`, `risk_level(score, thresholds)`, `describe_feature`, `top_indicators`, `explain(...)` |
| `src/storage.py` | Member 2 | `connect(path)`, `init_db`, `save_analysis(...)`, `list_history`, `get_analysis`, `clear_history` |
| `src/reports.py` | Member 2 | `sanitize_csv_cell`, `analysis_to_json`, `analysis_to_markdown`, `history_to_csv` |
| `src/ingest.py` | Member 3 | `IngestError`, `validate_upload(filename, size)`, `parse_eml(data)`, `parse_csv_upload(data)`, `attachment_warnings(attachments)` |
| `src/analysis_input.py` | Member 3 | `prepare_for_analysis(record)` |
| `src/settings.py` | Member 4 | `Settings`, `SettingsError`, `load_settings(env)` |
| `src/service.py` | Member 4 | `Predictor` (protocol), `analyze_record(...)`, `analyze_and_store(...)`, `analyze_many(records, predictor)` |
| `src/benchmark.py` | Member 4 | `time_calls`, `measure_latency` |
| `src/split_report.py` | Member 4 | `summarize_split(splits)`, `write_split_ids(splits, path)`, `format_quality_markdown(audit, title, records)`, `count_removed(dedup)` |
| `app/api.py` | Member 4 | FastAPI app: `/health`, `/analyze`, `/history`, `/history.csv`, `/report/{id}` |
| `app/streamlit_app.py` | Member 5 | web interface (`streamlit run app/streamlit_app.py`) |
| `scripts/*.py` | see `docs/work-distribution.md` | `audit_dataset`, `make_splits`, `run_baseline`, `train`, `evaluate`, `feature_report`, `make_model_card` |

The test `tests/test_contract.py` fails if a listed function disappears or is renamed.

## Safety rules for all code

No module may import network, process-launching or dynamic-execution tools, and no code may open URLs
or attachments found in emails.
