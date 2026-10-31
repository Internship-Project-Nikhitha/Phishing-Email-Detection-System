# Dataset Card: Phishing Email Detection System

**Status: public-source review completed 2026-10-24; no dataset is cleared for this project.** See the [dataset selection decision](dataset-selection.md).

The repository now contains a configurable CSV loader, preprocessing and validation, duplicate analysis, and a leakage-aware train/validation/test splitting workflow. MeAJOR is a research candidate only: public-source review did not establish permission for every upstream email, a reliable mapping of its classes to phishing versus legitimate, or why the paper and release counts differ. **Do not download for project use, train on, redistribute, or commercially use MeAJOR unless these questions are resolved in writing and reviewed by the project.** No dataset is approved for training and no real-data model performance is claimed here. See [dataset research](dataset-research.md) and [candidate comparison](dataset-candidates.md).

## 1. Project purpose and intended use

- **Purpose:** develop a system that classifies email records as `phishing` or `legitimate`.
- **Intended use:** research, learning, and evaluation of phishing-email detection methods.
- **Not intended for:** making security decisions about real mailboxes without further validation, or identifying or profiling individuals.

## 2. Required schema and label definitions

Each email record uses the following fields:

| Field | Type | Requirement | Description |
|---|---|---|---|
| `subject` | String | Optional | Email subject text |
| `body` | String | Optional | Email body text |
| `sender` | String | Optional | Sender address or identifier |
| `label` | String | Required | Class label |

At least one of `subject` or `body` must contain usable text.

**Working label definitions — to be checked against the chosen dataset's own guidelines:**

- `phishing`: an email intended to deceive recipients, such as by soliciting credentials, personal data, money, or interaction with malicious content.
- `legitimate`: a genuine email without deceptive or malicious intent.

The preprocessing implementation normalizes supported label variants to `phishing` or `legitimate`. Accepted variants include `phish`, `phishing email`, `malicious`, `legit`, `ham`, `safe`, `safe email`, `benign`, and the integer labels `1` and `0`, respectively. Matching is case-insensitive and supports documented separator variations.

Unknown labels are rejected. In particular, `spam` is not automatically treated as phishing.

The final label mapping must be reviewed against the selected dataset's actual labelling scheme.

## 3. Dataset source and licensing

### Leading candidate: MeAJOR v2.0

- Official record: [Zenodo v2.0](https://zenodo.org/records/18471483); paper: [MeAJOR Corpus](https://arxiv.org/abs/2507.17978).
- Zenodo's [record metadata](https://zenodo.org/api/records/18471483) declares **CC BY 4.0** for the deposit and reports 108,685 samples. This confirms the license identifier selected for the deposit, not that the depositors hold every right needed for all embedded messages or that all upstream terms permit the intended use. The [CC BY 4.0 legal code](https://creativecommons.org/licenses/by/4.0/legalcode) itself does not warrant title or non-infringement.
- Zenodo names TREC-05/06/07, Nazario, and Nigerian Fraud. The [NIST TREC Spam Track page](https://trec.nist.gov/data/spam.html) identifies the TREC collections as spam corpora but does not state an applicable reuse license. The [Nazario maintainer's README](https://monkey.org/~jose/phishing/README.txt) states CC BY 4.0 for that corpus and warns that it is a personal inbox, hand-classified with possible errors, and that later mailbox material is not anonymized. MeAJOR does not provide a row-level source manifest, an exact upstream release/version for every source, or a rights statement for the named Nigerian Fraud collection. The upstream-rights review is therefore **not cleared**, not merely assumed from Zenodo's deposit-level label.
- Zenodo defines `0 = benign` and `1 = phishing`. The paper's methods section describes TREC inputs as spam corpora, but neither the record nor the inspected paper documents how original labels were assigned to these two MeAJOR classes. Do not assume `benign` means legitimate.
- The paper reports 220,932 combined samples before cleaning and 135,894 after duplicate and empty samples were removed. The Zenodo v2.0 record reports 108,685 samples. No public explanation linking the paper's post-cleaning corpus to the downloadable release was found; the discrepancy is **unresolved**. Do not treat these counts as interchangeable.
- The CSV header was checked without downloading or inspecting email rows. It has 20 columns, including `body`, `source`, and `label`. The schema appears structurally compatible with the loader, but class semantics and permission must be resolved before mapping labels or training.

**Recommendation:** MeAJOR is **not cleared for project use**. Do not train on or redistribute it unless the authors provide written source-by-source rights/provenance, explain the label construction and count difference, and the project approves the response. A declared license is not a substitute for verifying upstream permissions. No author confirmation has been obtained; this is a due-diligence status, not legal advice.

Other investigated candidates and the evidence behind this assessment are recorded in [dataset research](dataset-research.md) and [dataset candidates](dataset-candidates.md).

The following project-use items remain **PENDING**:

| Item | Status |
|---|---|
| Written author confirmation of the exact upstream source releases and reuse rights for each source, including Nigerian Fraud and TREC materials | PENDING — not established by public record |
| Author explanation of the original-to-MeAJOR label mapping and definition of `benign` | PENDING — not established by public record |
| Explanation linking 220,932 raw → 135,894 post-cleaning paper counts to the 108,685 Zenodo v2.0 release | PENDING — no public reconciliation found |
| Project/legal review of permissions for the intended use after written clarification | PENDING |
| Local release row count, class distribution, duplicate rate, and quality audit | PENDING |
| Privacy and anonymization review of the actual dataset | PENDING |

Do not report locally verified dataset statistics or claim that a dataset has been approved until the relevant evidence has been checked and recorded. Published counts above are attributed to their respective sources, not verified from downloaded rows. Do not commit raw email data containing personal or confidential information.

## 4. Implemented preprocessing and data loading

### Individual-record preprocessing

Implemented in `src/preprocessing.py`:

- Validates the record structure and supported field types.
- Requires usable subject or body text.
- Normalizes whitespace.
- Normalizes recognized labels and rejects unknown labels.
- Reports invalid records through batch-processing results.

Punctuation and URLs are preserved as text. This implementation does not establish that HTML, invisible characters, or every dataset-specific encoding issue has been handled.

### Configurable CSV loading

Implemented in `src/dataset.py`:

- Validates dataset configuration.
- Supports configurable column mappings, delimiter, and encoding.
- Supports explicit raw-label mappings and an optional row limit.
- Checks CSV headers and row shape.
- Reports invalid records and loading errors.

The loader's existence does not mean that a real dataset has been selected, loaded, or approved.

## 5. Duplicate analysis and splitting

### Duplicate analysis

Implemented in `src/keys.py` and `src/quality.py`:

- Exact matching uses normalized subject/body content.
- Near matching applies more aggressive normalization, including URLs, email addresses, digits, and punctuation.
- Duplicate groups can be identified.
- Deduplication supports consistent-label records and reports conflicting-label groups rather than silently choosing a preferred label.

Near matching can group unrelated messages with similar templates. Its impact must be reviewed before relying on it for evaluation.

### Train/validation/test splitting

Implemented in `src/splitting.py`:

- Supports configurable training, validation, and test ratios.
- Supports a random seed and optional stratification.
- Keeps duplicate groups within a single partition.
- Checks for duplicate leakage across partitions.
- Reports conditions that prevent a safe split.

The default target ratios are 70% training, 15% validation, and 15% testing. Actual proportions can differ because duplicate groups are assigned together.

### Combined preparation workflow

Implemented in `src/data_prep.py` through `prepare_splits()`:

- Loads and preprocesses the configured dataset.
- Retains invalid-record errors for inspection.
- Reports duplicate groups.
- Produces train, validation, and test partitions.

**Important:** the combined workflow reports duplicate groups but does not automatically remove duplicate records before splitting. Duplicate-group protection is intended to prevent matching records from crossing partition boundaries.

No real-data split sizes or duplicate statistics are reported in this card because the selected dataset has not yet been verified.

## 6. Privacy, safety, and limitations

- Email records may contain names, addresses, credentials, or other sensitive information. Review the chosen dataset's contents and licence before use.
- Do not commit raw personal or confidential email data.
- Do not include secrets or real personal emails in tests or documentation.
- Treat URLs as text only. Do not fetch or resolve links from phishing emails, and do not open untrusted attachments.
- The current record schema represents subject, body, sender, and label. It does not by itself represent all email headers, attachment contents, or the actual destination of a link.
- Class imbalance, source bias, noisy labels, duplicate contamination, and changes in phishing tactics are risks to investigate, not findings established by this card.
- Accuracy alone may be misleading if one class dominates. Evaluation should eventually report suitable class-sensitive metrics as well.

## 7. Model and evaluation status

A trained baseline classifier and evaluation on a verified real dataset are **not documented as completed in the current project state**.

Before reporting model performance:

1. Verify and document the dataset source, licence, schema, and labelling methodology.
2. Record the actual dataset size and class distribution.
3. Run the implemented audit and splitting workflow on the approved data.
4. Record the split configuration and random seed.
5. Train and evaluate a baseline using the agreed pipeline.
6. Record actual results, limitations, and reproducibility details.

Do not insert invented metrics, sample counts, class distributions, or provenance information.

## 8. Maintenance

Update this card whenever the dataset is selected, inspected, or used for evaluation. Distinguish verified facts from assumptions and pending checks. Record the evidence supporting any newly completed item.