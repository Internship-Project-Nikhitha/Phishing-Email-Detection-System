"""Turn email records into numeric matrices for scikit-learn models (Member 5).

Two kinds of inputs:

* ``TextFeatures``: TF-IDF of subject + body (word and two-word phrases).
* ``EngineeredFeatures``: the hand-built sender/URL/text features from
  ``src/features/pipeline.py``, scaled to a common range.

``FeatureBuilder`` combines them depending on ``mode``. Always fit on training
records only, then call ``transform`` on validation/test/new records.
"""

from typing import Any

from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MaxAbsScaler

from src.baseline import record_text

Record = dict[str, Any]


class TextFeatures:
    """TF-IDF features from the subject and body text."""

    def __init__(self, max_features: int = 20000, min_df: int = 1) -> None:
        self._tfidf = TfidfVectorizer(
            lowercase=True, ngram_range=(1, 2), sublinear_tf=True, max_features=max_features, min_df=min_df
        )

    def fit(self, records: list[Record]) -> "TextFeatures":
        if not records:
            raise ValueError("Cannot fit on an empty list of records.")
        self._tfidf.fit([record_text(record) for record in records])
        return self

    def transform(self, records: list[Record]) -> csr_matrix:
        return self._tfidf.transform([record_text(record) for record in records]).tocsr()

    def fit_transform(self, records: list[Record]) -> csr_matrix:
        return self.fit(records).transform(records)

    @property
    def names(self) -> list[str]:
        """Column names as ``word:<term>``."""
        return [f"word:{term}" for term in self._tfidf.get_feature_names_out()]


# @@PART 2
from src.features.pipeline import extract_all  # noqa: E402

MODES = ("text", "engineered", "combined")


class EngineeredFeatures:
    """The hand-built features, scaled by their maximum absolute training value."""

    def __init__(self) -> None:
        self._vectorizer = DictVectorizer(sparse=True)
        self._scaler = MaxAbsScaler()

    def _rows(self, records: list[Record]) -> list[dict[str, float]]:
        return [extract_all(record) for record in records]

    def fit(self, records: list[Record]) -> "EngineeredFeatures":
        if not records:
            raise ValueError("Cannot fit on an empty list of records.")
        self._scaler.fit(self._vectorizer.fit_transform(self._rows(records)))
        return self

    def transform(self, records: list[Record]) -> csr_matrix:
        return csr_matrix(self._scaler.transform(self._vectorizer.transform(self._rows(records))))

    def fit_transform(self, records: list[Record]) -> csr_matrix:
        return self.fit(records).transform(records)

    @property
    def names(self) -> list[str]:
        return list(self._vectorizer.feature_names_)


class FeatureBuilder:
    """Builds the model input matrix for ``mode`` = 'text', 'engineered' or 'combined'."""

    def __init__(self, mode: str = "combined", max_features: int = 20000) -> None:
        if mode not in MODES:
            raise ValueError(f"Unknown mode {mode!r}. Use one of: {', '.join(MODES)}.")
        self.mode = mode
        self.text = TextFeatures(max_features=max_features) if mode in ("text", "combined") else None
        self.engineered = EngineeredFeatures() if mode in ("engineered", "combined") else None

    def _parts(self) -> list[Any]:
        return [part for part in (self.text, self.engineered) if part is not None]

    def fit(self, records: list[Record]) -> "FeatureBuilder":
        for part in self._parts():
            part.fit(records)
        return self

    def transform(self, records: list[Record]) -> csr_matrix:
        matrices = [part.transform(records) for part in self._parts()]
        return matrices[0] if len(matrices) == 1 else hstack(matrices, format="csr")

    def fit_transform(self, records: list[Record]) -> csr_matrix:
        return self.fit(records).transform(records)

    @property
    def feature_names(self) -> list[str]:
        """Column names in matrix order (``word:...`` first, then engineered names)."""
        names: list[str] = []
        for part in self._parts():
            names += part.names
        return names
