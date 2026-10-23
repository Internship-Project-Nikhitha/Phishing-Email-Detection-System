# Phishing Email Detection

A small research baseline for binary email-text classification. The project keeps source labels explicit, preserves useful indicators such as URLs and HTML, and reports data-quality checks without printing email contents.

## Setup

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Dataset

Read [the dataset research](docs/dataset-research.md), [candidate comparison](docs/dataset-candidates.md), and [dataset card](docs/dataset-card.md) before downloading or using any corpus. No dataset, email sample, or trained artifact is included in this repository. The recommended leading candidate is MeAJOR v2.0 on Zenodo. Its record declares CC BY 4.0 and documents `0 = benign`, `1 = phishing`; review upstream corpus terms and confirm that `benign` is an acceptable definition for this project's `legitimate` class before training, commercial use, or redistribution. The project also reviewed a separately supplied Cyber Cop Kaggle CSV; it is not recommended for training as-is because validation found many exact-text label conflicts and its email-content rights are unresolved.

Download `meajor_cleaned_preprocessed.csv` from the [official Zenodo record](https://zenodo.org/records/18471483) and place it at `data/meajor_cleaned_preprocessed.csv`. Do not commit the dataset. First inspect the header without reading message contents:

```powershell
python -c "import pandas as pd; print(pd.read_csv('data/meajor_cleaned_preprocessed.csv', nrows=0).columns.tolist())"
```

## Validate and Train

Inspect the stored label values and counts without printing email text:

```powershell
python -c "import pandas as pd; print(pd.read_csv('data/meajor_cleaned_preprocessed.csv', usecols=['label'])['label'].value_counts(dropna=False).to_dict())"
```

Zenodo defines `1` as phishing and `0` as benign. Counts show stored values, not their correctness. The source does not prove that benign means legitimate rather than any non-phishing email (potentially including spam). Continue only after accepting that limitation and reviewing source terms. If accepted, validate and train using the explicit source mappings:

```powershell
python -m src.data.validate_dataset data/meajor_cleaned_preprocessed.csv `
  --text-column "body" --label-column "label" `
  --phishing-label "1" `
  --legitimate-label "0"

python -m src.train data/meajor_cleaned_preprocessed.csv `
  --text-column "body" --label-column "label" `
  --phishing-label "1" `
  --legitimate-label "0" `
  --output artifacts/phishing_baseline.joblib
```

The `source` field is present in the CSV header, but inspect its values and confirm its meaning before using `--group-column source`. A group split can reduce known source overlap, but the default random stratified split does not establish independence across source, campaign, sender, or time.

### If you were given `Phishing_Email.csv` instead

Do not replace the repository with the ZIP contents. Extract only `Phishing_Email.csv` into `data\Phishing_Email.csv`; the `data\` folder is ignored by Git, so the email file will not be committed. The local copy reviewed for this project had columns `Email Text` and `Email Type` (plus an undocumented blank/index-like column) and labels `Safe Email` and `Phishing Email`. Kaggle declares LGPL-3.0, but rights to the original email contents and the uploader's authority are not established. The project validator also found 533 exact-text duplicates with conflicting labels. Do not train on this copy until the label conflicts and applicable rights have been reviewed. Full results are in [the dataset card](docs/dataset-card.md).

If you are authorized to inspect the local file, the following command reports aggregate validation results only; it does not print email bodies:

```powershell
python -m src.data.validate_dataset data/Phishing_Email.csv `
  --text-column "Email Text" --label-column "Email Type" `
  --phishing-label "Phishing Email" `
  --legitimate-label "Safe Email"
```

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