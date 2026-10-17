# Phishing Email Detection System

A cybersecurity internship project that will eventually classify emails as
`phishing` or `legitimate`. The project is built in small milestones.

## Current scope: Day 1 only

This repository currently contains **only** the foundation for checking and
cleaning individual email records:

- an email record format (`subject`, `body`, `sender`, `label`)
- label normalization to `phishing` or `legitimate`
- whitespace cleanup that keeps punctuation and URLs intact
- clear validation errors for bad input
- automated tests (pytest) for the above
- a dataset card that records what is still unknown about the data

Nothing else exists yet. There is **no** dataset, dataset loader, train/validation/test
split, machine-learning model, feature engineering, API, dashboard, database,
or email upload feature.

## Expected input format

One email record is a Python dictionary:

| Field     | Required?                             | Meaning                                  |
|-----------|---------------------------------------|------------------------------------------|
| `subject` | Optional                              | Email subject text                       |
| `body`    | Optional                              | Email body text                          |
| `sender`  | Optional                              | Sender address or identifier             |
| `label`   | **Required**                          | Class label (see below)                  |

Rules:

- At least one of `subject` or `body` must contain text (after whitespace is
  cleaned). A `sender` alone is not enough.
- A missing or `None` optional field becomes an empty string `""`.
- Text fields must be strings. Other types (numbers, lists, ...) are rejected.
- Extra keys are ignored.

### Supported label variations

Matching ignores upper/lower case and surrounding spaces, and treats `_` and `-`
between words like a space (so `Safe_Email` works, but `-1` does not become `1`).

| Normalized label | Accepted variations                                                 |
|------------------|---------------------------------------------------------------------|
| `phishing`       | `phishing`, `phish`, `phishing email`, `malicious`, `1`, `1` (int)  |
| `legitimate`     | `legitimate`, `legit`, `ham`, `safe`, `safe email`, `benign`, `0`, `0` (int) |

Any other label (for example `spam`, `suspicious`, `2`) is rejected with an
error instead of being guessed. Booleans (`True`/`False`) are also rejected.

### Output format

`preprocess_email()` returns a new dictionary with exactly four string fields:
`subject`, `body`, `sender`, `label`. Text fields have their whitespace
normalized; `label` is `"phishing"` or `"legitimate"`.

## Safe handling of URLs

Emails in phishing datasets can contain malicious links. This code treats URLs as
plain text only: it never opens, fetches, or resolves them. When you extend this
project, keep it that way, and never click links from dataset emails.

## Prerequisites

- Python 3.11 or newer
- `pip` (included with Python)

Check your version:

```
python --version
```

On Windows you can also use the launcher: `py -3.11 --version`. If `python` is
not found on Linux/macOS, use `python3` instead.

## Setup

Run these commands from the project's root folder (the one containing this
`README.md`).

**1. Create a virtual environment**

```
python -m venv .venv
```

**2. Activate it**

- Windows (PowerShell): `.venv\Scripts\Activate.ps1`
- Windows (Command Prompt): `.venv\Scripts\activate.bat`
- Linux / macOS: `source .venv/bin/activate`

If PowerShell blocks the script, run
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` and try again.

**3. Install dependencies**

```
python -m pip install -r requirements.txt
```

The only dependency is `pytest`.

## Run the tests

```
python -m pytest
```

Add `-v` for a test-by-test listing: `python -m pytest -v`.

## Quick example

Start Python from the project root (`python`) and try:

```python
from src.preprocessing import preprocess_email, preprocess_emails

preprocess_email({
    "subject": "  Verify   your account ",
    "body": "Log in at http://login.example.invalid/verify?id=1 today.",
    "label": "Phish",
})
# {'subject': 'Verify your account',
#  'body': 'Log in at http://login.example.invalid/verify?id=1 today.',
#  'sender': '',
#  'label': 'phishing'}

result = preprocess_emails([
    {"subject": "Hi", "body": "Lunch?", "label": "ham"},
    {"subject": "Hi", "body": "Hello", "label": "spam"},
])
len(result.valid)   # 1
result.errors[0]    # RecordError(index=1, message="Unknown label 'spam'. ...")
```

## Project layout

```
README.md
requirements.txt
src/
    __init__.py
    preprocessing.py      # validation + preprocessing functions
tests/
    test_preprocessing.py # pytest tests
docs/
    dataset-card.md       # dataset documentation (many fields still pending)
```

## Current limitations

- Works on in-memory Python dictionaries only; it does not read files.
- Only whitespace is normalized. HTML is not stripped, and invisible characters
  such as zero-width spaces are not removed.
- Line breaks become single spaces, so paragraph structure is not kept.
- The sender is not checked for being a valid email address.
- The list of label variations is small and fixed. Datasets that use other label
  names will need those names mapped explicitly later.
- No duplicate detection, language detection, or other dataset-level checks.

## Next planned milestone (not started)

Choose a candidate dataset, verify its source and license, and fill in the
pending sections of `docs/dataset-card.md`. Dataset loading, splitting, and any
modeling come after that and are not part of Day 1.
