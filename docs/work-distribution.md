# Work Distribution Document

**Project:** Phishing Email Detection System
**Organization:** Qveto Technologies
**Last updated:** 30 October 2026

## 1. Team

| Role | Name | GitHub Username | Branch / Integration Workflow | Responsibility |
|---|---|---|---|---|
| Team Lead | S.S. Nikhitha | `Internship_Project_Nikhitha` | `main`; creates review and integration branches when required | Integration, preprocessing, content keys, data pipeline, reviews and release |
| Member 1 | Shagufta | `Shagufta580` | Task-specific branches | Dataset research and card, sender features, explanations and final evaluation |
| Member 2 | Shaswata Biswal | `shaswata4-RB` | Task-specific branches | Dataset loader, URL features, history storage, reports and robustness tests |
| Member 3 | Lakshmi Subhaja K | `Lakshmi656` | Task-specific branches | Data quality and deduplication, text features, upload validation and safety tests |
| Member 4 | Mithun M | `Mithun1694` | Task-specific branches | Splitting and leakage checks, feature pipeline, settings, service, API and samples |
| Member 5 | Om Wagh | Not confirmed | Task-specific branch information not consolidated | Metrics, baseline, vectorizers, models, training and web interface |

## 2. Progress (as of 30 October 2026)

| Member | Delivered / Integrated Work | Open Items |
|---|---|---|
| Team Lead | Email preprocessing (`988ed53`); project documentation (`a2c515e`); content keys (`143b8f1`); data preparation pipeline (`3037ead`); feature registry (`4acc688`); split leakage report and fingerprint (`c2aeef4`); hygiene and deduplication fixes (`49bd2dd`, `abe9a5b`). | Final integration and release; dataset decision. |
| Member 1 | Dataset research, candidate comparison, selection assessment, pending-marker checker and privacy-safe dataset audit. Work merged into `main` (`e204e4f`, 27 October). | Final dataset choice with the lead; dataset card numbers after a real run; sender features. |
| Member 2 | Dataset configuration validation (`70dbf0b`, `bb7c349`, 22 October; Member 2's own commits). Dataset reading, CSV loading and fixtures (Days 1â€“2 work) were completed by Member 2, then reviewed and committed by the lead (`86b4908`, 22 October; `0e39f9d`, 26 October). Loader error-reason summary (Day 3) was completed by the lead (`3b23cc4`, 27 October). | URL features, history storage, report exports and robustness tests. |
| Member 3 | Duplicate detection (`c5ad5b7`, 22 October), deduplication with label conflicts (`4b8a9ae`, 23 October), and quality audit (`f03d2f5`, 27 October). The quality-audit work was completed by Member 3, then reviewed and committed by the lead. | Real-data audit report; text features; upload validation and safety tests. |
| Member 4 | Reproducible, leakage-safe splitting (`40f5a39`, 22 October). Split leakage report and fingerprint were completed by the lead (`c2aeef4`, 26 October; merged through `70fd80e`). | Split report on real data; feature pipeline, settings, service and API work. |
| Member 5 | No commits under Member 5's own identity as of 30 October. The lead completed the original three-day metrics and baseline assignment on 27 October: classification metrics (`d8a9b7a`, Days 1â€“2) and TF-IDF baseline (`a6f8eda`, Day 3). The lead separately completed the model-card generator and results guide (`7058187`, 29 October). | Vectorizers, models, model bundle, training script, baseline run script, Streamlit web interface and real-data results. |

## 3. Reassignments and Follow-up

### Member 5 â€“ Om Wagh

- The team lead made repeated requests in the group for members to complete their assigned work.
- On 23 October 2026, the lead specifically followed up with Om in the group and then contacted him privately for clarification.
- After multiple private follow-ups, Om stated that he would complete the assigned work later, but it remained incomplete despite subsequent follow-ups.
- Further follow-up messages from the lead did not receive a response as of 30 October 2026.
- No formal escalation to Qveto or the mentor had been made as of the date of this document.

### Work completed by the lead on behalf of Member 5

The following original Member 5 assignments were completed and committed under the lead's own GitHub identity:

- Classification metrics (`d8a9b7a`, 27 October 2026), covering original Days 1 and 2.
- TF-IDF baseline model (`a6f8eda`, 27 October 2026), covering original Day 3.
- Model-card generator and results guide (`7058187`, 29 October 2026), completed as separate work in the revised schedule.

### Member 2 â€“ Loader error summary

- Member 2 completed the Day 1 and Day 2 work (dataset configuration, reading, CSV loading and fixtures). The lead reviewed and committed it (`86b4908`, 22 October 2026; `0e39f9d`, 26 October 2026).
- Member 2 did not complete the Day 3 loader error-reason summary. The lead completed and committed it on 27 October 2026 (`3b23cc4`).

## 4. Branch and Integration Workflow

- Members used task-specific branches, which could change between assigned tasks or days. There was no single permanent working branch for each member.
- The team lead also created additional branches when required for reviewing, integrating and preparing members' work.
- Completed work was reviewed and integrated into `main`.
- From 30 October 2026, Mithun M (Member 4) also reviews and integrates members' pull requests.
- Commit authorship and integration responsibility are recorded according to the available Git history.

## 5. Rules and Working Guidelines

- Members are expected to work on assigned tasks and submit their completed work for review.
- Changes are reviewed and integrated into `main` after the necessary checks.
- Commit and contribution practices follow the Qveto SOP v1.1.
- Reports must contain only values produced by actual runs.
- Dataset selection and final evaluation should be based on verified data and reproducible results.
