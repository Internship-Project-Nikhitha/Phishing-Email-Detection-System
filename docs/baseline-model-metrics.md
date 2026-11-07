# Baseline Model & Metrics

## Contribution
This contribution adds a reproducible TF-IDF + Logistic Regression baseline and held-out evaluation outputs.

## Repository integration note
The repository README currently documents preprocessing only; it says the dataset, dataset loader, and train/validation/test split have not yet been added. This implementation therefore provides a reproducible stratified holdout split inside the baseline runner. If the team has a shared splitting utility in an unmerged branch, replace the `train_test_split` call with that utility before merging.

## Model
- Text features: subject + body (or one configured text column)
- Vectorizer: TF-IDF, unigrams and bigrams, maximum 50,000 features
- Classifier: Logistic Regression, `max_iter=1000`, `class_weight='balanced'`
- Split: stratified 80/20 holdout by default, seed 42
- Positive class: phishing (`1`); legitimate is `0`
- Leakage prevention: vectorizer is inside an sklearn Pipeline and is fitted only on training text
- Sender field is not included in the text features

## Run
Install dependencies from the repository root:

```bash
python -m pip install pandas scikit-learn
```

For a dataset with `subject`, `body`, and `label` columns:

```bash
python -m src.run_baseline --data path/to/agreed_dataset.csv
```

For a dataset with a single text column named `email_text`:

```bash
python -m src.run_baseline --data path/to/agreed_dataset.csv --text-col email_text
```

If the dataset uses different column names, pass `--subject-col`, `--body-col`, and `--label-col` as needed. The runner accepts the label variants already documented in the project preprocessing contract. Other labels must be mapped explicitly rather than guessed.

## Generated artifacts
The run writes these files under `outputs/baseline/`:
- `metrics.json`: run configuration, metrics, and confusion-matrix counts
- `summary_metrics.csv`: accuracy, precision, recall, F1, false-positive rate
- `confusion_matrix.csv`: TN/FP/FN/TP matrix
- `classification_report.csv`: per-class precision, recall, F1, and support

## Metric definitions
For phishing as the positive class:
- Precision = TP / (TP + FP)
- Recall = TP / (TP + FN)
- F1 = harmonic mean of precision and recall
- False-positive rate = FP / (FP + TN)

Confusion matrix layout is `[[TN, FP], [FN, TP]]`, with rows = actual class and columns = predicted class. FPR is saved as `null` only if there are no legitimate examples in the test set, because its denominator would be zero.

## Results policy
No performance figures are hard-coded in this contribution. Run the script on the team's agreed dataset and report the values written by that run. Do not copy scores from another repository or report sample/test-fixture metrics as project results. The dataset and generated outputs may be excluded from Git if they are large or contain sensitive email content.
