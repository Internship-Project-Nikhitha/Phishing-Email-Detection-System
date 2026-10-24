# Phishing Email Detection System

A Python-based cybersecurity internship project that builds the foundations for detecting phishing emails. The project currently supports email-record validation, configurable CSV dataset loading, duplicate analysis, and leakage-aware train/validation/test splitting.

The project is under active development. A verified real-world dataset and a trained, evaluated baseline classifier are not yet documented as completed.

## Current implementation status

| Component | Status |
|---|---|
| Email-record validation and preprocessing | Implemented |
| Label normalization and batch error reporting | Implemented |
| JSON dataset configuration validation | Implemented |
| Configurable CSV dataset loading | Implemented |
| Exact and near-duplicate identification | Implemented |
| Duplicate removal with conflict reporting | Implemented |
| Train/validation/test splitting with duplicate-group protection | Implemented |
| Combined dataset preparation workflow | Implemented |
| Verified dataset selection and licence review | Pending |
| Baseline machine-learning model and real-data evaluation | Pending |

Implementation status describes available code, not proof that a complete end-to-end experiment has been performed.

## Features

### 1. Email preprocessing

`src/preprocessing.py` provides record validation and preprocessing.

- Supports `subject`, `body`, `sender`, and `label` fields.
- Requires a supported label and usable subject or body text.
- Normalizes accepted label variants to `phishing` or `legitimate`.
- Normalizes whitespace while preserving punctuation and URLs.
- Reports invalid records through batch-processing results.

Unknown labels are rejected rather than guessed. In particular, `spam` is not automatically treated as `phishing`.

### 2. Dataset configuration and loading

`src/dataset.py` provides:

- JSON configuration parsing and validation.
- Configurable CSV column mappings.
- Configurable delimiter and text encoding.
- Optional raw-label mappings.
- Optional maximum row limits.
- CSV header and row-shape checks.
- Clear errors for invalid configuration and unreadable or malformed input.
- Integration with the preprocessing pipeline.

Dataset configuration supports `path`, `columns`, `label_map`, `delimiter`, `encoding`, and `max_rows`.

A configuration must map the required `label` field and at least one of `subject` or `body`.

### 3. Duplicate analysis and deduplication

`src/keys.py` generates deterministic SHA-256-based identifiers for email content.

- **Exact matching:** ignores case and whitespace differences in subject and body.
- **Near matching:** additionally normalizes URLs, email addresses, digits, and punctuation to identify template-like messages.

`src/quality.py` groups duplicate records and provides deduplication with an audit trail. Duplicate records with consistent labels retain the first occurrence. Groups with conflicting labels are excluded rather than silently assigned a preferred label.

Near-duplicate matching is more aggressive and may group unrelated messages with similar templates. Review its impact before using it for an experiment.

### 4. Train/validation/test splitting

`src/splitting.py` provides reproducible splitting into training, validation, and test partitions.

- Configurable split ratios.
- A configurable random seed.
- Optional class-stratification behavior.
- Exact- or near-duplicate grouping.
- Assignment of each duplicate group to a single partition.
- Checks for duplicate leakage across partitions.

The default split ratios are 70% training, 15% validation, and 15% testing. These are targets; duplicate groups can cause the final proportions to differ.

Small datasets or large duplicate groups may prevent every partition from being populated. Rare classes may also be absent from individual partitions, which can make class-specific evaluation unreliable.

### 5. Combined preparation workflow

`src/data_prep.py` connects dataset loading, duplicate-group analysis, and splitting through `prepare_splits()`.

The returned `PreparedData` object contains:

- Valid preprocessed records.
- Errors from invalid records.
- Duplicate-group information.
- Train, validation, and test partitions.
- Counts and split-size summaries.

This workflow reports duplicate groups and protects the splits from duplicate leakage. It does not automatically remove duplicate records before splitting.

## Expected email record format

A record is represented as a Python dictionary.

| Field | Requirement | Description |
|---|---|---|
| `subject` | Optional | Email subject |
| `body` | Optional | Email body |
| `sender` | Optional | Sender address or identifier |
| `label` | Required | Class label |

At least one of `subject` or `body` must contain usable text after preprocessing.

Supported labels are normalized to:

- `phishing`
- `legitimate`

The precise accepted label variants are defined by `src/preprocessing.py`. A dataset with different labels may require an explicitly reviewed `label_map`.

## Dataset selection and provenance

The project must use a dataset whose source, licence, permitted use, schema, and labeling methodology have been checked.

The [dataset card](docs/dataset-card.md) records the current candidate and unresolved checks. See the [dataset research](docs/dataset-research.md) and [candidate comparison](docs/dataset-candidates.md) before selecting or using a corpus. Complete pending verification before reporting dataset statistics or model performance.

Do not invent dataset sizes, class distributions, provenance, or evaluation results.

## Setup

Prerequisites:

- Python 3.11 or newer.
- `pip`.

From the repository root, create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

On Linux or macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Run the tests

From the repository root:

```bash
python -m pytest -q
```

For verbose test output:

```bash
python -m pytest -v
```

Run the complete test suite after making changes. The passing test count should be taken from the actual test run, not copied from an earlier run.

## Example: preprocess an email

```python
from src.preprocessing import preprocess_email

record = preprocess_email({
    "subject": "  Verify   your account ",
    "body": "Visit http://example.invalid/verify",
    "label": "Phish",
})

print(record)
```

Expected normalized record:

```python
{
    "subject": "Verify your account",
    "body": "Visit http://example.invalid/verify",
    "sender": "",
    "label": "phishing",
}
```

This example uses a reserved example domain and does not access the URL.

## Project structure

```text
README.md
requirements.txt
src/
    __init__.py
    preprocessing.py
    dataset.py
    keys.py
    quality.py
    splitting.py
    data_prep.py
tests/
    test_preprocessing.py
    test_dataset.py
    test_keys.py
    test_quality.py
    test_splitting.py
    test_data_prep.py
docs/
    dataset-card.md
```

## Data safety and limitations

- URLs in email records are handled as text; the project must not fetch or resolve them.
- Do not click links or open attachments contained in suspicious emails.
- Do not commit credentials, secrets, private mailbox exports, or unredacted personal information.
- Verify dataset licence and privacy restrictions before downloading, using, or redistributing data.
- Exact and near-duplicate matching are content-based heuristics, not proof that two messages belong to the same campaign.
- The current implementation does not establish real-world detection accuracy.
- A trained and evaluated baseline classifier, its metrics, and any production-facing interface must be documented only after they are implemented and verified.

## Development workflow

1. Work on the assigned branch.
2. Fetch and integrate the latest `origin/main` before starting work.
3. Inspect existing files before editing.
4. Add focused tests for behavior changes.
5. Run `python -m pytest -q` and `git diff --check`.
6. Review the diff before committing.
7. Push work to the assigned branch and use the agreed review process for integration.

Do not backdate commits or report unverified work as completed.