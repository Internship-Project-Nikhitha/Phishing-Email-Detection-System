# Sender features: manual review

**Owner: Member 1.** The features are defined in `src/features/sender.py`. Fill this
after running `python scripts/feature_report.py` on the real dataset.

## Feature list

List each feature name from `python -c "from src.features import sender; print(sender.descriptions())"`
and note what it means and why it might indicate phishing.

| Feature | What it measures | Why it might matter | Possible false alarm |
|---|---|---|---|
| <FILL> | <FILL> | <FILL> | <FILL> |

## Check against real emails

Look at 10 real emails of each class (read the text only; do not click anything).

- Features that looked right: <FILL>
- Features that fired on the wrong emails (with a short, anonymized example): <FILL>
- Features that are always 0 or always 1 on this dataset: <FILL>

## Limits

Sender text can be forged. A sender-based feature is a hint, not proof. <FILL anything dataset-specific>
