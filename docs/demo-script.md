# Demo script (about 3 minutes)

Prepare before the demo: a trained model (`python scripts/train.py`), the API or
Streamlit app running, and an empty history (`data/history.db` deleted).

1. **Paste an email.** Paste the text of `samples/phishing_sample.eml`. Point out the label,
   score, risk level and the listed indicators. Say what each indicator means in plain words.
2. **Compare with a normal email.** Paste `samples/legitimate_sample.eml`. Show the lower score.
3. **Attachment warning.** Upload `samples/suspicious_attachment_sample.eml`. Show that the
   attachment is only listed and flagged, never opened.
4. **Batch.** Upload `samples/sample_batch.csv`. Show one result per row.
5. **History and report.** Open the history, export the CSV, open one Markdown report.
6. **Safety.** Mention: text only, no network, no attachment execution, no email body stored.

## If something fails

- No model found: run `python scripts/train.py` first.
- Streamlit not starting: show the API at `/docs` instead.
- Always state honestly what the test results are; read them from `reports/final_evaluation.md`.
