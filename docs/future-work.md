# Recommended next steps

Each item answers a limitation that is already documented in `limitations.md`,
`dataset-card.md` or `reports/final_evaluation.md`.

| Limitation we found | Recommended next step |
|---|---|
| The data is TREC 2005-2007 mail and its positive class includes spam | Test on a newer, verified phishing corpus and report the results separately. Do not mix the two without checking labels |
| No sender or header columns, so all sender features are zero | Use or build a dataset with headers (From, Reply-To, authentication results) so sender features can carry signal |
| No phishing category or source column | Collect category labels so performance can be reported per category |
| One split and one seed | Repeat with several seeds or cross-validation and report the spread |
| The middle score bins are small and noisy | Gather more examples near the decision boundary and re-check calibration; consider calibrating the scores |
| Only linear and tree models were compared | Try a small transformer model and compare it on the same split |
| Rights to the dataset's emails are unresolved | Get a written answer from the data owners, or switch to a corpus with clear terms, before any wider use |
| The API has no login and keeps a local SQLite history | Add authentication, rate limits and a retention period before putting it on a network |
| Results can drift as mail changes | Track false positives and false negatives from real use and retrain on a schedule |
| The tool ranks and explains only | Keep a person in the loop; add an analyst feedback button so corrections can be collected |

## Out of scope for this release

Fetching links, detonating attachments, and automatic blocking or deleting of mail were left out on purpose
(see `safety.md`).
