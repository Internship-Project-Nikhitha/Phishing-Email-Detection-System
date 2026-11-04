"""Save and load a trained model together with its metadata (Member 5).

A bundle is a folder containing:

* ``model.joblib``: the fitted feature builder and estimator
* ``model_meta.json``: version, parameters, seed, split fingerprint, metrics

SECURITY: ``joblib`` files are pickles. Loading one can run arbitrary code.
Only load bundles that YOU created with ``scripts/train.py``; never load a
``model.joblib`` received from someone else.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib

from src import models

MODEL_FILE = "model.joblib"
META_FILE = "model_meta.json"


@dataclass
class ModelBundle:
    """A trained model plus the version string and metadata that describe it."""

    model: models.TrainedModel
    version: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def predict_score(self, record: dict[str, Any]) -> float:
        """Probability (0 to 1) that one cleaned record is phishing."""
        return self.model.predict_scores([record])[0]

    def contributions(self, record: dict[str, Any]) -> dict[str, float]:
        """Per-feature contributions for one record (see ``models.contributions``)."""
        return models.contributions(self.model, record)


def make_version(spec_name: str, now: datetime | None = None) -> str:
    """Return a version string like ``tfidf_logreg-20261105T101500Z``."""
    moment = now or datetime.now(timezone.utc)
    return f"{spec_name}-{moment:%Y%m%dT%H%M%SZ}"


def save_bundle(bundle: ModelBundle, directory: str | Path) -> Path:
    """Write the model and metadata into ``directory`` (created if needed)."""
    folder = Path(directory)
    folder.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle.model, folder / MODEL_FILE)
    meta = {**bundle.metadata, "version": bundle.version, "model_name": bundle.model.spec_name}
    (folder / META_FILE).write_text(json.dumps(meta, indent=2, default=str) + "\n", encoding="utf-8")
    return folder


def load_bundle(directory: str | Path) -> ModelBundle:
    """Load a bundle saved by ``save_bundle`` (only from folders you created yourself).

    Raises:
        FileNotFoundError: If the model or metadata file is missing.
    """
    folder = Path(directory)
    model_path, meta_path = folder / MODEL_FILE, folder / META_FILE
    for path in (model_path, meta_path):
        if not path.is_file():
            raise FileNotFoundError(
                f"{path} not found. Train a model first with: python scripts/train.py"
            )
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    return ModelBundle(model=joblib.load(model_path), version=metadata["version"], metadata=metadata)
