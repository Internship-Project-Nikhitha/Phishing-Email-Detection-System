# Dataset Card: Phishing Email Detection Baseline

## 1. Dataset Title and Status

**Title:** Phishing Email Detection (Cyber Cop Kaggle CSV; Hugging Face mirror `zefang-liu/phishing-email-dataset`).

**Status:** Candidate selected for conditional research use. The project repository does not include or redistribute the dataset. Dataset download, actual file values, data-quality statistics, and underlying email-content rights are **Pending verification**.

## 2. Project Purpose and Intended Use

The intended task is a baseline binary classifier over email text: phishing versus legitimate/safe. This is for research, education, and evaluation of text-classification methods. It is not a mail gateway, security control, legal determination, or guarantee that an email is safe. Human review and layered defenses remain necessary.

## 3. Dataset Source and Official URL

- Kaggle source page: https://www.kaggle.com/datasets/subhajournal/phishingemails
- Public Hugging Face copy/card: https://huggingface.co/datasets/zefang-liu/phishing-email-dataset
- HF CSV file listing: https://huggingface.co/datasets/zefang-liu/phishing-email-dataset/tree/main

The mirror says it is a direct copy of the Kaggle dataset. Kaggle may require an account to download. The HF repository metadata reports that it is public and not gated.

## 4. Publisher and Citation

The Kaggle page attributes the upload to Cyber Cop (`subhajournal`). The mirror says the dataset was originally created by that Kaggle user. The original email collector, acquisition methodology, and author-level provenance are **unknown** in reviewed source descriptions.

No DOI or formal citation requirement was found. Attribute Cyber Cop and the Kaggle source page; when using the mirror, also cite `zefang-liu/phishing-email-dataset` and disclose that it is a copy. Preserve the license notices and changes when sharing permitted derivatives.

## 5. License and Usage Conditions

Kaggle displays **GNU Lesser General Public License 3.0**; the Hugging Face card and repository metadata also declare `lgpl-3.0`. The LGPL-3.0 license generally permits commercial use, modification, and redistribution under its conditions. License confidence for the uploader's declaration is **medium**. Authority to license all underlying message text, personal data, and third-party content is **unknown**; the dataset description does not establish original collection rights. A public download is not proof that every email may legally be redistributed or used commercially.

Do not redistribute dataset rows or use them commercially until the source and rights status of the embedded messages have been reviewed. Seek permission or qualified legal guidance if those rights are material to the project. No dataset file is committed here.

## 6. Access and Download Instructions

Download `Phishing_Email.csv` from the Kaggle source or public HF files page and save it locally as `data/Phishing_Email.csv`. Do not put credentials in repository configuration. Kaggle can require sign-in; do not bypass access controls. No automatic downloader is enabled.

After dependencies are installed, inspect only the label column and counts:

```powershell
python -c "import pandas as pd; print(pd.read_csv('data/Phishing_Email.csv', usecols=['Email Type'])['Email Type'].value_counts(dropna=False).to_dict())"
```

Use the exact label values observed in that command. Do not infer them from file names or transform arbitrary unknown values.

## 7. Dataset Version or Retrieval Date

Hugging Face revision reported by the dataset API: `34085a032c123ca237f314a01a67909cdea35e34`, last modified 2024-01-17. Dataset retrieval date for this project: **Pending verification** (no corpus downloaded). This card's source review date is 2026-10-18.

## 8. Dataset Size

The Hugging Face API reports 18,650 records in one `train` split. File size is reported as about 52 MB. The downloaded file's record count and checksum are **Pending verification**. Per-label counts, missing rows, duplicate rows, and retained rows are **Pending verification**; do not treat the total as a cleaned-data count.

## 9. File Format and Schema

Hugging Face metadata reports a CSV with:

| Source column | Reported type | Meaning stated by source |
|---|---|---|
| `Unnamed: 0` | integer | Meaning not documented; do not assume it is a stable ID. |
| `Email Text` | string | Email body/text. Kaggle describes this as the email body. |
| `Email Type` | string | Email type, described conceptually as Phishing or Safe. |

Actual CSV header and data shape: **Pending verification**. The source does not document header fields, structured raw email headers, attachments, campaign/source IDs, or timestamps. The implementation requires explicit source-to-canonical column mapping.

## 10. Label Definitions and Mapping

The Kaggle description says `Email Type` distinguishes Phishing from Safe. The Hugging Face card marks the dataset for text classification but does not specify raw label tokens or a detailed annotation rubric.

| Canonical label | Source concept | Exact stored source label |
|---|---|---|
| `phishing` | Phishing email | **Pending verification** by inspecting only `Email Type` values. |
| `legitimate` | Safe email | **Pending verification** by inspecting only `Email Type` values. |

The training CLI requires both exact values, and the loader maps only explicitly configured labels. No assumption is made that `spam`, `ham`, `safe`, numeric values, or any guessed spelling is equivalent.

## 11. Data Collection and Provenance

The Kaggle uploader says the data contains email text and type; the HF card says its file is a direct copy of the Kaggle dataset. Original source mailboxes, collection dates, sampling frame, labelers, labeling protocol, and email authenticity are **unknown** from these descriptions. Provenance must not be described as independently verified.

## 12. Preprocessing and Cleaning

The repository loader reads CSV/JSON/JSONL; requires explicit column and label mappings; preserves original source columns, source labels, and source filename; normalizes configured label strings by trim/casefold; rejects missing or blank text, unknown/missing labels, malformed non-string text, and exact text duplicated with conflicting labels; and removes exact duplicate text when enabled. It does not strip URLs, HTML, headers, or email indicators. Invalid-row reports contain source row and reason only, not message content.

No dataset-specific cleaning has been run. Cleaning counts are **Pending verification** after manual download.

## 13. Data-Quality Checks

The loader summary reports input/output counts, missing/empty text, malformed text, unknown labels, conflicting duplicates, exact duplicates, and label distribution. `src/data/validate_dataset.py` reports empty rows, duplicate rows, class counts/imbalance, train/test exact duplicate contamination when splits are supplied, optional group overlap, and row counts with email-address, URL, IPv4, phone-like, and HTML indicators. It preserves the text and does not emit contents.

These are risk indicators, not a proof of safe data, clean annotations, no near-duplicates, or absence of PII. Exact checks do not identify paraphrases or unknown campaign/source overlap.

## 14. Class Distribution

Source-reported total: 18,650. Per-class source counts and cleaned class distribution: **Pending verification**. Run the label-only inspection in Section 6, followed by the validator. Do not infer class balance from the total.

## 15. Privacy and Security Considerations

Email bodies may contain personal names, addresses, phone numbers, account identifiers, quoted conversations, signatures, and other sensitive content. URLs can lead to malicious or tracking resources. Email headers, if present in a downloaded variant, can reveal senders, recipients, routing, or authentication metadata. The dataset source does not document a privacy review or redaction process.

Treat all text and URLs as untrusted. Do not open links, fetch remote resources, execute attachments, or send email text to external services. Do not print full rows or commit samples. The project only counts common sensitive indicators; these checks are incomplete and do not de-identify data.

## 16. Known Biases and Limitations

- The exact source population, time span, language, collection procedure, and class balance are not fully documented; HF metadata tags English but no language audit is available.
- Labels have no published annotation protocol or measured inter-annotator agreement in reviewed source descriptions.
- Data may contain stale patterns, duplicates, source/campaign artifacts, and unintended distribution shortcuts.
- A text-only model may miss sender/domain authentication, rendered HTML behavior, attachments, and context, while learning superficial words or formatting.
- A random split may overstate generalization if messages share campaigns, sources, senders, or time periods.
- A baseline cannot guarantee detection of every phishing email or absence of false positives/negatives.

Dataset-specific duplicate, missing-value, and class-imbalance rates: **Pending verification**.

## 17. Intended and Out-of-Scope Uses

Intended: reproducible academic/educational binary text-classification experiments, subject to license/privacy review.

Out of scope: production blocking decisions without independent validation; sole-factor account, employment, or law-enforcement decisions; claims of comprehensive phishing detection; testing against live mail systems; contacting addresses or opening links found in the data; and redistribution without rights review.

## 18. Train/Test Split Methodology

The baseline uses a seeded 80/20 random split (`random_state=42` by default) and stratifies when each class has at least two examples. Pass `--group-column` for group-held-out splitting when a verified source or campaign identifier is available. Exact duplicate removal occurs before splitting, and the audit can report exact cross-split overlap. The current source schema documents no group or time column, so campaign/source/time independence cannot be established. A random split is not a temporal or source-generalization test.

## 19. Reproducibility Instructions

Follow [README setup and execution instructions](../README.md). Record the dataset source, source revision/version, retrieval date, checksum, exact label strings, loader summary, and split seed in experiment records. Do not record private message bodies. Run tests with `python -m pytest -q`.

## 20. Ethical and Legal Considerations

Use the minimum data necessary, protect local files, restrict access, and remove unnecessary copies. Review applicable privacy, copyright, and dataset terms before processing, publication, or commercial use. LGPL-3.0 on a Kaggle/HF upload does not establish consent or authority over every included message. The project provides no legal advice.

## 21. Candidate Datasets Considered and Reasons for Selection

See [dataset-research.md](dataset-research.md) for the source-by-source comparison. This Kaggle/HF dataset is selected conditionally because it has both stated phishing/safe classes, an explicit declared license, published schema, a reported record count, and easy CSV access. Akilesh G A's Kaggle CSV is a possible alternative with an Apache 2.0 declaration, but its schema, exact labels, count, and provenance are not available in the reviewed metadata. The Naser Alam CC BY-SA 4.0 aggregate is not selected because it conflates some spam with phishing and combines sources with unresolved label and rights compatibility. Nazario is phishing-only; SpamAssassin is spam/ham, not phishing/safe, and leaves sender copyright in place; Enron has no target labels, no explicit license, and significant privacy concerns. None of the three Kaggle listings has fully verified original rights and label quality; ask for permission or further evidence before commercial use or redistribution. The project does not combine these sources.

## 22. References and Attribution

- Cyber Cop, [Phishing Email Detection, Kaggle](https://www.kaggle.com/datasets/subhajournal/phishingemails).
- `zefang-liu`, [phishing-email-dataset, Hugging Face](https://huggingface.co/datasets/zefang-liu/phishing-email-dataset), revision `34085a032c123ca237f314a01a67909cdea35e34`.
- [Dataset metadata API](https://huggingface.co/api/datasets/zefang-liu/phishing-email-dataset).
- Akilesh G A, [Email Phishing Legitimate classifier, Kaggle](https://www.kaggle.com/datasets/akileshga/email-phishing-legitimate-classifier).
- Naser Abdullah Alam, [Phishing Email Dataset, Kaggle](https://www.kaggle.com/datasets/naserabdullahalam/phishing-email-dataset), including its cited [arXiv paper](https://arxiv.org/abs/2405.11619).
- Jose Nazario, [Phishing Corpus](https://monkey.org/~jose/phishing/) and its [CC BY 4.0 license](https://monkey.org/~jose/phishing/LICENSE.txt).
- Apache SpamAssassin, [Public Mail Corpus](https://spamassassin.apache.org/old/publiccorpus/) and [README](https://spamassassin.apache.org/old/publiccorpus/readme.html).
- William W. Cohen / CALO, [Enron Email Dataset](https://www.cs.cmu.edu/~enron/).# Dataset Card: Phishing Email Detection Baseline

## 1. Dataset Title and Status

**Title:** Phishing Email Detection (Cyber Cop Kaggle CSV; Hugging Face mirror `zefang-liu/phishing-email-dataset`).

**Status:** Candidate selected for conditional research use. The project repository does not include or redistribute the dataset. Dataset download, actual file values, data-quality statistics, and underlying email-content rights are **Pending verification**.

## 2. Project Purpose and Intended Use

The intended task is a baseline binary classifier over email text: phishing versus legitimate/safe. This is for research, education, and evaluation of text-classification methods. It is not a mail gateway, security control, legal determination, or guarantee that an email is safe. Human review and layered defenses remain necessary.

## 3. Dataset Source and Official URL

- Kaggle source page: https://www.kaggle.com/datasets/subhajournal/phishingemails
- Public Hugging Face copy/card: https://huggingface.co/datasets/zefang-liu/phishing-email-dataset
- HF CSV file listing: https://huggingface.co/datasets/zefang-liu/phishing-email-dataset/tree/main

The mirror says it is a direct copy of the Kaggle dataset. Kaggle may require an account to download. The HF repository metadata reports that it is public and not gated.

## 4. Publisher and Citation

The Kaggle page attributes the upload to Cyber Cop (`subhajournal`). The mirror says the dataset was originally created by that Kaggle user. The original email collector, acquisition methodology, and author-level provenance are **unknown** in reviewed source descriptions.

No DOI or formal citation requirement was found. Attribute Cyber Cop and the Kaggle source page; when using the mirror, also cite `zefang-liu/phishing-email-dataset` and disclose that it is a copy. Preserve the license notices and changes when sharing permitted derivatives.

## 5. License and Usage Conditions

Kaggle displays **GNU Lesser General Public License 3.0**; the Hugging Face card and repository metadata also declare `lgpl-3.0`. The LGPL-3.0 license generally permits commercial use, modification, and redistribution under its conditions. License confidence for the uploader's declaration is **medium**. Authority to license all underlying message text, personal data, and third-party content is **unknown**; the dataset description does not establish original collection rights. A public download is not proof that every email may legally be redistributed or used commercially.

Do not redistribute dataset rows or use them commercially until the source and rights status of the embedded messages have been reviewed. Seek permission or qualified legal guidance if those rights are material to the project. No dataset file is committed here.

## 6. Access and Download Instructions

Download `Phishing_Email.csv` from the Kaggle source or public HF files page and save it locally as `data/Phishing_Email.csv`. Do not put credentials in repository configuration. Kaggle can require sign-in; do not bypass access controls. No automatic downloader is enabled.

After dependencies are installed, inspect only the label column and counts:

```powershell
python -c "import pandas as pd; print(pd.read_csv('data/Phishing_Email.csv', usecols=['Email Type'])['Email Type'].value_counts(dropna=False).to_dict())"
```

Use the exact label values observed in that command. Do not infer them from file names or transform arbitrary unknown values.

## 7. Dataset Version or Retrieval Date

Hugging Face revision reported by the dataset API: `34085a032c123ca237f314a01a67909cdea35e34`, last modified 2024-01-17. Dataset retrieval date for this project: **Pending verification** (no corpus downloaded). This card's source review date is 2026-10-18.

## 8. Dataset Size

The Hugging Face API reports 18,650 records in one `train` split. File size is reported as about 52 MB. The downloaded file's record count and checksum are **Pending verification**. Per-label counts, missing rows, duplicate rows, and retained rows are **Pending verification**; do not treat the total as a cleaned-data count.

## 9. File Format and Schema

Hugging Face metadata reports a CSV with:

| Source column | Reported type | Meaning stated by source |
|---|---|---|
| `Unnamed: 0` | integer | Meaning not documented; do not assume it is a stable ID. |
| `Email Text` | string | Email body/text. Kaggle describes this as the email body. |
| `Email Type` | string | Email type, described conceptually as Phishing or Safe. |

Actual CSV header and data shape: **Pending verification**. The source does not document header fields, structured raw email headers, attachments, campaign/source IDs, or timestamps. The implementation requires explicit source-to-canonical column mapping.

## 10. Label Definitions and Mapping

The Kaggle description says `Email Type` distinguishes Phishing from Safe. The Hugging Face card marks the dataset for text classification but does not specify raw label tokens or a detailed annotation rubric.

| Canonical label | Source concept | Exact stored source label |
|---|---|---|
| `phishing` | Phishing email | **Pending verification** by inspecting only `Email Type` values. |
| `legitimate` | Safe email | **Pending verification** by inspecting only `Email Type` values. |

The training CLI requires both exact values, and the loader maps only explicitly configured labels. No assumption is made that `spam`, `ham`, `safe`, numeric values, or any guessed spelling is equivalent.

## 11. Data Collection and Provenance

The Kaggle uploader says the data contains email text and type; the HF card says its file is a direct copy of the Kaggle dataset. Original source mailboxes, collection dates, sampling frame, labelers, labeling protocol, and email authenticity are **unknown** from these descriptions. Provenance must not be described as independently verified.

## 12. Preprocessing and Cleaning

The repository loader reads CSV/JSON/JSONL; requires explicit column and label mappings; preserves original source columns, source labels, and source filename; normalizes configured label strings by trim/casefold; rejects missing or blank text, unknown/missing labels, malformed non-string text, and exact text duplicated with conflicting labels; and removes exact duplicate text when enabled. It does not strip URLs, HTML, headers, or email indicators. Invalid-row reports contain source row and reason only, not message content.

No dataset-specific cleaning has been run. Cleaning counts are **Pending verification** after manual download.

## 13. Data-Quality Checks

The loader summary reports input/output counts, missing/empty text, malformed text, unknown labels, conflicting duplicates, exact duplicates, and label distribution. `src/data/validate_dataset.py` reports empty rows, duplicate rows, class counts/imbalance, train/test exact duplicate contamination when splits are supplied, optional group overlap, and row counts with email-address, URL, IPv4, phone-like, and HTML indicators. It preserves the text and does not emit contents.

These are risk indicators, not a proof of safe data, clean annotations, no near-duplicates, or absence of PII. Exact checks do not identify paraphrases or unknown campaign/source overlap.

## 14. Class Distribution

Source-reported total: 18,650. Per-class source counts and cleaned class distribution: **Pending verification**. Run the label-only inspection in Section 6, followed by the validator. Do not infer class balance from the total.

## 15. Privacy and Security Considerations

Email bodies may contain personal names, addresses, phone numbers, account identifiers, quoted conversations, signatures, and other sensitive content. URLs can lead to malicious or tracking resources. Email headers, if present in a downloaded variant, can reveal senders, recipients, routing, or authentication metadata. The dataset source does not document a privacy review or redaction process.

Treat all text and URLs as untrusted. Do not open links, fetch remote resources, execute attachments, or send email text to external services. Do not print full rows or commit samples. The project only counts common sensitive indicators; these checks are incomplete and do not de-identify data.

## 16. Known Biases and Limitations

- The exact source population, time span, language, collection procedure, and class balance are not fully documented; HF metadata tags English but no language audit is available.
- Labels have no published annotation protocol or measured inter-annotator agreement in reviewed source descriptions.
- Data may contain stale patterns, duplicates, source/campaign artifacts, and unintended distribution shortcuts.
- A text-only model may miss sender/domain authentication, rendered HTML behavior, attachments, and context, while learning superficial words or formatting.
- A random split may overstate generalization if messages share campaigns, sources, senders, or time periods.
- A baseline cannot guarantee detection of every phishing email or absence of false positives/negatives.

Dataset-specific duplicate, missing-value, and class-imbalance rates: **Pending verification**.

## 17. Intended and Out-of-Scope Uses

Intended: reproducible academic/educational binary text-classification experiments, subject to license/privacy review.

Out of scope: production blocking decisions without independent validation; sole-factor account, employment, or law-enforcement decisions; claims of comprehensive phishing detection; testing against live mail systems; contacting addresses or opening links found in the data; and redistribution without rights review.

## 18. Train/Test Split Methodology

The baseline uses a seeded 80/20 random split (`random_state=42` by default) and stratifies when each class has at least two examples. Pass `--group-column` for group-held-out splitting when a verified source or campaign identifier is available. Exact duplicate removal occurs before splitting, and the audit can report exact cross-split overlap. The current source schema documents no group or time column, so campaign/source/time independence cannot be established. A random split is not a temporal or source-generalization test.

## 19. Reproducibility Instructions

Follow [README setup and execution instructions](../README.md). Record the dataset source, source revision/version, retrieval date, checksum, exact label strings, loader summary, and split seed in experiment records. Do not record private message bodies. Run tests with `python -m pytest -q`.

## 20. Ethical and Legal Considerations

Use the minimum data necessary, protect local files, restrict access, and remove unnecessary copies. Review applicable privacy, copyright, and dataset terms before processing, publication, or commercial use. LGPL-3.0 on a Kaggle/HF upload does not establish consent or authority over every included message. The project provides no legal advice.

## 21. Candidate Datasets Considered and Reasons for Selection

See [dataset-research.md](dataset-research.md) for the source-by-source comparison. This Kaggle/HF dataset is selected conditionally because it has both stated phishing/safe classes, an explicit declared license, published schema, a reported record count, and easy CSV access. Akilesh G A's Kaggle CSV is a possible alternative with an Apache 2.0 declaration, but its schema, exact labels, count, and provenance are not available in the reviewed metadata. The Naser Alam CC BY-SA 4.0 aggregate is not selected because it conflates some spam with phishing and combines sources with unresolved label and rights compatibility. Nazario is phishing-only; SpamAssassin is spam/ham, not phishing/safe, and leaves sender copyright in place; Enron has no target labels, no explicit license, and significant privacy concerns. None of the three Kaggle listings has fully verified original rights and label quality; ask for permission or further evidence before commercial use or redistribution. The project does not combine these sources.

## 22. References and Attribution

- Cyber Cop, [Phishing Email Detection, Kaggle](https://www.kaggle.com/datasets/subhajournal/phishingemails).
- `zefang-liu`, [phishing-email-dataset, Hugging Face](https://huggingface.co/datasets/zefang-liu/phishing-email-dataset), revision `34085a032c123ca237f314a01a67909cdea35e34`.
- [Dataset metadata API](https://huggingface.co/api/datasets/zefang-liu/phishing-email-dataset).
- Akilesh G A, [Email Phishing Legitimate classifier, Kaggle](https://www.kaggle.com/datasets/akileshga/email-phishing-legitimate-classifier).
- Naser Abdullah Alam, [Phishing Email Dataset, Kaggle](https://www.kaggle.com/datasets/naserabdullahalam/phishing-email-dataset), including its cited [arXiv paper](https://arxiv.org/abs/2405.11619).
- Jose Nazario, [Phishing Corpus](https://monkey.org/~jose/phishing/) and its [CC BY 4.0 license](https://monkey.org/~jose/phishing/LICENSE.txt).
- Apache SpamAssassin, [Public Mail Corpus](https://spamassassin.apache.org/old/publiccorpus/) and [README](https://spamassassin.apache.org/old/publiccorpus/readme.html).
- William W. Cohen / CALO, [Enron Email Dataset](https://www.cs.cmu.edu/~enron/).


Observed source labels: Phishing Email and Safe Email. Every unique label in the downloaded file must still be verified.
