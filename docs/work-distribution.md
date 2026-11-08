# Work Distribution Document

**Project:** Phishing Email Detection System
**Organization:** Qveto Technologies
**Last updated:** 8 November 2026

## 1. Team

| Role | Name | GitHub Username | Branch / Integration Workflow | Responsibility |
|---|---|---|---|---|
| Team Lead | S.S. Nikhitha | `Internship_Project_Nikhitha` | `main`; creates review and integration branches when required | Integration, preprocessing, content keys, data pipeline, reviews and release |
| Member 1 | Shagufta | `Shagufta580` | Task-specific branches | Dataset research and card, explanations, feature report, limitations and final evaluation script |
| Member 2 | Shaswata Biswal | `shaswata4-RB` | Task-specific branches | Dataset loader, URL features, history storage, reports, robustness tests and setup guide |
| Member 3 | Lakshmi Subhaja K | `Lakshmi656` | Task-specific branches | Data quality and deduplication, text features, upload validation and safety tests |
| Member 4 | Mithun M | `Mithun1694` | Task-specific branches | Splitting and leakage checks, feature pipeline, settings, analysis service, benchmark and API |
| Member 5 | Om Wagh | `omwagh8288` | Task-specific branches | Metrics, baseline, vectorizers, models, training, model card and web interface |

## 2. Project status (as of 8 November 2026)

- All planned components are integrated into `main` and tagged `v1.0` (commit `7d7e5d9`).
- The full test suite passes (636 tests), also from a clean clone with a fresh virtual environment (`reports/test_log.txt`).
- The dataset is MeAJOR v2.0, selected by the lead for restricted educational use with documented limitations (`docs/dataset-selection.md`, `docs/dataset-card.md`).
- Real-data reports are committed: dataset audit and source labels, split summary, baseline metrics, model comparison, feature statistics and the final evaluation.
- The final evaluation on the held-out test split was run once, after training and model selection were finished (`reports/final_evaluation.md`, commit `f90fa6f`).
- The FastAPI service and the Streamlit web app were started and tried with the sample emails.

## 3. Progress by member

Commit hashes are from the repository history. "Done by lead" means the assigned work was completed by the lead and committed under the lead's GitHub identity. "Placed by lead" means the member's own code was reviewed against the plan and committed to `main` by the lead.

| Member | Work by the member | Work completed by the lead on the member's behalf |
|---|---|---|
| Team Lead | Email preprocessing (`988ed53`); project documentation (`a2c515e`); content keys (`143b8f1`); data preparation pipeline (`3037ead`); feature registry (`4acc688`); split leakage report and fingerprint (`c2aeef4`); hygiene and deduplication fixes (`49bd2dd`, `abe9a5b`); contract and integration tests (`d4377a0`); interfaces and README (`dc1801d`); demo script, presentation outline and evidence index (`0186c7b`); test log and completed evidence index (`abe89ee`); web app fixes found while running it (`389355d`, `7d7e5d9`); release tag `v1.0`. | See the rows below. |
| Member 1 (Shagufta) | Dataset research, candidate comparison, selection assessment, pending-marker checker and dataset audit (merged `e204e4f`, 27 October); risk levels and explanation of top indicators (`833d9c4`, 1 November); feature statistics report script (`6fde013`, 1 November); final evaluation script (`d2cb8fc`, 5 November, placed as `976c5d9`); feature statistics from the real training split (`aa1dbd1`, 7 November, merged with her dataset and limitations documents). | Dataset decision with fixes for very large email bodies and float labels (`3c64846`, 4 November); dataset card with real numbers (`89fb194`, 4 November); running the final evaluation and committing its reports (`f90fa6f`, 8 November). |
| Member 2 (Shaswata) | Dataset configuration validation (`70dbf0b`, `bb7c349`, 22 October); dataset reading, CSV loading and fixtures (Days 1-2, reviewed and committed by the lead as `86b4908`, `0e39f9d`); URL features (`299b2cd`, 31 October); robustness tests (`c50860a`, 3 November); setup guide and `.env.example` (placed as `c851322`, 5 November). | Loader error-reason summary (`3b23cc4`, 27 October); privacy-safe analysis history storage (`680ea0b`, 1 November); report exports with CSV formula protection (`a4d576a`, 2 November); documentation of what the history stores (`98fdc0b`, 3 November). |
| Member 3 (Lakshmi) | Duplicate detection (`c5ad5b7`, 22 October); deduplication with label conflicts (`4b8a9ae`, 23 October); quality audit (`f03d2f5`, 27 October); text features (merged `617e984`, 31 October); safe upload validation and email parsing (placed as `fd60268`, 1 November); analysis input preparation (placed as `8886f26`, 2 November). | Dataset audit report script (`5843f66`, 3 November); real-data audit and source-label reports (`389d8ea`, 4 November); safe sample emails, safety tests and safety notes (`0964c94`, 5 November). |
| Member 4 (Mithun) | Reproducible, leakage-safe splitting (`40f5a39`, 22 October); feature pipeline (merged `861021c`, 1 November); settings (merged `b234953`, 2 November); analysis service (merged `dee9396`, 3 November); benchmark (merged `996f6c3`, 4 November); REST API, API tests and API document (placed as `0ea670c`, 5 November). | Split report helpers and split script (`2c2995b`, 1 November); real-data split summary (`54b3822`, 5 November). |
| Member 5 (Om) | Training script and its test (placed as `bbc40a4`, 5 November); Streamlit web application (placed as `66173f9`, 7 November); model card generated from the real run (placed as `1ef13e2`, 8 November); model bundle with integrity check (placed as `7f1db06`, 4 November). | Classification metrics (`d8a9b7a`, 27 October); TF-IDF baseline (`a6f8eda`, 27 October); model-card generator and results guide (`7058187`, 29 October); baseline run script (`9adcefc`, 1 November); TF-IDF and engineered-feature vectorizers (`bacd249`, 2 November); candidate models with validation tuning (`7a72352`, 3 November); running the training script on the real data, real model comparison and baseline reports (`e4879cc`, `54b3822`, 5 November). |

## 4. Reassignments and follow-up

### Member 5 - Om Wagh

- The team lead made repeated requests in the group for members to complete their assigned work.
- On 23 October 2026, the lead specifically followed up with Om in the group and then contacted him privately for clarification.
- The assigned work remained incomplete through 30 October despite these follow-ups, so the lead completed the original Member 5 assignments (see the table above) so that the project could proceed.
- From early November, Om started pushing his own work to his branch (`member-5-baseline-models-ui`): the training script and its test (4 November), the Streamlit web application (7 November) and the generated model card (7 November). The lead reviewed these files and committed them to `main` (`bbc40a4`, `66173f9`, `1ef13e2`). His separate baseline files on that branch overlapped with work already in `main` and were not merged.

### Member 2 - Loader error summary

- Member 2 completed the Day 1 and Day 2 work (dataset configuration, reading, CSV loading and fixtures). The lead reviewed and committed it (`86b4908`, 22 October 2026; `0e39f9d`, 26 October 2026).
- Member 2 did not complete the Day 3 loader error-reason summary. The lead completed and committed it on 27 October 2026 (`3b23cc4`).

### Other steps completed by the lead

Where a member's daily step was not pushed by the end of its day, the lead completed it so the project would stay on schedule and the team would keep committing every day. These steps are listed in the "Work completed by the lead on the member's behalf" column above.

## 5. Branch and integration workflow

- Members used task-specific branches, which could change between assigned tasks or days. There was no single permanent working branch for each member.
- The team lead also created additional branches when required for reviewing, integrating and preparing members' work.
- Completed work was reviewed and integrated into `main`. Before each integration, branch files were compared with the plan, merged in a scratch copy of the repository, and the full test suite was run.
- Where a branch contained unrelated or stale files, only the intended files were taken into `main`.
- Integration into `main` was carried out by the team lead.
- Commit authorship and integration responsibility are recorded according to the available Git history.

## 6. Rules and working guidelines

- Members are expected to work on assigned tasks and submit their completed work for review.
- Changes are reviewed and integrated into `main` after the necessary checks.
- Commit and contribution practices follow the Qveto SOP v1.1.
- Reports must contain only values produced by actual runs.
- The test split is used once, for the final evaluation only.
- Raw datasets, model files and local databases are not committed.
- Dataset selection and final evaluation are based on verified data and reproducible results.
