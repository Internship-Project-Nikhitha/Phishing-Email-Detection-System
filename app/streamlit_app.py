"""Streamlit web app for analysts (Member 5).

Run from the project root::

    streamlit run app/streamlit_app.py

Shows the risk score, the label and the warning indicators for an uploaded
.eml/.csv or pasted email, keeps a history and lets you download reports.
Links are never opened and attachments are never executed.

NOTE: this file was written without being executed in the authoring environment
(Streamlit was not installed there). Run it once, fix anything that breaks and
take your screenshots from the running app.
"""

import streamlit as st

from src import bundle, ingest, reports, service, storage
from src.preprocessing import EmailValidationError
from src.settings import load_settings

st.set_page_config(page_title="Phishing Email Analyzer", layout="wide")
settings = load_settings()


@st.cache_resource
def load_model(model_dir: str):
    """Load the trained model once per session."""
    return bundle.load_bundle(model_dir)


def show_result(result: dict) -> None:
    """Display one analysis result."""
    columns = st.columns(3)
    columns[0].metric("Result", result["label"])
    columns[1].metric("Risk level", result["risk_level"])
    columns[2].metric("Score", f"{result['score']:.2f}")
    for warning in result.get("warnings", []):
        st.warning(warning)
    if result["indicators"]:
        st.subheader("Warning indicators")
        st.table([{"Indicator": i["feature"], "Why it matters": i["description"], "Contribution": i["contribution"]} for i in result["indicators"]])
    else:
        st.info("No indicators pointed toward phishing.")
    conn = storage.connect(settings.db_path)
    try:
        analysis = storage.get_analysis(conn, result["id"])
    finally:
        conn.close()
    if analysis:
        st.download_button("Download report (Markdown)", reports.analysis_to_markdown(analysis), f"report_{result['id']}.md")
        st.download_button("Download report (JSON)", reports.analysis_to_json(analysis), f"report_{result['id']}.json")


st.title("Phishing Email Analyzer")
st.caption("Automated assessment only. A person should review results. Links are never opened and attachments are never executed.")

try:
    predictor = load_model(settings.model_dir)
except FileNotFoundError as error:
    st.error(str(error))
    st.stop()

options = {"thresholds": settings.thresholds, "decision_threshold": settings.decision_threshold}
analyze_tab, history_tab = st.tabs(["Analyze", "History"])

with analyze_tab:
    uploaded = st.file_uploader("Upload an .eml or .csv file", type=["eml", "csv"])
    st.write("Or paste an email:")
    subject = st.text_input("Subject")
    sender = st.text_input("Sender")
    body = st.text_area("Body", height=150)
    if st.button("Analyze"):
        conn = storage.connect(settings.db_path)
        try:
            if uploaded is not None:
                data = uploaded.getvalue()
                extension = ingest.validate_upload(uploaded.name, len(data))
                if extension == ".eml":
                    parsed = ingest.parse_eml(data)
                    record = {key: parsed[key] for key in ("subject", "body", "sender")}
                    show_result(service.analyze_and_store(conn, record, predictor, source_name=uploaded.name,
                                                          extra_warnings=parsed["attachment_warnings"], **options))
                else:
                    rows = ingest.parse_csv_upload(data)
                    results, errors = service.analyze_many(rows, predictor, **options)
                    st.write(f"Analyzed {len(results)} emails; {len(errors)} could not be analyzed.")
                    for item in results:
                        storage.save_analysis(conn, item, source_name=uploaded.name, content_sha256=item["content_sha256"])
                    st.table([{"Row": r["index"], "Result": r["label"], "Risk": r["risk_level"], "Score": r["score"]} for r in results])
                    if errors:
                        st.table(errors)
            else:
                show_result(service.analyze_and_store(conn, {"subject": subject, "body": body, "sender": sender},
                                                      predictor, source_name="pasted", **options))
        except (ingest.IngestError, EmailValidationError) as error:
            st.error(str(error))
        finally:
            conn.close()

with history_tab:
    conn = storage.connect(settings.db_path)
    try:
        rows = storage.list_history(conn, limit=200)
    finally:
        conn.close()
    if rows:
        st.dataframe([{k: r[k] for k in ("id", "created_at", "source_name", "label", "risk_level", "score", "model_version")} for r in rows])
        st.download_button("Download history (CSV)", reports.history_to_csv(rows), "history.csv")
    else:
        st.info("No analyses yet.")
