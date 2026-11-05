"""FastAPI service for phishing analysis (Member 4).

Run from the project root::

    uvicorn app.api:app --reload

Endpoints: ``GET /health``, ``POST /analyze``, ``POST /analyze/upload``,
``GET /history``, ``GET /history.csv``, ``GET /report/{id}?format=md|json``.

Safety: uploads are validated (name, type, size) before parsing; links are never
opened and attachments are never saved or executed.

NOTE: this file was written without being executed in the authoring environment
(FastAPI was not installed there). Run ``python -m pytest tests/test_api.py``
after installing the requirements and fix anything it reports.
"""

from typing import Any

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from src import bundle, ingest, reports, service, storage
from src.preprocessing import EmailValidationError
from src.settings import Settings, SettingsError, load_settings

app = FastAPI(title="Phishing Email Detection API", version="1.0")

_cache: dict[str, Any] = {}


class EmailIn(BaseModel):
    """An email to analyze. At least one of subject or body must contain text."""

    subject: str = ""
    body: str = ""
    sender: str = ""


def get_settings() -> Settings:
    """Settings from environment variables (override in tests)."""
    try:
        return load_settings()
    except SettingsError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


def get_predictor(settings: Settings = Depends(get_settings)):
    """Load the trained model once and reuse it (override in tests)."""
    if "predictor" not in _cache:
        try:
            _cache["predictor"] = bundle.load_bundle(settings.model_dir)
        except FileNotFoundError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
    return _cache["predictor"]


def _options(settings: Settings) -> dict[str, Any]:
    return {"thresholds": settings.thresholds, "decision_threshold": settings.decision_threshold}


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check."""
    return {"status": "ok"}


@app.post("/analyze")
def analyze(email: EmailIn, settings: Settings = Depends(get_settings), predictor=Depends(get_predictor)):
    """Analyze one email sent as JSON and store the result in the history."""
    conn = storage.connect(settings.db_path)
    try:
        return service.analyze_and_store(conn, email.model_dump(), predictor, source_name="api", **_options(settings))
    except EmailValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    finally:
        conn.close()


@app.post("/analyze/upload")
async def analyze_upload(
    file: UploadFile = File(...), settings: Settings = Depends(get_settings), predictor=Depends(get_predictor)
):
    """Analyze an uploaded .eml (one email) or .csv (up to 500 emails)."""
    data = await file.read(ingest.MAX_UPLOAD_BYTES + 1)
    try:
        extension = ingest.validate_upload(file.filename or "", len(data))
        conn = storage.connect(settings.db_path)
        try:
            if extension == ".eml":
                parsed = ingest.parse_eml(data)
                record = {key: parsed[key] for key in ("subject", "body", "sender")}
                return service.analyze_and_store(
                    conn, record, predictor, source_name=file.filename,
                    extra_warnings=parsed["attachment_warnings"], **_options(settings),
                )
            results, errors = [], []
            for index, record in enumerate(ingest.parse_csv_upload(data)):
                try:
                    results.append(
                        {"index": index, **service.analyze_and_store(
                            conn, record, predictor, source_name=file.filename, **_options(settings))}
                    )
                except EmailValidationError as error:
                    errors.append({"index": index, "message": str(error)})
            return {"results": results, "errors": errors}
        finally:
            conn.close()
    except (ingest.IngestError, EmailValidationError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.get("/history")
def history(limit: int = 50, offset: int = 0, settings: Settings = Depends(get_settings)):
    """Return stored analyses, newest first."""
    conn = storage.connect(settings.db_path)
    try:
        return storage.list_history(conn, limit=limit, offset=offset)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    finally:
        conn.close()


@app.get("/history.csv", response_class=PlainTextResponse)
def history_csv(settings: Settings = Depends(get_settings)) -> str:
    """Return the history as a CSV file (no email content)."""
    conn = storage.connect(settings.db_path)
    try:
        return reports.history_to_csv(storage.list_history(conn, limit=1000))
    finally:
        conn.close()


@app.get("/report/{analysis_id}", response_class=PlainTextResponse)
def report(analysis_id: int, format: str = "md", settings: Settings = Depends(get_settings)) -> str:
    """Return one stored analysis as a Markdown or JSON report."""
    if format not in ("md", "json"):
        raise HTTPException(status_code=422, detail="format must be 'md' or 'json'.")
    conn = storage.connect(settings.db_path)
    try:
        analysis = storage.get_analysis(conn, analysis_id)
    finally:
        conn.close()
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return reports.analysis_to_markdown(analysis) if format == "md" else reports.analysis_to_json(analysis)
