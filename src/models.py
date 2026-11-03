"""Candidate classifiers, training and validation-based tuning (Member 5).

Four candidates are compared:

* ``logreg_combined``: Logistic Regression on TF-IDF + engineered features
* ``tfidf_logreg``: Logistic Regression on TF-IDF text only (NLP baseline)
* ``tfidf_naive_bayes``: Multinomial Naive Bayes on TF-IDF text (NLP classifier)
* ``random_forest_engineered``: Random Forest on the hand-built features

Tuning uses only the training and validation splits. The test split is never
touched in this module.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB

from src import metrics
from src.vectorize import FeatureBuilder

Record = dict[str, Any]
POSITIVE_LABEL = "phishing"


@dataclass(frozen=True)
class ModelSpec:
    """Description of one candidate model.

    Attributes:
        name: Short unique name.
        mode: Feature mode for ``FeatureBuilder`` ('text', 'engineered', 'combined').
        description: One plain sentence.
        factory: ``factory(seed, params)`` returns an untrained estimator.
        param_grid: Parameter dictionaries to try during tuning.
    """

    name: str
    mode: str
    description: str
    factory: Callable[[int, dict[str, Any]], Any]
    param_grid: tuple[dict[str, Any], ...]


def available_models() -> dict[str, ModelSpec]:
    """Return every candidate model, keyed by name."""
    specs = [
        ModelSpec(
            "logreg_combined", "combined", "Logistic Regression on TF-IDF + engineered features",
            lambda seed, p: LogisticRegression(C=p["C"], max_iter=2000, class_weight="balanced", random_state=seed),
            tuple({"C": c} for c in (0.1, 1.0, 10.0)),
        ),
        ModelSpec(
            "tfidf_logreg", "text", "Logistic Regression on TF-IDF text only",
            lambda seed, p: LogisticRegression(C=p["C"], max_iter=2000, class_weight="balanced", random_state=seed),
            tuple({"C": c} for c in (0.1, 1.0, 10.0)),
        ),
        ModelSpec(
            "tfidf_naive_bayes", "text", "Multinomial Naive Bayes on TF-IDF text",
            lambda seed, p: MultinomialNB(alpha=p["alpha"]),
            tuple({"alpha": a} for a in (0.1, 0.5, 1.0)),
        ),
        ModelSpec(
            "random_forest_engineered", "engineered", "Random Forest on engineered features",
            lambda seed, p: RandomForestClassifier(
                n_estimators=p["n_estimators"], max_depth=p["max_depth"], class_weight="balanced",
                random_state=seed, n_jobs=1,
            ),
            tuple({"n_estimators": n, "max_depth": d} for n in (100, 300) for d in (None, 10)),
        ),
    ]
    return {spec.name: spec for spec in specs}


@dataclass
class TrainedModel:
    """A fitted feature builder plus estimator that can score new records."""

    spec_name: str
    mode: str
    params: dict[str, Any]
    builder: FeatureBuilder
    estimator: Any

    def predict_scores(self, records: list[Record]) -> list[float]:
        """Probability (0 to 1) that each record is phishing."""
        column = list(self.estimator.classes_).index(POSITIVE_LABEL)
        probabilities = self.estimator.predict_proba(self.builder.transform(records))
        return [float(row[column]) for row in probabilities]

    def predict_labels(self, records: list[Record], threshold: float = 0.5) -> list[str]:
        """``'phishing'`` when the score is at least ``threshold``, else ``'legitimate'``."""
        return ["phishing" if score >= threshold else "legitimate" for score in self.predict_scores(records)]


def train_model(
    spec: ModelSpec,
    train_records: list[Record],
    seed: int = 42,
    params: dict[str, Any] | None = None,
    max_features: int = 20000,
) -> TrainedModel:
    """Fit a feature builder and estimator on training records only.

    Raises:
        ValueError: If training data is empty or lacks one of the two labels.
    """
    if not train_records:
        raise ValueError("Cannot train on an empty list of records.")
    labels = [record["label"] for record in train_records]
    if set(labels) != {"phishing", "legitimate"}:
        raise ValueError("Training data must contain both 'phishing' and 'legitimate' records.")
    chosen = dict(params if params is not None else spec.param_grid[0])
    builder = FeatureBuilder(mode=spec.mode, max_features=max_features).fit(train_records)
    estimator = spec.factory(seed, chosen)
    estimator.fit(builder.transform(train_records), labels)
    return TrainedModel(spec.name, spec.mode, chosen, builder, estimator)


# @@PART 2
@dataclass
class TuningResult:
    """Best parameters for one model, with its validation metrics."""

    spec_name: str
    params: dict[str, Any]
    model: TrainedModel
    validation_metrics: dict[str, Any]
    candidates_tried: int


def evaluate_model(model: TrainedModel, records: list[Record], threshold: float = 0.5) -> dict[str, Any]:
    """Compute metrics for ``model`` on ``records`` (see ``src/metrics.py``)."""
    predicted = model.predict_labels(records, threshold)
    return metrics.compute_metrics([record["label"] for record in records], predicted)


def tune_model(
    spec: ModelSpec,
    train_records: list[Record],
    validation_records: list[Record],
    seed: int = 42,
    max_features: int = 20000,
    threshold: float = 0.5,
) -> TuningResult:
    """Try every parameter set in ``spec.param_grid`` and keep the best.

    Models are fitted on ``train_records`` and compared on ``validation_records``
    only. The best has the highest F1; ties go to the lower false-positive rate,
    then to the earlier parameter set.
    """
    best: TuningResult | None = None
    for params in spec.param_grid:
        model = train_model(spec, train_records, seed, params, max_features)
        result = evaluate_model(model, validation_records, threshold)
        better = best is None or (result["f1"], -result["false_positive_rate"]) > (
            best.validation_metrics["f1"],
            -best.validation_metrics["false_positive_rate"],
        )
        if better:
            best = TuningResult(spec.name, params, model, result, len(spec.param_grid))
    assert best is not None
    return best


# @@PART 3
def contributions(model: TrainedModel, record: Record) -> dict[str, float]:
    """Explain one record: how much each active feature pushed toward 'phishing'.

    * Logistic Regression: ``coefficient * feature value`` (positive means toward phishing).
    * Naive Bayes: ``log P(feature | phishing) - log P(feature | legitimate)`` times the value.
    * Random Forest: the feature's global importance if it is active in this
      record. This shows relevance, NOT direction (forests have no simple sign).

    Only features that are active (non-zero) in the record are returned, and
    only features the model actually used.
    """
    classes = list(model.estimator.classes_)
    phishing = classes.index(POSITIVE_LABEL)
    estimator = model.estimator
    if hasattr(estimator, "coef_"):
        weights = estimator.coef_[0] if phishing == 1 else -estimator.coef_[0]
    elif hasattr(estimator, "feature_log_prob_"):
        legitimate = classes.index("legitimate")
        weights = estimator.feature_log_prob_[phishing] - estimator.feature_log_prob_[legitimate]
    elif hasattr(estimator, "feature_importances_"):
        weights = estimator.feature_importances_
    else:
        raise ValueError(f"Cannot explain estimator of type {type(estimator).__name__}.")

    row = model.builder.transform([record]).tocoo()
    names = model.builder.feature_names
    use_value = not hasattr(estimator, "feature_importances_")
    return {
        names[int(column)]: float(weights[int(column)] * (value if use_value else 1.0))
        for column, value in zip(row.col, row.data)
        if value != 0
    }
