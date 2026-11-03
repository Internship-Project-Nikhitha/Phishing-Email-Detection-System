"""Tests for src/storage.py."""

from datetime import datetime, timezone

import pytest

from src import storage as st


def result(**overrides):
    base = {
        "label": "phishing",
        "score": 0.91,
        "risk_level": "high",
        "model_version": "v1",
        "indicators": [{"feature": "url_count", "description": "Links.", "contribution": 0.5, "value": 2.0}],
        "warnings": ["Attachment 'a.exe' looks executable."],
    }
    base.update(overrides)
    return base


@pytest.fixture
def conn():
    connection = st.connect(":memory:")
    yield connection
    connection.close()


def test_connect_creates_the_table(conn):
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()

    assert "analysis_history" in [row["name"] for row in tables]


def test_save_analysis_returns_increasing_ids_and_stores_values(conn):
    moment = datetime(2026, 11, 2, 9, 30, tzinfo=timezone.utc)

    first = st.save_analysis(conn, result(), source_name="mail.eml", content_sha256="abc", now=moment)
    second = st.save_analysis(conn, result(label="legitimate", score=0.1, risk_level="low"))

    assert (first, second) == (1, 2)
    row = conn.execute("SELECT * FROM analysis_history WHERE id = 1").fetchone()
    assert row["created_at"] == "2026-11-02T09:30:00+00:00"
    assert row["source_name"] == "mail.eml"
    assert row["content_sha256"] == "abc"
    assert row["score"] == pytest.approx(0.91)


def test_no_email_text_is_stored_unless_a_preview_is_given(conn):
    st.save_analysis(conn, result())
    st.save_analysis(conn, result(), subject_preview="  Hello\n   world " + "x" * 200)

    rows = conn.execute("SELECT subject_preview FROM analysis_history ORDER BY id").fetchall()
    assert rows[0]["subject_preview"] == ""
    assert rows[1]["subject_preview"].startswith("Hello world xxx")
    assert len(rows[1]["subject_preview"]) == st.PREVIEW_LENGTH


def test_save_analysis_rejects_incomplete_results(conn):
    incomplete = result()
    del incomplete["model_version"]

    with pytest.raises(ValueError, match="missing keys.*model_version"):
        st.save_analysis(conn, incomplete)


def test_sql_injection_text_is_stored_as_plain_data(conn):
    evil = "x'); DROP TABLE analysis_history;--"

    st.save_analysis(conn, result(), source_name=evil)

    assert conn.execute("SELECT source_name FROM analysis_history WHERE id = 1").fetchone()[0] == evil
    assert conn.execute("SELECT COUNT(*) FROM analysis_history").fetchone()[0] == 1


# @@PART 2
def test_list_history_is_newest_first_and_decodes_json(conn):
    for score in (0.1, 0.5, 0.9):
        st.save_analysis(conn, result(score=score))

    rows = st.list_history(conn)

    assert [row["score"] for row in rows] == [0.9, 0.5, 0.1]
    assert rows[0]["indicators"][0]["feature"] == "url_count"
    assert rows[0]["warnings"] == ["Attachment 'a.exe' looks executable."]
    assert "indicators_json" not in rows[0]


def test_list_history_limit_and_offset(conn):
    for _ in range(5):
        st.save_analysis(conn, result())

    assert [row["id"] for row in st.list_history(conn, limit=2)] == [5, 4]
    assert [row["id"] for row in st.list_history(conn, limit=2, offset=2)] == [3, 2]
    assert st.list_history(conn, limit=10, offset=10) == []


@pytest.mark.parametrize("limit, offset", [(0, 0), (1001, 0), (10, -1)])
def test_list_history_validates_paging(conn, limit, offset):
    with pytest.raises(ValueError):
        st.list_history(conn, limit=limit, offset=offset)


def test_get_analysis_and_missing_id(conn):
    st.save_analysis(conn, result())

    assert st.get_analysis(conn, 1)["label"] == "phishing"
    assert st.get_analysis(conn, 99) is None


def test_clear_history_removes_everything(conn):
    st.save_analysis(conn, result())
    st.save_analysis(conn, result())

    assert st.clear_history(conn) == 2
    assert st.list_history(conn) == []


def test_file_database_persists_between_connections(tmp_path):
    path = tmp_path / "nested" / "history.db"
    first = st.connect(path)
    st.save_analysis(first, result())
    first.close()

    second = st.connect(path)

    assert len(st.list_history(second)) == 1
    second.close()
