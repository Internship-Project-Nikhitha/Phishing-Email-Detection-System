# Member 4 handover: what I own and how to check it

This page lists the parts of the project that Member 4 built, where their tests are and how to
re-check them in a few minutes. It only describes what is in the repository; the results of the
real-data runs are in `reports/` and are explained in `docs/interpreting-results.md`.

## What Member 4 owns

| Part | File | Key functions | Tests |
|---|---|---|---|
| Leakage-safe splitting | `src/splitting.py` | `split_dataset`, `audit_split_leakage`, `assert_no_duplicate_leakage`, `fingerprint_split` | `tests/test_splitting.py` |
| Split report | `src/split_report.py` | `summarize_split`, `write_split_ids` | `tests/test_split_report.py` |
| Split script | `scripts/make_splits.py` | - | `tests/test_make_splits_script.py` |
| Feature pipeline | `src/features/pipeline.py` | `feature_names`, `feature_descriptions`, `extract_all`, `extract_many`, `check_pipeline` | `tests/test_features_pipeline.py` |
| Settings | `src/settings.py` | `load_settings` | `tests/test_settings.py` |
| Analysis service | `src/service.py` | `analyze_record`, `analyze_and_store`, `analyze_many` | `tests/test_service.py` |
| Benchmark helpers | `src/benchmark.py` | `time_calls`, `measure_latency` | `tests/test_benchmark.py` |
| REST API | `app/api.py` | `analyze`, `analyze_upload`, `history`, `history_csv`, `report` | `tests/test_api.py` |
| API reference | `docs/api.md` | - | `tests/test_docs_links.py` |

## How the pieces fit

```
email (JSON / .eml / .csv)
   -> src/ingest.py            safe parsing, size and type checks
   -> src/analysis_input.py    clean the text, no label needed
   -> src/features/pipeline.py hand-built features (text only, no network)
   -> model score + contributions
   -> src/explain.py           risk level, label, top indicators
   -> src/storage.py           history keeps a hash and the result, not the email text
```

`src/service.py` runs this chain and `app/api.py` exposes it. Links are never opened and
attachments are never executed (`docs/safety.md`).

## Re-check in five minutes

From the project root, in an activated virtual environment:

```
python -m pip install -r requirements.txt
python -m pytest -q
python -m pytest -q tests/test_service.py tests/test_api.py tests/test_settings.py tests/test_splitting.py
```

Expected: every test passes. `tests/test_api.py` is skipped only when `fastapi` or `httpx` is not installed.

## Decisions worth knowing

- The decision threshold (`DECISION_THRESHOLD`, default 0.5) only sets the label. Risk levels use `RISK_MEDIUM` and `RISK_HIGH` (defaults 0.4 and 0.7). All three come from `.env.example`.
- A bad email in a CSV upload is reported in `errors` with its row index and does not stop the other rows.
- Splitting keeps exact duplicates together. `near` mode is stricter and is not the default.
- The history stores a SHA-256 of the cleaned email, never the text (`docs/storage-and-privacy.md`).

## Added in the daily tasks (15 to 20 November)

These are extra checks added on top of the finished project; each is one file and does not change `src/` or `app/`.

| Day | File | What it protects |
|---|---|---|
| 15 Nov | `tests/test_api_contract.py` | paging, error codes, missing model, privacy of the stored history |
| 16 Nov | `tests/test_config_docs_consistency.py` | `.env.example` and `docs/api.md` match the code |
| 17 Nov | `tests/test_service_contract.py` | result fields, thresholds, warnings, batch indices |
| 18 Nov | `tests/test_feature_reference.py` | generated `docs/feature-reference.md` and the feature pipeline contract |
| 19 Nov | `tests/test_split_invariants.py` | no leakage and stable sizes for many seeds |
| 20 Nov | `tests/test_member4_handover.py` | this page names only files and functions that exist |

## Known limits

- The risk thresholds are fixed numbers, not calibrated on the real data (see `docs/limitations.md`).
- Registered-domain matching in the URL features uses the last two labels and has no public-suffix list.
