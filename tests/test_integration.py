"""End-to-end integration tests (team lead).

Part 1 runs the whole analysis workflow with a fake model (no scikit-learn).
Part 2 trains a real model on the synthetic fixture and runs the same workflow.
"""

from pathlib import Path

import pytest

from src import ingest, reports, service, storage
from tests.helpers import FakePredictor

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLES = PROJECT_ROOT / "samples"
CONFIG = PROJECT_ROOT / "tests" / "fixtures" / "sample_dataset.json"


def record_from(name):
    parsed = ingest.parse_eml((SAMPLES / name).read_bytes())
    return {key: parsed[key] for key in ("subject", "body", "sender")}, parsed["attachment_warnings"]


def test_upload_analyze_store_report_roundtrip_with_a_fake_model():
    conn = storage.connect(":memory:")
    record, warnings = record_from("suspicious_attachment_sample.eml")

    result = service.analyze_and_store(conn, record, FakePredictor(), source_name="sample.eml", extra_warnings=warnings)
    stored = storage.get_analysis(conn, result["id"])
    markdown = reports.analysis_to_markdown(stored)

    assert stored["warnings"] == warnings and warnings
    assert "invoice.pdf.exe" in markdown
    assert "Links in the email were not opened" in markdown
    assert reports.history_to_csv(storage.list_history(conn)).count("\n") == 2
    conn.close()


def test_batch_csv_flows_through_the_service_and_reports_bad_rows():
    rows = ingest.parse_csv_upload((SAMPLES / "sample_batch.csv").read_bytes())

    results, errors = service.analyze_many(rows, FakePredictor())

    assert [r["label"] for r in results] == ["phishing", "legitimate", "legitimate"]
    assert len(errors) == 1


# @@PART 2
def test_real_model_trained_on_the_fixture_works_through_the_whole_workflow(tmp_path):
    pytest.importorskip("sklearn")
    pytest.importorskip("joblib")
    from scripts import train
    from src import bundle
    from src.features import pipeline

    _, best = train.run_training(CONFIG, base_dir=PROJECT_ROOT, model_names=["logreg_combined"])
    bundle.save_bundle(best, tmp_path / "model")
    predictor = bundle.load_bundle(tmp_path / "model")
    conn = storage.connect(":memory:")

    phishing, _ = record_from("phishing_sample.eml")
    legitimate, _ = record_from("legitimate_sample.eml")
    bad = service.analyze_and_store(conn, phishing, predictor, source_name="phishing_sample.eml")
    good = service.analyze_and_store(conn, legitimate, predictor, source_name="legitimate_sample.eml")

    assert 0.0 <= bad["score"] <= 1.0 and 0.0 <= good["score"] <= 1.0
    assert bad["score"] > good["score"]
    known = set(pipeline.feature_names())
    for indicator in bad["indicators"]:
        assert indicator["feature"] in known or indicator["feature"].startswith("word:")
        assert indicator["contribution"] > 0
    assert len(storage.list_history(conn)) == 2
    conn.close()
