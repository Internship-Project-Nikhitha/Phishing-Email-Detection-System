# Dataset Card: Phishing Email Detection System

**Status: draft (Day 1).** No dataset has been selected or downloaded yet. Every
item marked **PENDING** must be filled in from verified information before any
data is used. Nothing in this card describes real results.

## 1. Project purpose and intended use

- **Purpose:** support an internship project that will classify emails as
  `phishing` or `legitimate`.
- **Intended use of the data (planned):** training and evaluating a phishing
  email classifier for learning and research.
- **Not intended for:** making security decisions about real mailboxes without
  further validation, or identifying or profiling individuals.

## 2. Required schema and label definitions

Each record is a dictionary with these fields:

| Field     | Type   | Required?                              | Description                        |
|-----------|--------|----------------------------------------|------------------------------------|
| `subject` | string | Optional                               | Email subject text                 |
| `body`    | string | Optional                               | Email body text                    |
| `sender`  | string | Optional                               | Sender address or identifier       |
| `label`   | string | **Required**                           | `phishing` or `legitimate`         |

At least one of `subject` or `body` must contain text.

**Label definitions (working definitions, to be checked against the chosen dataset's own labeling guidelines):**

- `phishing`: an email that tries to deceive the recipient, for example into
  revealing credentials or personal data, opening a malicious link or
  attachment, or sending money.
- `legitimate`: a genuine email with no deceptive or malicious intent.

**Accepted label spellings** (normalized by the code): `phishing`, `phish`, `phishing email`, `malicious`, and `1` for phishing; `legitimate`, `legit`, `ham`, `safe`, `safe email`, `benign`, and `0` for legitimate. Matching ignores case and surrounding whitespace. Spaces, underscores (`_`), and hyphens (`-`) between letters or digits are treated as separators, so `Safe_Email` and `safe-email` both match `safe email`. Integer labels `1` and `0` are also accepted. Other labels, including `spam`, are rejected. Spam is not automatically assumed to be phishing.

## 3. Dataset source and licensing

| Item                      | Status                       |
|---------------------------|------------------------------|
| Dataset name and source   | **PENDING** (not selected)   |
| Download location / date  | **PENDING**                  |
| License                   | **PENDING**                  |
| License verification      | **PENDING**                  |
| Terms of use / redistribution rules | **PENDING**        |
| Dataset size (records)    | **PENDING**                  |
| Class distribution        | **PENDING**                  |
| Time period covered       | **PENDING**                  |
| Original labeling method  | **PENDING**                  |

No dataset may be added to the repository or used for training until the source
and license are verified and recorded here.

## 4. Data cleaning and preprocessing

**Implemented in Day 1 (per individual record, in `src/preprocessing.py`):**

- Check that the record is a dictionary with a usable `subject` or `body`.
- Treat missing or `None` optional fields as empty strings.
- Normalize whitespace (runs of spaces, tabs, and newlines become one space;
  ends are trimmed). Punctuation and URLs are left unchanged.
- Normalize the label to `phishing` or `legitimate`, and reject unknown labels.
- Reject records with no usable content or no valid label, with an error message.

**Planned, not implemented:** dataset-level cleaning, removal of duplicates,
handling of encodings and HTML, and any feature extraction. These will be
decided after the dataset is chosen and inspected.

## 5. Privacy and safe-handling considerations

- Email datasets may contain real names, addresses, phone numbers, account
  details, or other personal data. Check what the chosen dataset contains and
  whether it has been anonymized (**PENDING**).
- Do not commit raw data containing personal information to the repository.
- Do not include credentials, secrets, or real personal emails in code, tests,
  or documentation. Tests use fictional content and reserved example domains.
- **URLs and attachments in phishing emails can be dangerous.** URLs are kept
  as plain text only. Code must never open, fetch, or resolve them, and people
  working with the data should not click links or open attachments.
- Share only what the dataset license and privacy review allow.

## 6. Potential class imbalance, duplicates, bias, and limitations

These are risks to check once a dataset is chosen. They are not findings.

- **Class imbalance:** phishing and legitimate emails may not be equally
  represented. Class distribution is **PENDING**. Accuracy alone can be
  misleading if one class dominates.
- **Duplicates and near-duplicates:** the same or very similar emails may appear
  many times (templates, mass mailings, forwarded copies). They can inflate
  results if they appear in more than one data split.
- **Source bias:** emails from one organization, time period, language, or
  collection method may not represent other real-world email.
- **Label quality:** labels may be noisy or assigned by an unknown process.
- **Changing threats:** phishing tactics change over time, so older data may
  not reflect current attacks.
- **Content limits:** the schema keeps only subject, body, sender, and label.
  Headers, attachments, HTML structure, and links' real destinations are not
  represented.

## 7. Planned train/validation/test separation and leakage prevention

**Planned only. No splitting has been implemented.**

- Split the data into separate training, validation, and test sets before any
  model tuning, with the test set kept untouched until final evaluation.
- Remove duplicates and near-duplicates before splitting, so the same email
  cannot appear in more than one set.
- Fit any preprocessing or vocabulary only on training data, then apply it to
  the validation and test sets.
- Consider keeping related emails (same sender or campaign) together in one
  split, if the dataset provides enough information.
- If the data has timestamps, consider splitting by time to better mimic real use.
- Use stratified splits or another documented method so each set keeps a
  similar label balance. Record the split method and random seed.

## 8. Status summary

| Item                                  | Status                |
|---------------------------------------|-----------------------|
| Schema and label definitions          | Defined (Day 1)       |
| Per-record preprocessing functions    | Implemented (Day 1)   |
| Dataset selection                     | **PENDING**           |
| Source and license verification       | **PENDING**           |
| Dataset size and class distribution   | **PENDING**           |
| Duplicate and bias analysis           | Not started           |
| Train/validation/test split           | Planned, not started  |
