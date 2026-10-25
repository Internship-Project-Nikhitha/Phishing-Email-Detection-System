# Dataset selection

**Owner: Member 1.**

**Decision date:** 2026-10-24
**Status:** **No dataset selected; approval is blocked pending rights and label verification.**

No reviewed candidate currently satisfies both the project's phishing-versus-legitimate label requirements and a substantiated permission basis for every underlying email. Do not create `configs/dataset.json`, download data, train, or redistribute a candidate based on this document.

## Chosen dataset

- **Name:** None selected.
- **Source URL:** Not applicable; no candidate approved.
- **License:** Not applicable to a project selection. Candidate-specific declarations and gaps are recorded in [dataset-candidates.md](dataset-candidates.md).
- **Download date:** None; no dataset downloaded for this review.
- **File name to save as:** None. Do not place or commit dataset files.

## Why no candidate is selected

MeAJOR v2.0 is the leading research candidate, but its Zenodo CC BY 4.0 declaration does not establish rights for every message from its upstream sources; the source-label mapping for `benign` is undocumented, and the paper and release sample counts differ without a public explanation. The nine-corpus Phishing-Email-Detection-Dataset also declares CC BY 4.0 at the Zenodo deposit level, but groups spam, scam, and phishing together and does not settle source-by-source rights. The 2,000-email validation dataset has clear `Safe Email` and `Phishing Email` labels and a Zenodo CC BY 4.0 declaration, but the record says it includes synthetic data and is intended for post-training validation; permissions for underlying real-world emails and its suitability as training data are not independently established. The Cyber Cop Kaggle page declares LGPL 3.0, but does not document exact label definitions, provenance, or the uploader's rights to the email contents. Therefore none is yet a defensible approved training choice.

All four source landing pages or metadata records were publicly viewable during this review, but actual file downloads and any platform sign-in requirements were not tested; download access for the underlying corpora remains **UNVERIFIED**. Public access to a metadata page is not evidence of permission to use its email records.

**Lead approval:** Pending. Reconsider a selection only after written author/upstream rights clarification, acceptance of the exact label definitions, and project review. This is a research due-diligence status, not legal advice.

## Mapping to our schema

No candidate has been approved, so no values should be copied into `configs/dataset.json`.

| Our field | Dataset column |
|---|---|
| subject | Not selected |
| body | Not selected |
| sender | Not selected |
| label | Not selected |

| Dataset label text | Our label |
|---|---|
| Not selected | phishing |
| Not selected | legitimate |

Do not map `benign`, `safe`, `spam`, or numeric labels to `legitimate` or `phishing` without verified source definitions and explicit project approval.

## How a teammate obtains data

1. **Do not download a dataset yet.** First obtain written source-by-source rights and label clarification and get project approval.
2. If a dataset is later approved, update this document with its exact official record, release/version, license/terms, retrieval date, and verified schema before sharing download instructions.
3. Never commit raw email data. Keep approved files local and verify they remain excluded by `.gitignore`.

## Configuration and pending-marker checks

No source dataset is approved, so `configs/dataset.example.json` is a schema example only. Its path is deliberately `<PENDING_DATASET_APPROVAL>`, and its empty `label_map` does not guess source-label meanings. Do not copy it to `configs/dataset.json` or use it to load data until a dataset, its exact columns, label meanings, and usage rights are approved.

Run the scoped checker from the repository root:

```powershell
python scripts/check_pending.py
```

It checks only this dataset card, candidate review, selection decision, and example config. `PENDING`, `UNVERIFIED`, `TODO`, and `<FILL ...>` occurrences are printed with file and line numbers. These findings are informational and return exit status 0 because the current blockers are documented intentionally. Missing or unreadable configured files return exit status 2 so an incomplete scan cannot look successful.

## Risks and limitations

- Current sources do not establish source-by-source rights for all emails in the multi-source candidates.
- `benign`, spam, scam, and safe are not interchangeable class definitions; label mapping requires evidence.
- MeAJOR's paper and Zenodo v2.0 sample counts remain unreconciled.
- Some candidates mix real-world and synthetic emails, or are intended for validation rather than training.
- Email data can contain personal information, malicious URLs, and other sensitive content. Do not open embedded links or attachments, print message contents, or use external services to inspect emails.
- Public license metadata does not, by itself, verify the depositor's authority over third-party email content or resolve privacy and other rights.

## Validation commands

Run from the repository root:

```powershell
.\.venv312\Scripts\python.exe -m pytest -q
python scripts/check_pending.py
git diff --check
```

These checks validate project tests and patch formatting; they do not provide dataset licensing or legal clearance.
