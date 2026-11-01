"""Combine all feature modules into one feature dictionary (Member 4).

Every record gets the same feature names in the same order, so the result can
be turned into a model matrix. Features come from three modules:

* ``sender``: sender address and display name
* ``urls``: web addresses in the email (text analysis only)
* ``text``: wording, markup and formatting
"""

from typing import Any

from src.features import sender, text, urls

MODULES = (sender, urls, text)


def feature_names() -> list[str]:
    """All feature names, in a fixed order (sender, then urls, then text)."""
    names = [name for module in MODULES for name in module.registry.names()]
    if len(set(names)) != len(names):
        raise RuntimeError("Duplicate feature names across feature modules.")
    return names


def feature_descriptions() -> dict[str, str]:
    """Map every feature name to its plain-language description."""
    merged: dict[str, str] = {}
    for module in MODULES:
        merged.update(module.descriptions())
    return merged


def extract_all(record: dict[str, Any]) -> dict[str, float]:
    """Compute every feature for one cleaned record.

    Returns:
        A dict with exactly the keys of ``feature_names()``, in that order.

    Raises:
        TypeError: If ``record`` is not a dict.
    """
    values: dict[str, float] = {}
    for module in MODULES:
        values.update(module.extract(record))
    return values


# @@PART 2
def extract_many(records: list[dict[str, Any]]) -> list[dict[str, float]]:
    """Compute features for a list of records (same order as the input)."""
    return [extract_all(record) for record in records]


def check_pipeline() -> list[str]:
    """Return a list of problems with the registered features (empty means OK).

    Checks that names are unique, every feature has a non-empty description and
    every module's features really appear in the combined output.
    """
    problems: list[str] = []
    names = [name for module in MODULES for name in module.registry.names()]
    if len(set(names)) != len(names):
        problems.append("Duplicate feature names.")
    descriptions = feature_descriptions()
    for name in names:
        if not descriptions.get(name, "").strip():
            problems.append(f"Feature '{name}' has no description.")
    combined = extract_all({})
    if list(combined) != names:
        problems.append("extract_all() output does not match the registered feature names.")
    return problems
