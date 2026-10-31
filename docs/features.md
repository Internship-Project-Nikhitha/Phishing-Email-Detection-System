# Feature contract

Hand-built features live in `src/features/`. There is one module per kind:

| Module | Owner | Looks at |
|---|---|---|
| `src/features/sender.py` | Member 1 | sender address and display name |
| `src/features/urls.py` | Member 2 | web addresses in subject and body |
| `src/features/text.py` | Member 3 | wording, markup and formatting |
| `src/features/pipeline.py` | Member 4 | combines all of the above |

## How to add a feature

Every module creates a registry and registers small functions:

```python
from src.features.base import FeatureRegistry

registry = FeatureRegistry("sender")          # prefix for every feature name

@registry.register("free_mail", "The sender uses a free webmail provider.")
def free_mail(record):                        # record = cleaned email dict
    return 1.0 if ... else 0.0                # return a number (True/False also works)
```

The final feature name is `<prefix>_<name>` (here `sender_free_mail`).

## Rules

1. A feature function receives a cleaned record (`subject`, `body`, `sender`; `label` is never used) and returns one number.
2. It must work when any field is empty.
3. **No network access.** URLs are text. Never fetch, resolve or open them.
4. The description is one plain sentence; it is shown to analysts as the reason for a warning.
5. Do not use the label inside a feature (that would leak the answer).
6. Every feature needs a test with a positive and a negative example.

`src/features/pipeline.py` merges the three modules; `check_pipeline()` reports
duplicate names or missing descriptions.
