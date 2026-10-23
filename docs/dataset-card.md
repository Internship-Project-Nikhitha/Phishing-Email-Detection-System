# Dataset Card: Phishing Email Detection Baseline

## 1. Dataset Title and Status

**Title:** MeAJOR: Merged email Assets from Joint Open-source Repositories.

**Status:** Recommended as the leading candidate for a local, non-production baseline, subject to verifying that its `benign` class is acceptable as this project's `legitimate` class and reviewing the upstream source-corpus terms. The project repository does not include or redistribute the dataset. The official Zenodo record and license metadata were checked, and the CSV header was read using an HTTP byte-range request; no email rows were inspected or retained. Actual class counts, annotation quality, duplicates, and source-level reuse rights remain **Pending verification**.

## 2. Project Purpose and Intended Use

The intended task is a baseline binary classifier over email text: phishing versus legitimate/safe. This is for research, education, and evaluation of text-classification methods. It is not a mail gateway, security control, legal determination, or guarantee that an email is safe. Human review and layered defenses remain necessary.

## 3. Dataset Source and Official URL

- Official Zenodo record (version 2.0): https://zenodo.org/records/18471483
- Zenodo record API metadata: https://zenodo.org/api/records/18471483
- Paper: Cardoso et al., *MeAJOR Corpus: A Multi-Source Dataset for Phishing Email Detection*: https://arxiv.org/abs/2507.17978
- CSV file: `meajor_cleaned_preprocessed.csv` on the Zenodo record.

Zenodo describes an open dataset from GECAD, ISEP, Polytechnic of Porto, assembled from TREC-05, TREC-06, TREC-07, the Nazario Phishing Corpus, and Nigerian Fraud. The record offers CSV and compressed Parquet files. This card recommends the CSV because its header can be mapped directly to the project's text-and-label loader; the source recommends Parquet for more efficient querying and compression.

## 4. Publisher and Citation

The Zenodo record names Francisco Cardoso, João Vitorino, Paulo Mendes, Eva Maia, and Isabel Praça as creators and identifies GECAD, ISEP, Polytechnic of Porto. The record describes the five source corpora but does not give a record-level provenance map for each email. Cite the dataset record and paper when using it. The paper's cited source records should also be credited where required.

Suggested citation: Cardoso, F., Vitorino, J., Mendes, P., Maia, E., & Praça, I. (2026). *MeAJOR: Merged email Assets from Joint Open-source Repositories* (Version 2.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.18471483. Include the article citation listed in the References section when appropriate.

## 5. License and Usage Conditions

Zenodo record metadata declares **Creative Commons Attribution 4.0 International (CC BY 4.0)**. The license permits sharing and adaptation, including commercially, when its terms are followed: provide appropriate attribution, link to the license, indicate changes, and do not imply endorsement. However, the record aggregates messages from five upstream corpora. Its CC BY declaration does not by itself establish that every upstream message or third-party right is covered by that grant. Review the upstream terms and any privacy/publicity rights before reuse, especially redistribution or commercial use. Public access is not a substitute for that review.

No dataset file is committed here. Preserve attribution and license notices for any permitted use; seek rights clarification or qualified legal advice if upstream rights are material.

## 6. Access and Download Instructions

Download `meajor_cleaned_preprocessed.csv` from the [official Zenodo record](https://zenodo.org/records/18471483) and save it locally as `data/meajor_cleaned_preprocessed.csv`. The published CSV is about 191 MB; the record also offers a compressed Parquet file. Do not put credentials in repository configuration. No automatic downloader is enabled.

After dependencies are installed, you can check the CSV header without reading its email rows:

```powershell
python -c "import pandas as pd; print(pd.read_csv('data/meajor_cleaned_preprocessed.csv', nrows=0).columns.tolist())"
```

The official CSV header was independently verified on 2026-10-23 using an HTTP range request that read only the first line. To inspect the stored label counts locally without printing messages:

```powershell
python -c "import pandas as pd; print(pd.read_csv('data/meajor_cleaned_preprocessed.csv', usecols=['label'])['label'].value_counts(dropna=False).to_dict())"
```

Counts reveal stored values, not their accuracy. The Zenodo record says `0 = benign` and `1 = phishing`; check that the source's benign category meets the project's intended definition of legitimate/non-phishing before mapping labels or training. Do not print or commit email text.

## 7. Dataset Version or Retrieval Date

Zenodo record: version 2.0, published February 2026; record API metadata last modified 2026-02-03. Dataset retrieval date for this project: **Not applicable; no corpus downloaded**. Source metadata and CSV header were reviewed on 2026-10-23.

## 8. Dataset Size

The Zenodo record reports 108,685 samples. Its API lists a CSV file of 191,121,228 bytes (MD5 `aa8f59e96787cbd696c0b650e5400dc9`) and a compressed Parquet file of 86,278,230 bytes (MD5 `78e397ad8447bcdba5a98097921ba8bd`). The paper abstract reports 135,894 samples, which conflicts with the 108,685 samples reported by the version 2.0 Zenodo release; the reason for this difference is **unknown**. These are publisher statements, not an independent file audit. The actual row count and checksum, per-label counts, missing rows, duplicate rows, and retained rows are **Pending verification**; do not treat either reported total as a cleaned-data count.

## 9. File Format and Schema

The Zenodo release contains CSV and compressed Parquet files. The official CSV header was checked without reading message rows; it contains these 20 columns:

| Source column | Type/meaning |
|---|---|---|
| `sender`, `sender_domain` | Sender address and domain; represented in an anonymized corpus. |
| `receiver`, `receiver_domain` | Recipient address and domain; represented in an anonymized corpus. |
| `date` | Message date; exact type/format not audited. |
| `subject` | Subject text. |
| `content_types` | Content-type information; exact encoding not audited. |
| `body` | Email body text; use as the project's text column. |
| `urls` | URL data; exact encoding not audited. |
| `url_count`, `url_length_max`, `url_length_avg`, `url_subdom_max`, `url_subdom_avg` | URL-related features, as named in the header. |
| `attachment_count`, `has_attachments`, `attachment_types` | Attachment-related fields, as named in the header; do not retrieve or execute attachments. |
| `language` | Language field; values and reliability not audited. |
| `source` | Source-corpus field; values and mapping not audited. |
| `label` | Numeric class field; the Zenodo record defines 0 as benign and 1 as phishing. |

Header fields were verified by requesting bytes 0-2047 and reading the first CSV line only. Detailed field types, value formats, completeness, and whether every row is anonymized remain **Pending verification** from a local metadata-only audit. Do not assume `source` is a campaign identifier or that its values fully capture provenance.

## 10. Label Definitions and Mapping

The Zenodo record explicitly defines `0 = benign` and `1 = phishing`. It does not provide a detailed annotation rubric, adjudication procedure, label-error rate, or a definition establishing that every benign email is legitimate rather than merely non-phishing or spam. Accordingly, `1` maps to the project's phishing label as documented by the source; map `0` to project `legitimate` only if that broader semantic equivalence is acceptable and recorded for the experiment.

| Canonical label | Source concept | Exact stored source label |
|---|---|---|
| `phishing` | Phishing | `1` (documented by Zenodo) |
| `legitimate` | Benign/non-phishing | `0` (documented as `benign`; equivalence to legitimate needs project acceptance) |

Inspecting the label column and counts can reveal the tokens but cannot establish what those tokens mean. Do not map labels to the project's binary targets based only on a token name or guessed spelling. The training CLI requires exact configured source values, and the loader does not infer mappings; confirm both class meanings before training. In particular, do not assume that spam, ham, safe, numeric values, or any guessed spelling is equivalent to phishing/legitimate.

## 11. Data Collection and Provenance

Zenodo says the corpus combines TREC-05, TREC-06, TREC-07, the Nazario Phishing Corpus, and Nigerian Fraud. It describes the messages as anonymized by entity removal, replacing detected entities with bracketed tokens (for example `[EMAIL_ADDRESS]`, `[URL]`, `[NAME]`, and `[PHONE_NUMBER]`). This is the publisher's description, not an independent privacy audit. Source-level message provenance, original collection dates, sampling and deduplication methods, labelers, annotation quality, and the consistency of the `source` field are **Pending verification**.

## 12. Preprocessing and Cleaning

The repository loader reads CSV/JSON/JSONL; requires explicit column and label mappings; preserves original source columns, source labels, and source filename; normalizes configured label strings by trim/casefold; rejects missing or blank text, unknown/missing labels, malformed non-string text, and exact text duplicated with conflicting labels; and removes exact duplicate text when enabled. It does not strip URLs, HTML, headers, or email indicators. Invalid-row reports contain source row and reason only, not message content.

The corpus is described as preprocessed, engineered, and anonymized. No dataset-specific cleaning or privacy audit has been run by this project. Do not assume upstream preprocessing makes the data free of personal information or suitable for all uses. Project cleaning counts are **Pending verification** after authorized local inspection.

## 13. Data-Quality Checks

The loader summary reports input/output counts, missing/empty text, malformed text, unknown labels, conflicting duplicates, exact duplicates, and label distribution. `src/data/validate_dataset.py` reports empty rows, duplicate rows, class counts/imbalance, train/test exact duplicate contamination when splits are supplied, optional group overlap, and row counts with email-address, URL, IPv4, phone-like, and HTML indicators. It preserves the text and does not emit contents.

These are risk indicators, not a proof of safe data, clean annotations, no near-duplicates, or absence of PII. Exact checks do not identify paraphrases or unknown campaign/source overlap.

## 14. Class Distribution

Publisher-reported total: 108,685 in the Zenodo v2.0 record and 135,894 in the paper abstract; the discrepancy is unresolved. Per-class source counts and cleaned class distribution: **Pending verification**. Run the label-only inspection in Section 6, then the validator. Do not infer class balance from either total.

## 15. Privacy and Security Considerations

Although the publisher says it applied entity removal, email bodies and structured fields may retain personal or sensitive information, quoted conversations, signatures, and malicious or tracking URLs. The CSV header includes sender, recipient, date, URL, and attachment-related fields. The source record does not establish that anonymization is complete or that privacy risks have been independently reviewed.

Treat all text and URLs as untrusted. Do not open links, fetch remote resources, execute attachments, or send email text to external services. Do not print full rows or commit samples. The project only counts common sensitive indicators; these checks are incomplete and do not de-identify data.

## 16. Known Biases and Limitations

- The dataset aggregates historical corpora and its exact source-level population, sampling, language distribution, and time coverage have not been independently verified.
- The paper abstract reports 135,894 samples, while the Zenodo v2.0 record reports 108,685; this count discrepancy is unresolved.
- The publisher's `benign` label is not defined in enough detail to prove it means legitimate email rather than non-phishing/spam; annotation protocol and measured agreement are not reported in the record.
- The five-source description and the `source` column need to be reconciled against actual values and source records; cross-source or campaign coverage cannot be inferred from the schema alone.
- Anonymization can remove identity cues that real-world phishing systems may use; it may also be incomplete or introduce artifacts.
- The record includes engineered URL and attachment-related fields; exclude them if the experiment is intended to evaluate body text only, and check for target leakage before using any engineered feature.
- Data may contain stale patterns, duplicates, source/campaign artifacts, and unintended distribution shortcuts.
- A text-only model may miss sender/domain authentication, rendered HTML behavior, attachments, and context, while learning superficial words or formatting.
- A random split may overstate generalization if messages share campaigns, sources, senders, or time periods.
- A baseline cannot guarantee detection of every phishing email or absence of false positives/negatives.

Dataset-specific duplicate, missing-value, and class-imbalance rates: **Pending verification**.

## 17. Intended and Out-of-Scope Uses

Intended, if labels and rights are confirmed: reproducible academic/educational binary text-classification experiments.

Out of scope: production blocking decisions without independent validation; sole-factor account, employment, or law-enforcement decisions; claims of comprehensive phishing detection; testing against live mail systems; contacting addresses or opening links found in the data; and redistribution without rights review.

## 18. Train/Test Split Methodology

The baseline uses a seeded 80/20 random split (`random_state=42` by default) and stratifies when each class has at least two examples. This schema includes `source`, which may be suitable for a group-held-out split only after its values and meanings are verified; pass `--group-column source` only after that check. Exact duplicate removal occurs before splitting, and the audit can report exact cross-split overlap. A random split is not a temporal or source-generalization test.

## 19. Reproducibility Instructions

Follow [README setup and execution instructions](../README.md). Record the Zenodo DOI and version, retrieval date, checksum, exact label mapping (`1` to phishing; `0` to benign, if accepted as legitimate), loader summary, and split seed in experiment records. Do not record private message bodies. Run tests with `python -m pytest -q`.

## 20. Ethical and Legal Considerations

Use the minimum data necessary, protect local files, restrict access, and remove unnecessary copies. Review applicable privacy, copyright, and dataset terms before processing, publication, or commercial use. A CC BY 4.0 declaration on an aggregate release does not establish consent or authority over every upstream message. The project provides no legal advice.

## 21. Candidate Datasets Considered and Reasons for Selection

See [dataset-research.md](dataset-research.md) and [dataset-candidates.md](dataset-candidates.md) for source comparisons. MeAJOR is recommended as the leading candidate because its official Zenodo record provides a CC BY 4.0 declaration, documented `0 = benign` and `1 = phishing` labels, a reported size, and an inspectable email-text schema. It is not an unconditional recommendation: `benign` may not mean legitimate, upstream source rights must be reviewed, and the data has not been independently audited. Do not train until the project explicitly accepts the label mapping and completes rights review. Do not claim commercial or redistribution permission for every underlying message solely from the aggregate record license. Other candidates have less suitable labels, weaker license/schema evidence, or greater integration/privacy concerns. The project does not combine these sources.

## 22. References and Attribution

- Cardoso, F., Vitorino, J., Mendes, P., Maia, E., & Praça, I., [MeAJOR: Merged email Assets from Joint Open-source Repositories, Zenodo, version 2.0](https://zenodo.org/records/18471483), DOI: [10.5281/zenodo.18471483](https://doi.org/10.5281/zenodo.18471483).
- [Zenodo record API metadata](https://zenodo.org/api/records/18471483) and [file metadata](https://zenodo.org/api/records/18471483/files).
- Cardoso et al., [MeAJOR Corpus: A Multi-Source Dataset for Phishing Email Detection](https://arxiv.org/abs/2507.17978), arXiv:2507.17978.
- [Creative Commons Attribution 4.0 International legal code](https://creativecommons.org/licenses/by/4.0/legalcode) and [license deed](https://creativecommons.org/licenses/by/4.0/).
- Akilesh G A, [Email Phishing Legitimate classifier, Kaggle](https://www.kaggle.com/datasets/akileshga/email-phishing-legitimate-classifier).
- Naser Abdullah Alam, [Phishing Email Dataset, Kaggle](https://www.kaggle.com/datasets/naserabdullahalam/phishing-email-dataset), including its cited [arXiv paper](https://arxiv.org/abs/2405.11619).
- Jose Nazario, [Phishing Corpus](https://monkey.org/~jose/phishing/) and its [CC BY 4.0 license](https://monkey.org/~jose/phishing/LICENSE.txt).
- Apache SpamAssassin, [Public Mail Corpus](https://spamassassin.apache.org/old/publiccorpus/) and [README](https://spamassassin.apache.org/old/publiccorpus/readme.html).
- William W. Cohen / CALO, [Enron Email Dataset](https://www.cs.cmu.edu/~enron/).