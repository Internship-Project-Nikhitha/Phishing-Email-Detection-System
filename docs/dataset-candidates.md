# Dataset candidate review

This document records publicly described candidates for the phishing-email detection project. Facts below are taken from linked dataset or catalog pages. MeAJOR's Zenodo license declaration and CSV header were checked, but its corpus was not downloaded or audited. A separate Cyber Cop Kaggle CSV was supplied locally and audited without printing email content. **No candidate is currently approved for training:** MeAJOR needs source-rights clarification and documented label mapping, while the Kaggle copy has conflicting-label duplicates and unresolved content rights.

## Candidate comparison

| Candidate | Reported size and format | Labels and content | License status | Main concerns | Current assessment |
|---|---|---|---|---|---|
| [MeAJOR: Merged email Assets from Joint Open-source Repositories](https://zenodo.org/records/18471483) | Zenodo v2.0 reports 108,685 samples; CSV 191,121,228 bytes or compressed Parquet 86,278,230 bytes. The paper abstract reports 135,894. Sources do not explain the difference; use 108,685 only as the v2.0 record's stated count and request clarification. | Official record defines `0 = benign`, `1 = phishing`; says messages were entity-anonymized and lists TREC-05/06/07, Nazario, and Nigerian Fraud as sources. The paper characterizes TREC as spam corpora, but does not establish how source labels map to MeAJOR classes. | Zenodo metadata declares CC BY 4.0 for the deposit. Per-source terms/rights and authority to license each included message are not established by the record. Nazario separately publishes a CC BY 4.0 notice; verify exact terms for every other source and the authors' rights. | Header only: 20 columns including `body`, `source`, `label`. No message rows, source distribution, duplicate counts, or quality audit. `benign` is not proven equivalent to legitimate email. | **Research candidate only—not approved for training, redistribution, or commercial use until rights, labels, and count are clarified.** |
| [Phishing Email Detection](https://www.kaggle.com/datasets/subhajournal/phishingemails) (Cyber Cop; HF mirror [card](https://huggingface.co/datasets/zefang-liu/phishing-email-dataset)) | Kaggle API reports 52,034,604 bytes. Supplied local CSV has 18,650 rows. | Local header: blank/index-like column, `Email Text`, `Email Type`. Observed: 11,322 `Safe Email`, 7,328 `Phishing Email`. | Kaggle and mirror declare LGPL-3.0. The declaration and Kaggle upload do not establish rights in underlying email content. | Validator found 19 empty-text rows, 533 exact-text conflicting-label rows, and 563 exact duplicate texts removed; 17,535 rows remained. Message privacy and annotation methods are not documented. | **Do not train as-is.** Useful for comparison only after resolving label conflicts, intended label meanings, and source/content rights. |
| [Phishing-Email-Detection-Dataset, v2](https://zenodo.org/records/17314806) and its [project repository](https://github.com/Manar-ibr/Phishing-Email-Detection-Dataset) | Merged CSV about 391 MB; balanced CSV about 359 MB | Project documentation describes `body` and `label`; `0 = Safe Email`, `1 = Phishing Email`. The positive class groups spam, scam, and phishing emails together. | The NLM Dataset Catalog lists CC BY 4.0. Check attribution and the rights/conditions of the source corpora before redistributing any data. | Large files; body-only input; broad positive class may label spam/scams as phishing; balanced version is not representative of real-world class prevalence. | **Shortlist, but label definition and size need to be acceptable for the project.** |
| [Phishing validation emails dataset](https://zenodo.org/records/13474746) | 2,000 emails; CSV about 203 KB | Full email text and a label: `Safe Email` or `Phishing Email`; the record says it mixes real-world and artificially generated examples. Sender/subject/body columns are not separately described. | **Unconfirmed:** the visible record does not clearly state a license. Do not use until the authors or record confirm reuse rights. | Small; intended for validating models after training, not as the main training corpus; includes synthetic examples. | **Do not select for training unless license and intended use are clarified.** |
| [Curated Dataset - Phishing Email](https://figshare.com/articles/dataset/Curated_Dataset_-_Phishing_Email/24899952) | About 691 MB; curated from seven repositories | The page describes `Subject` and `Body` for Ling/Enron and `Sender`, `Receiver`, `Date`, `Subject`, `Body`, and `Urls` for other source files. Exact row count and label conventions need to be confirmed from the release and paper. | The Figshare page lists CC BY 4.0. Attribution is required; check underlying corpus terms and the dataset paper before use. | Large, multi-source schema differences; class meaning and row counts need inspection; duplicates and source artifacts likely need auditing. | **Backup candidate pending schema and label verification.** |

## Recommended next checks

1. Ask the corresponding author listed in the MeAJOR paper, or use the authors' institutional contact route, to confirm source-by-source rights, intended-use permissions, label mapping, and the sample-count difference. See Section 24 of `dataset-card.md` for exact questions.
2. Check the original terms for each upstream corpus. Treat MeAJOR as not cleared if any included material or intended use remains unaccounted for.
3. Do not map `benign` to `legitimate` until the authors document what source labels comprise class 0 and the project accepts that definition.
4. Keep the supplied Kaggle CSV out of training unless its 533 conflicting-label rows, source annotation documentation, and rights have been resolved.
5. If use is authorized, inspect aggregate counts and quality locally without printing message contents; never open email links or attachments. Report the exact release/version and don't conflate paper and release counts.

## Sources

- MeAJOR official Zenodo record: https://zenodo.org/records/18471483
- MeAJOR Zenodo metadata API (license and files): https://zenodo.org/api/records/18471483
- MeAJOR paper: https://arxiv.org/abs/2507.17978
- CC BY 4.0 legal code: https://creativecommons.org/licenses/by/4.0/legalcode
- Cyber Cop Kaggle dataset metadata API: https://www.kaggle.com/api/v1/datasets/view/subhajournal/phishingemails
- Cyber Cop Kaggle dataset page: https://www.kaggle.com/datasets/subhajournal/phishingemails
- Hugging Face mirror: https://huggingface.co/datasets/zefang-liu/phishing-email-dataset
- Phishing-Email-Detection-Dataset official Zenodo record: https://zenodo.org/records/17314806
- NLM catalog entry listing CC BY 4.0 for that dataset: https://datasetcatalog.nlm.nih.gov/dataset?q=0002099877
- Phishing validation emails official Zenodo record: https://zenodo.org/records/13474746
- Curated Dataset - Phishing Email Figshare record: https://figshare.com/articles/dataset/Curated_Dataset_-_Phishing_Email/24899952
