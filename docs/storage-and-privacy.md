# Storage and privacy

What the analysis history keeps. (Member 2)

## What is stored (table `analysis_history`)

| Column | Meaning |
|---|---|
| `id`, `created_at` | row number and UTC time |
| `source_name` | uploaded file name, or `pasted` / `api` |
| `content_sha256` | hash of the normalized email (identifies duplicates without keeping the text) |
| `subject_preview` | first 80 characters of the subject; **empty unless the caller asks for it** |
| `label`, `score`, `risk_level` | the result |
| `model_version` | which model produced it |
| `indicators_json`, `warnings_json` | the warning indicators and attachment warnings shown to the analyst |

## What is NOT stored

- The email body, sender address, headers or attachments.
- Any link target. Links are never opened.
- Credentials of any kind.

## Safe handling in code

- All SQL uses `?` placeholders; text is never pasted into queries (`tests/test_storage.py` checks an injection attempt).
- CSV exports prefix cells that start with `=`, `+`, `-` or `@` so spreadsheets cannot run them as formulas.
- The database file (`data/history.db`) is git-ignored and must never be committed.
- Open one database connection per request or thread.

## Retention

History is kept until `storage.clear_history` is called or the file is deleted. Delete it before sharing the project folder.
