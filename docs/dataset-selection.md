# Dataset selection

**Owner: Member 1 (research). Decision: team lead.**

**Decision date:** 2026-11-04
**Status:** **Selected, with a warning: the "phishing" class is TREC spam/phishing (see "What the download check found").**

## Chosen dataset

- **Name:** MeAJOR (Merged email Assets from Joint Open-source Repositories), version 2.0
- **Source URL:** https://zenodo.org/records/18471483 (paper: https://arxiv.org/abs/2507.17978)
- **Declared license:** CC BY 4.0 (the Zenodo record's own declaration)
- **File to download:** the CSV file on the Zenodo record (191,121,228 bytes, MD5 `aa8f59e96787cbd696c0b650e5400dc9` as recorded in `dataset-candidates.md`)
- **Save it as:** `data/raw/meajor_v2.csv` (this folder is git-ignored; never commit the file)
- **Download date:** 2026-11-04
- **Local verification:** re-downloaded from the official Zenodo file URL on 2026-11-07; verified size 191,121,228 bytes and MD5 `aa8f59e96787cbd696c0b650e5400dc9`.

## Why this one

It is the only reviewed candidate that is large (108,685 records), has a documented binary label (`0 = benign`, `1 = phishing`), has a separate `subject` and `body` column, and is published for phishing-detection research. The other candidates are smaller, validation-only, or merge spam and scam into the positive class without a documented mapping.

## Approval and limits

Approved by the team lead on 2026-11-04 **for use in this educational, non-commercial internship project only**, with these conditions:

- Keep the data on local machines only. Do not redistribute it and do not commit it.
- Written clarification from the dataset authors and upstream corpus owners was **not** obtained. The CC BY 4.0 declaration is on the Zenodo deposit; it does not prove the depositors' rights over every email. This is a project decision, not legal advice.
- Reports and the presentation must call the classes **"benign" and "phishing/spam (MeAJOR label 1)"**. The v2.0 release contains only TREC 2005, 2006 and 2007 emails, so label 1 is the TREC spam-labelled mail. It is not a collection of verified phishing emails. Do not claim that results measure phishing detection in general.
- The emails come from the TREC 2005 to 2007 spam corpora. Results do not promise the same performance on current email.
- Sender and receiver addresses in MeAJOR are hashed, so the `sender` column is **not** mapped. The sender features are all zero on this dataset; see [limitations](limitations.md).
- The paper reports 135,894 emails after cleaning; the Zenodo release has 108,685. No public explanation was found. We use the Zenodo release as published and report what we actually loaded.

## What the download check found (2026-11-04)

- Rows read: **108,685**, matching the Zenodo record.
- The `source` column has only `trec5`, `trec6` and `trec7`. Nazario and Nigerian Fraud, listed in the paper, are not in this release.
- Labels are written `0.0` and `1.0` (not `0` and `1`). `configs/dataset.json` maps both forms.
- Rows per source and label (from `scripts/dataset_crosstab.py`):

| source | label 0 (benign) | label 1 (phishing/spam) | total |
|---|---|---|---|
| trec5 | 29,929 | 19,654 | 49,583 |
| trec6 | 11,208 | 3,797 | 15,005 |
| trec7 | 19,513 | 24,583 | 44,096 |
| empty source and label | | | 1 (rejected) |
| **all** | 60,650 | 48,034 | 108,685 |

- Both labels occur in every source, so a model cannot get the label just from the source. The risk is different: label 1 is spam, so the system learns spam versus ordinary mail from 2005 to 2007.

## Post-download checks

1. **Shape.** `python scripts/audit_dataset.py --config configs/dataset.json --out reports/dataset_audit.md` runs without error, and the number of rows read is close to 108,685. Write the real number in this document.
2. **Source versus label.** `python scripts/dataset_crosstab.py --config configs/dataset.json --source-column source --out reports/dataset_sources.md` shows how many rows of each source carry each label. Copy the table into `docs/dataset-card.md`.
   - If one class comes entirely from one source (for example all `0` from TREC and all `1` from Nazario), models can learn the source rather than phishing. Then the report must say so and must not claim the accuracy generalises.
   - If TREC rows carry label `1`, the phishing class includes spam. Say so in the report.
3. **Labels.** The only raw label values are `0` and `1`. Anything else is listed under "Rejected rows" in the audit and must be explained.

Result of the checks (2026-11-04): shape and sources checked as above; raw labels `0.0`/`1.0` mapped in the config; the exact audit numbers are in `reports/dataset_audit.md` after the corrected config is run.

## Mapping to our schema

| Our field | Dataset column |
|---|---|
| subject | `subject` |
| body | `body` |
| sender | not mapped (hashed in this dataset) |
| label | `label` |

| Dataset label text | Our label |
|---|---|
| `0` or `0.0` | legitimate |
| `1` or `1.0` | phishing |

This mapping is in `configs/dataset.json`. `max_rows` is left empty on purpose: the file may be ordered by source, so taking only the first rows could drop a whole class.

## How a teammate obtains data

1. Open https://zenodo.org/records/18471483 and download the CSV file.
2. Save it as `data/raw/meajor_v2.csv` in your project folder.
3. Check that `git status` does not list it (it must be ignored).
4. Run `python scripts/audit_dataset.py --config configs/dataset.json --out reports/dataset_audit.md` and read the counts.
5. Never open links or attachments found in the emails, never print message contents, and never use external services to inspect emails.

## Checks

```powershell
python scripts/check_pending.py
python -m src.audit_dataset configs/dataset.json
python -m pytest -q
```

These validate the project's code and configuration; they are not legal clearance.
