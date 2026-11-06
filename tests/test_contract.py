"""Interface contract test (team lead).

Checks that every function/class listed in docs/interfaces.md still exists.
If a team member renames something that others depend on, this test fails.
"""

import importlib

import pytest

CONTRACT = {
    "src.preprocessing": ["preprocess_email", "preprocess_emails", "normalize_label", "normalize_text",
                          "EmailValidationError", "BatchResult", "RecordError"],
    "src.keys": ["exact_key", "near_key", "key_function", "record_id"],
    "src.dataset": ["DatasetConfig", "DatasetError", "parse_config", "load_config", "load_dataset",
                    "categorize_error", "count_error_reasons"],
    "src.quality": ["find_duplicate_groups", "deduplicate", "DedupResult", "RemovedRecord",
                    "audit_quality", "audit_dataset", "QualityAudit"],
    "src.splitting": ["SplitResult", "validate_ratios", "split_dataset", "audit_split_leakage",
                      "assert_no_duplicate_leakage", "fingerprint_split", "LeakageReport"],
    "src.metrics": ["confusion_counts", "compute_metrics", "format_metrics_markdown"],
    "src.data_prep": ["PreparedData", "prepare_splits"],
    "src.split_report": ["summarize_split", "write_split_ids", "format_quality_markdown", "count_removed"],
    "src.features.base": ["FeatureRegistry"],
    "src.features.pipeline": ["feature_names", "feature_descriptions", "extract_all", "extract_many", "check_pipeline"],
    "src.explain": ["validate_thresholds", "risk_level", "describe_feature", "top_indicators", "explain"],
    "src.storage": ["connect", "init_db", "save_analysis", "list_history", "get_analysis", "clear_history"],
    "src.reports": ["sanitize_csv_cell", "analysis_to_json", "analysis_to_markdown", "history_to_csv"],
    "src.ingest": ["IngestError", "validate_upload", "parse_eml", "parse_csv_upload", "attachment_warnings"],
    "src.analysis_input": ["prepare_for_analysis"],
    "src.service": ["Predictor", "analyze_record", "analyze_and_store", "analyze_many"],
    "src.settings": ["Settings", "SettingsError", "load_settings"],
    "src.benchmark": ["time_calls", "measure_latency"],
}
SKLEARN_CONTRACT = {
    "src.baseline": ["record_text", "build_baseline", "train_baseline", "predict_labels", "predict_scores"],
    "src.vectorize": ["TextFeatures", "EngineeredFeatures", "FeatureBuilder"],
    "src.models": ["ModelSpec", "available_models", "TrainedModel", "train_model", "tune_model",
                   "evaluate_model", "contributions"],
    "src.bundle": ["ModelBundle", "make_version", "save_bundle", "load_bundle"],
}


@pytest.mark.parametrize("module_name, names", sorted(CONTRACT.items()))
def test_documented_names_exist(module_name, names):
    module = importlib.import_module(module_name)

    missing = [name for name in names if not hasattr(module, name)]

    assert missing == [], f"{module_name} is missing {missing}"


@pytest.mark.parametrize("module_name, names", sorted(SKLEARN_CONTRACT.items()))
def test_documented_model_names_exist(module_name, names):
    pytest.importorskip("sklearn")
    module = importlib.import_module(module_name)

    missing = [name for name in names if not hasattr(module, name)]

    assert missing == [], f"{module_name} is missing {missing}"


def test_every_feature_module_exposes_the_same_interface():
    from src.features import sender, text, urls

    for module in (sender, urls, text):
        assert callable(module.extract) and callable(module.descriptions)
        assert module.registry.names()
