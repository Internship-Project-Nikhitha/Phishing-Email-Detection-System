# Phishing Email Detection

A small research baseline for binary email-text classification. The project keeps source labels explicit, preserves useful indicators such as URLs and HTML, and reports data-quality checks without printing email contents.

## Setup

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Dataset

Read [the dataset research](docs/dataset-research.md), [candidate comparison](docs/dataset-candidates.md), and [dataset card](docs/dataset-card.md) first. No dataset, email sample, or trained artifact is included in this repository. MeAJOR v2.0 is a candidate for further review, **not approved for training yet**. Zenodo declares CC BY 4.0, but source-by-source rights and the meaning of `benign` remain unresolved. Its release record reports 108,685 rows; the paper abstract reports 135,894, and the difference is unexplained.

Do not download the corpus for training, map its labels, redistribute it, or make commercial-use claims until the MeAJOR authors clarify source rights, label mapping, and the count discrepancy, and your organization approves the intended use. The project does not download or include datasets.

After these issues are resolved and you are authorized to inspect the release, download `meajor_cleaned_preprocessed.csv` from the [Zenodo record](https://zenodo.org/records/18471483) into `data/`. Inspect only the header and aggregate labels first:

```powershell
python -c "import pandas as pd; print(pd.read_csv('data/meajor_cleaned_preprocessed.csv', nrows=0).columns.tolist())"
python -c "import pandas as pd; print(pd.read_csv('data/meajor_cleaned_preprocessed.csv', usecols=['label'])['label'].value_counts(dropna=False).to_dict())"
```

Counts show stored tokens, not their meanings or accuracy. The record defines `0 = benign`, `1 = phishing`, but the paper lists spam corpora among the sources and does not explain their label mapping. **Do not map `0` to this project's `legitimate` label or train until the authors confirm the class definition and the project accepts it.** See the author questions in [the dataset card](docs/dataset-card.md).

Once rights and label mapping are explicitly confirmed, validate the approved file locally without printing message text. Substitute exact source labels only after the author response and review:

```powershell
python -m src.data.validate_dataset data/meajor_cleaned_preprocessed.csv `
  --text-column "body" --label-column "label" `
  --phishing-label "<confirmed phishing value>" `
  --legitimate-label "<confirmed legitimate value>"
```

Only after the rights and label gates are cleared, use the same confirmed mapping for training:

```powershell
python -m src.train data/meajor_cleaned_preprocessed.csv `
  --text-column "body" --label-column "label" `
  --phishing-label "<confirmed phishing value>" `
  --legitimate-label "<confirmed legitimate value>" `
  --output artifacts/phishing_baseline.joblib
```

Do not assume `source` is a valid campaign/group field until its values and meaning are checked. A random stratified split does not establish independence across source, campaign, sender, or time.

## Check One Email

After training, classify one local UTF-8 text file without printing the email contents:

```powershell
python -m src.predict artifacts/phishing_baseline.joblib --text-file .\email.txt
```

Or pipe text from a local source through stdin:

```powershell
Get-Content -Raw .\email.txt | python -m src.predict artifacts/phishing_baseline.joblib
```

The command prints only `phishing` or `legitimate` (plus a joblib trust warning on stderr). Input remains local; the command does not open URLs or execute attachments. Do not load model artifacts from untrusted sources: joblib deserialization can execute code. This baseline prediction is not a guarantee that an email is safe.

The loader accepts CSV, JSON, and JSONL, and requires explicit source-label mappings. Invalid-row reports contain source row numbers and reasons only. The audit reports empty rows, labels, duplicates, imbalance, exact split contamination, group overlap (when a group column is supplied), and counts of email addresses, URLs, IPv4 strings, phone-like strings, and HTML. These checks are indicators, not guarantees of privacy, representativeness, or leakage-free evaluation.

Run tests with:

```powershell
python -m pytest -q
```

The scikit-learn TF-IDF/logistic-regression pipeline is a baseline, not a production phishing detector. Only load model artifacts that you created or otherwise trust; joblib/pickle-based formats can execute code when deserialized.