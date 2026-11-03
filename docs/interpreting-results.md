# How to read the results

A guide to the metrics in `reports/`. (Member 5)

Phishing is the **positive** class.

| Term | Meaning |
|---|---|
| True positive (TP) | phishing correctly flagged |
| False positive (FP) | legitimate email wrongly flagged |
| True negative (TN) | legitimate email correctly passed |
| False negative (FN) | phishing email missed |

| Metric | Formula | Plain meaning |
|---|---|---|
| Precision | TP / (TP + FP) | when we flag an email, how often are we right? |
| Recall | TP / (TP + FN) | of all phishing emails, how many did we catch? |
| F1-score | harmonic mean of precision and recall | one number balancing both |
| False-positive rate | FP / (FP + TN) | share of legitimate emails wrongly flagged (analyst workload) |
| False-negative rate | FN / (FN + TP) | share of phishing emails missed (risk) |

## Reading tips

- **Accuracy alone can mislead** when one class is much bigger than the other.
- A high recall with a high false-positive rate means many false alarms for analysts.
- Validation metrics (`model_comparison.md`) were used to choose the model. Only `final_evaluation.md` (test split) is an unbiased estimate.
- Small test sets give noisy numbers. Look at the confusion counts, not just the percentages.
- The **risk score** is the model's probability that an email is phishing. The calibration table in `final_evaluation.md` shows whether higher scores really mean more phishing.
- Results describe the chosen dataset only. They do not promise the same performance on other email.
- Explanations show which features pushed the score. For linear and Naive Bayes models the direction is meaningful; for Random Forest only relevance is shown.

## Human review

The system ranks and explains. A person makes the final decision.
