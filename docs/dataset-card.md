# Dataset Card: Phishing Email Detection System

**Status: MeAJOR v2.0 selected on 2026-11-04 with documented limits; local statistics verified on the downloaded file (see sections 3 and 5).** See the [dataset selection decision](dataset-selection.md).

The system classifies emails as `phishing` or `legitimate`. For this dataset the two classes are MeAJOR's `0 = benign` and `1 = phishing`, and the "phishing" class is TREC spam/phishing mail (see section 3). Do not read results as general phishing detection.

## 1. Project purpose and intended use

- **Purpose:** develop a system that classifies email records as `phishing` or `legitimate`.
- **Intended use:** research, learning, and evaluation of phishing-email detection methods.
- **Not intended for:** making security decisions about real mailboxes without further validation, or identifying or profiling individuals.

## 2. Required schema and label definitions

Each email record uses the following fields:

| Field | Type | Requirement | Description |
|---|---|---|---|
| `subject` | String | Optional | Email subject text |
| `body` | String | Optional | Email body text |
| `sender` | String | Optional | Sender address or identifier |
| `label` | String | Required | Class label |

At least one of `subject` or `body` must contain usable text.

**Working label definitions — to be checked against the chosen dataset's own guidelines:**

- `phishing`: an email intended to deceive recipients, such as by soliciting credentials, personal data, money, or interaction with malicious content.
- `legitimate`: a genuine email without deceptive or malicious intent.

The preprocessing implementation normalizes supported label variants to `phishing` or `legitimate`. Accepted variants include `phish`, `phishing email`, `malicious`, `legit`, `ham`, `safe`, `safe email`, `benign`, and the integer labels `1` and `0`, respectively. Matching is case-insensitive and supports documented separator variations.

Unknown labels are rejected. In particular, `spam` is not automatically treated as phishing.

The final label mapping must be reviewed against the selected dataset's actual labelling scheme.

## 3. Dataset source and licensing

### Selected dataset: MeAJOR v2.0

- Official record: [Zenodo v2.0](https://zenodo.org/records/18471483); paper: [MeAJOR Corpus](https://arxiv.org/abs/2507.17978). Downloaded 2026-11-04 and kept only on local machines (`data/raw/`, git-ignored).
- Declared license: **CC BY 4.0** for the Zenodo deposit. This is the deposit-level declaration; it does not prove the depositors hold every right over all embedded emails, and no written clarification from the authors or upstream owners was obtained.
- Approved by the team lead on 2026-11-04 for this educational, non-commercial internship project only, with the limits in [dataset-selection.md](dataset-selection.md).
- The file has 20 columns. We use `subject`, `body` and `label`. Sender and receiver addresses are hashed in this dataset, so the `sender` column is not used and sender features have little signal.

### What the local file contains (verified from the downloaded file, 2026-11-04)

- Data rows read: **108,685** (matches the Zenodo record). Valid: **108,684**. Rejected: **1** (empty label).
- Labels are written `0.0` and `1.0` in the file; `configs/dataset.json` maps `0`/`0.0` to `legitimate` and `1`/`1.0` to `phishing`.
- The `source` column has only `trec5`, `trec6` and `trec7`. The Nazario and Nigerian Fraud sources named on the record and in the paper do **not** appear in this release.

| Source | Label 0 (benign) | Label 1 (phishing/spam) | Total |
|---|---|---|---|
| trec5 | 29,929 | 19,654 | 49,583 |
| trec6 | 11,208 | 3,797 | 15,005 |
| trec7 | 19,513 | 24,583 | 44,096 |
| (empty source and label) | | | 1 |
| **All** | 60,650 | 48,034 | 108,685 |

Both labels occur in every source, so the source alone does not give the label. Because the sources are TREC spam corpora, label 1 is the spam-labelled mail. The task learned here is spam/phishing versus ordinary mail from 2005 to 2007.

### Open items

| Item | Status |
|---|---|
| Written author confirmation of upstream source rights | Not obtained; accepted as a documented limit |
| Author explanation of how original labels became `benign`/`phishing` | Not found; label 1 is described as phishing/spam in all reports |
| Paper counts (220,932 raw, 135,894 cleaned) versus the release (108,685) | No public explanation found; we report what we loaded |
| Privacy review | No manual review of message text was done; addresses are hashed per the paper. Do not print or share message contents |
| Local row count, class distribution, duplicate rate | Done 2026-11-04 (`reports/dataset_audit.md`, `reports/dataset_sources.md`) |

## 4. Implemented preprocessing and data loading

### Individual-record preprocessing

Implemented in `src/preprocessing.py`:

- Validates the record structure and supported field types.
- Requires usable subject or body text.
- Normalizes whitespace.
- Normalizes recognized labels and rejects unknown labels.
- Reports invalid records through batch-processing results.

Punctuation and URLs are preserved as text. This implementation does not establish that HTML, invisible characters, or every dataset-specific encoding issue has been handled.

### Configurable CSV loading

Implemented in `src/dataset.py`:

- Validates dataset configuration.
- Supports configurable column mappings, delimiter, and encoding.
- Supports explicit raw-label mappings and an optional row limit.
- Checks CSV headers and row shape.
- Reports invalid records and loading errors.

The loader's existence does not mean that a real dataset has been selected, loaded, or approved.

## 5. Duplicate analysis and splitting

### Duplicate analysis

Implemented in `src/keys.py` and `src/quality.py`:

- Exact matching uses normalized subject/body content.
- Near matching applies more aggressive normalization, including URLs, email addresses, digits, and punctuation.
- Duplicate groups can be identified.
- Deduplication supports consistent-label records and reports conflicting-label groups rather than silently choosing a preferred label.

Near matching can group unrelated messages with similar templates. Its impact must be reviewed before relying on it for evaluation.

### Train/validation/test splitting

Implemented in `src/splitting.py`:

- Supports configurable training, validation, and test ratios.
- Supports a random seed and optional stratification.
- Keeps duplicate groups within a single partition.
- Checks for duplicate leakage across partitions.
- Reports conditions that prevent a safe split.

The default target ratios are 70% training, 15% validation, and 15% testing. Actual proportions can differ because duplicate groups are assigned together.

### Combined preparation workflow

Implemented in `src/data_prep.py` through `prepare_splits()`:

- Loads and preprocesses the configured dataset.
- Retains invalid-record errors for inspection.
- Reports duplicate groups.
- Produces train, validation, and test partitions.

The combined workflow removes duplicate records and label conflicts before splitting (`quality.deduplicate`), so no copy of the same email can cross partitions.

### Real-data results (2026-11-04, seed 42, near-duplicate level)

- Quality audit (`reports/dataset_audit.md`): exact duplicate groups 1,045 (4,155 records); near-duplicate groups 1,206 (5,244 records); groups with conflicting labels 0.
- Near-duplicate removal removed 5,244 records, leaving **103,440**.
- Split (`reports/split_summary.md`), leakage check passed:

| Split | Records | Phishing | Legitimate |
|---|---|---|---|
| train | 72,406 | 32,384 | 40,022 |
| validation | 15,517 | 6,940 | 8,577 |
| test | 15,517 | 6,940 | 8,577 |

The test split is reserved for the single final evaluation.

## 6. Privacy, safety, and limitations

- Email records may contain names, addresses, credentials, or other sensitive information. Review the chosen dataset's contents and licence before use.
- Do not commit raw personal or confidential email data.
- Do not include secrets or real personal emails in tests or documentation.
- Treat URLs as text only. Do not fetch or resolve links from phishing emails, and do not open untrusted attachments.
- The current record schema represents subject, body, sender, and label. It does not by itself represent all email headers, attachment contents, or the actual destination of a link.
- Class imbalance, source bias, noisy labels, duplicate contamination, and changes in phishing tactics are risks to investigate, not findings established by this card.
- Accuracy alone may be misleading if one class dominates. Evaluation should eventually report suitable class-sensitive metrics as well.

## 7. Model and evaluation status

A TF-IDF (1-2 grams) + Logistic Regression baseline was trained on the training split and evaluated on the **validation** split only (`reports/baseline_metrics.md`, 2026-11-04, seed 42):

| Metric | Value |
|---|---|
| Accuracy | 0.9783 |
| Precision | 0.9740 |
| Recall | 0.9775 |
| F1-score | 0.9758 |
| False-positive rate | 0.0211 |
| False-negative rate | 0.0225 |

Of 6,940 phishing validation emails, 156 were missed; of 8,577 legitimate ones, 181 were flagged.

These numbers describe this dataset only. They come from one run and one split, with no confidence interval. High scores are expected on TREC spam from 2005 to 2007 and do not show that the system detects current phishing. Model comparison and the final test-set evaluation are still to be run and recorded.

## 8. Maintenance

Update this card whenever the dataset is selected, inspected, or used for evaluation. Distinguish verified facts from assumptions and pending checks. Record the evidence supporting any newly completed item.