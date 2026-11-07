# Baseline contribution files

Copy these files into the root of `Phishing-Email-Detection-System` while preserving the paths:

- `src/baseline_model.py`
- `src/run_baseline.py`
- `tests/test_baseline_model.py`
- `docs/baseline-model-metrics.md`

Add `pandas` and `scikit-learn` to the existing `requirements.txt` if not already present. Do not replace the team's existing `requirements.txt` with `requirements-baseline.txt`; it is only a dependency reminder.

The public repository README currently says a dataset and split utility are not yet committed. Therefore, the experiment must be run against the team's agreed dataset once its actual path and column names are known. The generated metrics are genuine only after that run.
