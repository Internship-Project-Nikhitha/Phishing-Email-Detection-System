# Dataset Card: Phishing Email Detection Baseline

## 1. Dataset Title and Status

**Title:** MeAJOR: Merged email Assets from Joint Open-source Repositories.

**Status: Candidate for further review only; not approved yet for this project's phishing-versus-legitimate training task.** The official Zenodo v2.0 record declares CC BY 4.0 and defines `0 = benign`, `1 = phishing`; however, it does not document the original-label-to-MeAJOR mapping or establish that the benign class means legitimate rather than non-phishing/spam. The record names five source corpora but does not provide source-level rights evidence for each. The paper abstract and release record also report different sample counts. Therefore, do not treat MeAJOR as cleared for training, redistribution, or commercial use until the authors clarify those points and the intended use is reviewed. The Zenodo record and CSV header were checked; no MeAJOR email rows were downloaded or inspected. A separate Cyber Cop Kaggle CSV was supplied locally and audited with the project validator; its results are in Section 23, and it is not recommended as a substitute.

## 2. Project Purpose and Intended Use

The intended task is a baseline binary classifier over email text: phishing versus legitimate/safe. This is for research, education, and evaluation of text-classification methods. It is not a mail gateway, security control, legal determination, or guarantee that an email is safe. Human review and layered defenses remain necessary.

## 3. Dataset Source and Official URL

- Official Zenodo record (version 2.0): https://zenodo.org/records/18471483
- Zenodo record API metadata: https://zenodo.org/api/records/18471483
- Paper: Cardoso et al., *MeAJOR Corpus: A Multi-Source Dataset for Phishing Email Detection*: https://arxiv.org/abs/2507.17978
- CSV file: `meajor_cleaned_preprocessed.csv` on the Zenodo record.

Zenodo describes an open dataset from GECAD, ISEP, Polytechnic of Porto, assembled from TREC-05, TREC-06, TREC-07, the Nazario Phishing Corpus, and Nigerian Fraud. The record offers CSV and compressed Parquet files. Its header includes `body` and `label`, which are structurally compatible with the project loader, but schema compatibility does not establish label or rights compatibility. The source recommends Parquet for more efficient querying and compression.

## 4. Publisher and Citation

The Zenodo record names Francisco Cardoso, João Vitorino, Paulo Mendes, Eva Maia, and Isabel Praça as creators and identifies GECAD, ISEP, Polytechnic of Porto. The record names five source corpora but provides no per-message provenance map or documentation assigning each row to an upstream collection. Cite the dataset record and paper when citing the release. Citation is not a substitute for verifying the permissions applicable to source messages.

Suggested citation: Cardoso, F., Vitorino, J., Mendes, P., Maia, E., & Praça, I. (2026). *MeAJOR: Merged email Assets from Joint Open-source Repositories* (Version 2.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.18471483. Include the article citation listed in the References section when appropriate.

## 5. License and Usage Conditions

Zenodo record metadata declares **Creative Commons Attribution 4.0 International (CC BY 4.0)** for the deposited dataset. The license generally permits sharing and adaptation, including commercially, subject to attribution, a link to the license, noting changes, and no implied endorsement. This verifies the license declared on the Zenodo record; it does **not** independently verify the contributors' authority to license every included email or third-party right. The record aggregates five upstream corpora and supplies no per-message rights manifest. The Nazario corpus has its own CC BY 4.0 notice; terms for the exact TREC and Nigerian Fraud materials included in MeAJOR have not been established from the documentation reviewed. Obtain written confirmation from the MeAJOR authors and check source terms before use. Treat MeAJOR as **not rights-cleared for this project** until that review is complete. This is not a legal determination.

No dataset file is committed here. Preserve attribution and license notices for any permitted use; seek rights clarification or qualified legal advice if upstream rights are material.

## 6. Access and Download Instructions

Only after rights review and project approval, download `meajor_cleaned_preprocessed.csv` from the [official Zenodo record](https://zenodo.org/records/18471483) and save it locally as `data/meajor_cleaned_preprocessed.csv`. The published CSV is about 191 MB; the record also offers a compressed Parquet file. Do not put credentials in repository configuration. No automatic downloader is enabled.

After dependencies are installed, you can check the CSV header without reading its email rows:

```powershell
python -c "import pandas as pd; print(pd.read_csv('data/meajor_cleaned_preprocessed.csv', nrows=0).columns.tolist())"
```

The official CSV header was independently verified on 2026-10-23 using an HTTP range request that read only the first line. To inspect the stored label counts locally without printing messages:

```powershell
python -c "import pandas as pd; print(pd.read_csv('data/meajor_cleaned_preprocessed.csv', usecols=['label'])['label'].value_counts(dropna=False).to_dict())"
```

Counts reveal stored values, not their accuracy. The Zenodo record says `0 = benign` and `1 = phishing`. Do not automatically map `0` to the project's `legitimate` target: the paper describes some input corpora as spam datasets, and the available record does not explain exactly how their original spam/ham labels were mapped into MeAJOR. Ask the authors for the label-construction method and class definition before mapping labels or training. Do not print or commit email text.

## 7. Dataset Version or Retrieval Date

Zenodo record: version 2.0, published February 2026; record API metadata last modified 2026-02-03. Dataset retrieval date for this project: **Not applicable; no corpus downloaded**. Source metadata and CSV header were reviewed on 2026-10-23.

## 8. Dataset Size

For the exact v2.0 downloadable release, use **108,685 as the Zenodo-reported record count**, not as a locally verified row count. Its API lists a CSV file of 191,121,228 bytes (MD5 `aa8f59e96787cbd696c0b650e5400dc9`) and compressed Parquet of 86,278,230 bytes (MD5 `78e397ad8447bcdba5a98097921ba8bd`). The paper abstract reports 135,894 samples. The sources reviewed do not reconcile the difference or identify which processing stage/version the paper count describes. Do not present the counts as equivalent or claim the discrepancy is solved; request clarification from the authors. Actual release row count/checksum, per-label counts, missing rows, duplicates, and retained rows are **Pending verification**.

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

The Zenodo record explicitly defines `0 = benign` and `1 = phishing`. It does not provide a detailed annotation rubric, adjudication procedure, label-error rate, or enough documentation to establish that every benign email is legitimate rather than non-phishing/spam. The paper's source overview includes spam corpora (TREC-05/06/07) and phishing-only corpora, but the release record does not explain how original categories were mapped to the two labels. Do not map either class to project targets for training until the authors confirm the label construction and the project accepts that definition.

| Canonical label | Source concept | Exact stored source label |
|---|---|---|
| `phishing` | Publisher-defined phishing | `1` (documented by Zenodo; annotation process not independently audited) |
| `legitimate` | Legitimate/non-phishing | **Unresolved**; do not assume this is equivalent to source `0 = benign` |

Inspecting the label column and counts can reveal the tokens but cannot establish what those tokens mean. Do not map labels to the project's binary targets based only on a token name or guessed spelling. The training CLI requires exact configured source values, and the loader does not infer mappings; confirm both class meanings before training. In particular, do not assume that spam, ham, safe, numeric values, or any guessed spelling is equivalent to phishing/legitimate.

## 11. Data Collection and Provenance

Zenodo says the corpus combines TREC-05, TREC-06, TREC-07, the Nazario Phishing Corpus, and Nigerian Fraud. The paper's source overview characterizes TREC-05/06/07 as spam corpora, which makes the exact meaning of the resulting `benign` label important to verify. Zenodo describes the messages as anonymized by entity removal, replacing detected entities with bracketed tokens (for example `[EMAIL_ADDRESS]`, `[URL]`, `[NAME]`, and `[PHONE_NUMBER]`); this is the publisher's description, not an independent privacy audit. There is no per-row source mapping in the verified metadata. Original collection dates, sampling and deduplication methods, label mapping, annotation quality, and the consistency/completeness of `source` values are **Pending verification**.

## 12. Preprocessing and Cleaning

The repository loader reads CSV/JSON/JSONL; requires explicit column and label mappings; preserves original source columns, source labels, and source filename; normalizes configured label strings by trim/casefold; rejects missing or blank text, unknown/missing labels, malformed non-string text, and exact text duplicated with conflicting labels; and removes exact duplicate text when enabled. It does not strip URLs, HTML, headers, or email indicators. Invalid-row reports contain source row and reason only, not message content.

The MeAJOR corpus is described as preprocessed, engineered, and anonymized; no dataset-specific cleaning or privacy audit has been run on MeAJOR by this project. A separate supplied Kaggle CSV was processed locally by the project validator; its results are recorded in Section 23. Do not assume upstream preprocessing makes either corpus free of personal information or suitable for all uses.

## 13. Data-Quality Checks

The loader summary reports input/output counts, missing/empty text, malformed text, unknown labels, conflicting duplicates, exact duplicates, and label distribution. `src/data/validate_dataset.py` reports empty rows, duplicate rows, class counts/imbalance, train/test exact duplicate contamination when splits are supplied, optional group overlap, and row counts with email-address, URL, IPv4, phone-like, and HTML indicators. It preserves the text and does not emit contents.

These are risk indicators, not a proof of safe data, clean annotations, no near-duplicates, or absence of PII. Exact checks do not identify paraphrases or unknown campaign/source overlap.

## 14. Class Distribution

For MeAJOR v2.0, the Zenodo-reported total is 108,685; the paper abstract's 135,894 figure is unreconciled. Per-class source counts and cleaned distribution for MeAJOR: **Pending verification**. The distinct supplied Kaggle CSV's observed distribution is reported in Section 23. Do not transfer counts between datasets or describe the paper count as the v2.0 release count.

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

For MeAJOR, dataset-specific duplicate, missing-value, and class-imbalance rates: **Pending verification**. The separate Kaggle CSV audit found missing text and conflicting duplicate labels; see Section 23.

## 17. Intended and Out-of-Scope Uses

Intended, if labels and rights are confirmed: reproducible academic/educational binary text-classification experiments.

Out of scope: production blocking decisions without independent validation; sole-factor account, employment, or law-enforcement decisions; claims of comprehensive phishing detection; testing against live mail systems; contacting addresses or opening links found in the data; and redistribution without rights review.

## 18. Train/Test Split Methodology

The baseline uses a seeded 80/20 random split (`random_state=42` by default) and stratifies when each class has at least two examples. This schema includes `source`, which may be suitable for a group-held-out split only after its values and meanings are verified; pass `--group-column source` only after that check. Exact duplicate removal occurs before splitting, and the audit can report exact cross-split overlap. A random split is not a temporal or source-generalization test.

## 19. Reproducibility Instructions

Follow [README setup and execution instructions](../README.md). MeAJOR is not cleared for training until the label and rights questions below are answered. If the authors confirm an acceptable mapping and the project approves it, record the Zenodo DOI and version, retrieval date, checksum, exact mapping, loader summary, and split seed. Do not record private message bodies. Run tests with `python -m pytest -q`.

## 20. Ethical and Legal Considerations

Use the minimum data necessary, protect local files, restrict access, and remove unnecessary copies. Review applicable privacy, copyright, and dataset terms before processing, publication, or commercial use. A CC BY 4.0 declaration on an aggregate release does not establish consent or authority over every upstream message. The project provides no legal advice.

## 21. Candidate Datasets Considered and Reasons for Selection

See [dataset-research.md](dataset-research.md) and [dataset-candidates.md](dataset-candidates.md) for source comparisons. MeAJOR is a **provisional candidate for further review, not a recommendation to train now**. The Zenodo record gives a usable schema and declares CC BY 4.0, but unresolved source rights, the meaning/mapping of `benign`, and the 108,685-versus-135,894 count difference prevent confident approval for this phishing-versus-legitimate task. Do not map labels, train, redistribute, or use commercially until these gates are addressed. The Cyber Cop Kaggle CSV is also not recommended as-is because of the conflicting-label duplicates and unresolved rights described in Section 23. The project does not combine these sources.

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

## 23. Separately Supplied Cyber Cop Kaggle CSV (Comparison Candidate; Not Approved for Training)

A separate local file, `data/Phishing_Email.csv`, was available for review. The file is ignored by Git via the repository's `data/` ignore rule and is not included in the repository commit. Its 52,034,604-byte size matches the total size reported by the Kaggle dataset API, but no cryptographic checksum was available to establish file identity. Kaggle attributes the dataset to Cyber Cop (`subhajournal`), describes email body text and email type, and declares LGPL-3.0. Its metadata does not document the annotation protocol or establish the uploader's authority over all embedded messages. Review source and content rights before reuse or redistribution.

The local CSV header is an empty first column (an index-like field whose meaning is undocumented), `Email Text`, and `Email Type`. The local row scan found 18,650 data rows and no blank labels:

| Observed `Email Type` | Rows |
|---|---:|
| `Safe Email` | 11,322 |
| `Phishing Email` | 7,328 |

The project validator was run with `Email Text` as text and `Email Type` as label, mapping the exact tokens above. It reported 18,650 input rows; 19 missing/empty text rows; 533 rows whose exact text appears with conflicting labels; and 563 exact duplicate text rows removed. After its invalid-row and duplicate handling, 17,535 rows remained: 10,979 legitimate and 6,556 phishing, for a 1.67:1 class-imbalance ratio. These are results of this project's loader/validator on this local file, not publisher-certified statistics. The high conflicting-label count is a material label-quality concern; do not train on this copy until its cause and treatment have been reviewed. Do not add or commit the CSV.

The validator also found rows containing email-address-like strings (2,598), URL-like strings (4,020), IPv4-like strings (153), phone-like strings (5,312), and HTML (259). These are heuristic indicators, not proof that personal information is present or absent, and do not anonymize the messages. No message text was printed or retained in the documentation. If a rights-reviewed experiment later uses this candidate, first confirm the label definitions and inspect the blank index column's purpose; for this repository's CLI, the text and label columns are `Email Text` and `Email Type`.

## 24. MeAJOR Decision Gates and Author Clarification

The source review resolved what can be established from public records, but it cannot independently grant rights or infer undocumented label construction. Before treating MeAJOR as suitable for this project, send the following questions to the corresponding author listed in the [paper](https://arxiv.org/abs/2507.17978) or use the authors' institutional contact route:

1. Does the Zenodo CC BY 4.0 declaration cover every email body and derived field in this release, including material originating from TREC-05/06/07, the Nazario corpus, and Nigerian Fraud? If not, identify excluded rows/material and each applicable source license or permission.
2. How were each source corpus's original labels mapped to MeAJOR `0 = benign` and `1 = phishing`? Do class-0 examples include spam, unsolicited mail, or other non-legitimate messages? Is there a label guide or adjudication/quality review?
3. Why does the version 2.0 Zenodo record report 108,685 samples while the paper abstract reports 135,894? Which count describes the exact released files, and what processing/version difference explains the other count?
4. Does the documented permission cover the intended use (local academic training, publication of aggregate results, model-weight sharing, redistribution, or commercial use)? Ask separately for each use you intend.

Until those answers and any needed source-term/privacy review are documented, keep MeAJOR marked **not cleared**. Do not reinterpret the `benign` label as `legitimate`, train on it, redistribute it, or make a commercial-use claim. An author response can provide evidence, but legal or institutional review may still be appropriate. This card does not provide legal advice.

Suggested message:

> I am reviewing MeAJOR v2.0 (Zenodo DOI 10.5281/zenodo.18471483) for a phishing-versus-legitimate email classification project. Could you clarify whether CC BY 4.0 covers all included email contents and derived fields, and provide the applicable terms/permissions for each upstream source? How were original source labels mapped to `benign` and `phishing`, and does `benign` exclude spam? Finally, why does the Zenodo release report 108,685 rows while the paper abstract reports 135,894? I will not share email samples. Please also indicate whether your answers cover local model training, publication of aggregate results, model-weight sharing, redistribution, and commercial use.