"""Tiny helper that lets feature modules register small, named feature functions.

Example::

    registry = FeatureRegistry("sender")

    @registry.register("has_sender", "The email has a sender value.")
    def has_sender(record):
        return 1.0 if record.get("sender") else 0.0

    registry.extract({"sender": "a@example.com"})   # {"sender_has_sender": 1.0}

Registered names get the registry prefix (``sender_`` above) so feature names
from different modules can never collide.
"""

from collections.abc import Callable
from typing import Any

FeatureFunction = Callable[[dict[str, Any]], float]


class FeatureRegistry:
    """A collection of named numeric feature functions for one feature module."""

    def __init__(self, prefix: str) -> None:
        if not prefix or not prefix.isidentifier():
            raise ValueError("Registry prefix must be a non-empty identifier such as 'sender'.")
        self.prefix = prefix
        self._functions: dict[str, FeatureFunction] = {}
        self._descriptions: dict[str, str] = {}

    def register(self, name: str, description: str) -> Callable[[FeatureFunction], FeatureFunction]:
        """Decorator that registers a feature function as ``<prefix>_<name>``.

        Args:
            name: Short feature name (letters, digits, underscores).
            description: One plain-language sentence used in explanations.

        Raises:
            ValueError: If the name is invalid, the description is empty, or
                the feature is already registered.
        """
        if not name or not name.isidentifier():
            raise ValueError(f"Feature name {name!r} must be a valid identifier.")
        if not isinstance(description, str) or not description.strip():
            raise ValueError(
                f"Feature {name!r} needs a description; provide a non-empty string description."
            )
        full_name = f"{self.prefix}_{name}"
        if full_name in self._functions:
            raise ValueError(f"Feature '{full_name}' is already registered.")

        def decorator(function: FeatureFunction) -> FeatureFunction:
            self._functions[full_name] = function
            self._descriptions[full_name] = description.strip()
            return function

        return decorator

    def names(self) -> list[str]:
        """Feature names in registration order."""
        return list(self._functions)

    def descriptions(self) -> dict[str, str]:
        """Map each feature name to its plain-language description."""
        return dict(self._descriptions)

    def extract(self, record: dict[str, Any]) -> dict[str, float]:
        """Compute every registered feature for one cleaned record.

        Raises:
            TypeError: If ``record`` is not a dict.
        """
        if not isinstance(record, dict):
            raise TypeError(f"Record must be a dict, got {type(record).__name__}.")
        return {name: float(function(record)) for name, function in self._functions.items()}
