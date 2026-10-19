# Phishing Email Detection

A small research baseline for binary email-text classification. The project keeps source labels explicit, preserves useful indicators such as URLs and HTML, and reports data-quality checks without printing email contents.

## Setup

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Dataset

Read [the dataset research](docs/dataset-research.md) and [the dataset card](docs/dataset-card.md) before downloading or using any corpus. No dataset, email sample, or trained artifact is included in this repository. The current candidate is the Kaggle `Phishing Email Detection` dataset mirrored on Hugging Face. Its mirror advertises LGPL-3.0, but rights in the source email content and original collection lineage have not been independently established. Do not redistribute the data unless you have confirmed the applicable rights.

Download the CSV from [the Hugging Face repository](https://huggingface.co/datasets/zefang-liu/phishing-email-dataset/tree/main) or Kaggle and place it at `data/Phishing_Email.csv`. The Kaggle download may require an account. Confirm the CSV's label values locally before choosing mappings; the inspection below prints only labels and counts, never email text:

```powershell
python -c "import pandas as pd; print(pd.read_csv('data/Phishing_Email.csv', usecols=['Email Type'])['Email Type'].value_counts(dropna=False).to_dict())"
```

## Validate and Train

Use the exact source label strings observed above. The Kaggle description defines the concepts as Phishing and Safe, but exact stored values must be verified against the downloaded file:

```powershell
python -m src.data.validate_dataset data/Phishing_Email.csv `
  --text-column "Email Text" --label-column "Email Type" `
  --phishing-label "<exact phishing label>" `
  --legitimate-label "<exact safe label>"

python -m src.train data/Phishing_Email.csv `
  --text-column "Email Text" --label-column "Email Type" `
  --phishing-label "<exact phishing label>" `
  --legitimate-label "<exact safe label>" `
  --output artifacts/phishing_baseline.joblib
```

Replace the angle-bracketed arguments with the exact values shown by the label inspection. If records have a documented source or campaign field, supply it as `--group-column <column>` to hold groups out of the test set. The default random stratified split does not establish independence across source, campaign, sender, or time.

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