# Safety

**Owner: Member 3.** Phishing emails are dangerous content. This project analyses
them as **text only**.

## Rules the code follows

| Rule | How it is enforced |
|---|---|
| Never open, fetch or resolve a URL | no network modules are imported; `tests/test_safety.py` scans every source file and also runs the full analysis with the network disabled |
| Never run or open an attachment | attachments are only listed by name and type; risky extensions (for example `.exe`, `.js`, `.docm`) produce a warning |
| Never run commands or evaluate text as code | forbidden calls (`eval`, `exec`, `subprocess`, ...) are blocked by the same scan |
| Limit what can be uploaded | allowed types (`.eml`, `.csv`), 5 MiB maximum, 500 CSV rows maximum (`src/ingest.py`) |
| Do not keep sensitive data | the history stores a hash, never the email body or sender (`docs/storage-and-privacy.md`) |
| Block spreadsheet formula injection | CSV exports prefix `=`, `+`, `-`, `@` cells |
| Block SQL injection | all SQL uses placeholders |
| Never load untrusted model files | `joblib.load` can run code, so only model files created by `scripts/train.py` on this machine may be loaded |

## Handling datasets

- Keep raw data out of git.
- Do not open links found in the dataset. Do not paste real emails into public chats.
- Anonymize any example you put in a report (replace names and addresses).

## What the project does NOT do

- It does not detect malware or inspect attachment contents.
- It does not check sender authentication (SPF, DKIM, DMARC) because the dataset has no headers.
- It does not guarantee an email is safe. A low score is not a clearance.

## Checklist before a release

- [ ] `python -m pytest tests/test_safety.py` passes
- [ ] `git status` shows no `.env`, `.db`, `.joblib` or raw data
- [ ] `python scripts/check_pending.py` reports nothing unexplained
