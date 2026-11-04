# Setup guide

**Owner: Member 5.** Tested on Python 3.11 or newer.

## 1. Install

```
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Get the dataset

Follow `docs/dataset-selection.md`, then copy `configs/dataset.example.json` to
`configs/dataset.json` and edit it. Check that it loads:

```
python scripts/audit_dataset.py
```

## 3. Build the data products and train

```
python scripts/make_splits.py        # reports/split_summary.md
python scripts/run_baseline.py       # reports/baseline_metrics.md
python scripts/train.py              # models/latest/, reports/model_comparison.md
python scripts/make_model_card.py    # docs/model-card.md
```

## 4. Final evaluation (run once, on the test split)

```
python scripts/evaluate.py           # reports/final_evaluation.md
```

## 5. Run the apps

```
uvicorn app.api:app --reload                 # API on http://127.0.0.1:8000/docs
streamlit run app/streamlit_app.py           # web interface
```

Copy `.env.example` to `.env` to change paths or risk thresholds.

## 6. Tests

```
python -m pytest
```

## Troubleshooting

| Problem | Likely cause |
|---|---|
| "No model found" | run `scripts/train.py` first |
| "dataset file not found" | the `path` in `configs/dataset.json` does not match your downloaded file |
| Most rows rejected | check `columns` and `label_map` in the config; `audit_dataset.py` shows the reasons |
| `ModuleNotFoundError: fastapi` | `pip install -r requirements.txt` |
