# API reference

**Owner: Member 4.** The FastAPI service is in `app/api.py`.

Run it (after training a model, see `docs/setup-guide.md`):

```
uvicorn app.api:app --reload
```

Interactive docs: `http://127.0.0.1:8000/docs`

| Method and path | Purpose | Notes |
|---|---|---|
| `GET /health` | service is running | returns `{"status": "ok"}` |
| `POST /analyze` | analyse one pasted email | JSON body: `subject`, `body`, `sender` (all optional text, at least subject or body required) |
| `POST /analyze/upload` | analyse an uploaded `.eml` or `.csv` | `.eml` gives one result; `.csv` gives one result per valid row (max 500) and lists row errors |
| `GET /history` | list saved analyses | newest first |
| `GET /history.csv` | export history | formula-safe CSV |
| `GET /report/{id}` | report for one analysis | `?format=md` (default) or `?format=json`; 404 if the id does not exist |

## Result fields

`label` (phishing / legitimate), `score` (0 to 1), `risk_level` (low / medium / high),
`indicators` (the top reasons with plain-language descriptions), `warnings` (attachment
warnings), `model_version`.

## Errors

| Status | Cause |
|---|---|
| 422 | invalid input: bad upload (type, size, unreadable), an email with no usable text, or an unknown report format |
| 404 | unknown report id |
| 503 | model could not be loaded from `MODEL_DIR` (train first) |
| 500 | server-side configuration or database error |

Settings come from environment variables (see `.env.example`).
