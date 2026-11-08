# Presentation outline

**Owner: Team lead.** One speaker per section; every member explains their own part.

| # | Slide | Speaker | Evidence (file) |
|---|---|---|---|
| 1 | Problem and goal | Lead | `README.md` |
| 2 | Dataset, license, limits | Member 1 | `docs/dataset-card.md` |
| 3 | Loading and quality (duplicates, conflicts) | Members 2 and 3 | `reports/dataset_audit.md` |
| 4 | Leakage-safe split | Member 4 | `docs/split-strategy.md` |
| 5 | Baseline and metrics | Member 5 | `reports/baseline_metrics.md` |
| 6 | Features (sender, URL, text) | Members 1, 2, 3 | `docs/features.md` |
| 7 | Model comparison and choice | Member 5 | `reports/model_comparison.md`, `docs/model-card.md` |
| 8 | Explanations and risk levels | Member 1 | `src/explain.py` |
| 9 | App and API demo | Members 4 and 5 | `docs/api.md`, `docs/setup-guide.md` |
| 10 | Safety and privacy | Members 3 and 2 | `docs/safety.md`, `docs/storage-and-privacy.md` |
| 11 | Final results and errors | Member 5 | `reports/final_evaluation.md`, `docs/limitations.md` |
| 12 | Team workflow and commit history | Lead | `docs/work-distribution.md` |

## Demo plan (3 minutes)

1. Paste `samples/phishing_sample.eml` text, show score, level and indicators.
2. Upload `samples/suspicious_attachment_sample.eml`, show the attachment warning.
3. Upload `samples/sample_batch.csv`, export history, open a Markdown report.

## Questions to prepare

- Why was the test split untouched until the end?
- What does a false positive cost versus a false negative?
- How do we know there is no leakage?
- What would you improve first?
