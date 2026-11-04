"""Tests for scripts/dataset_crosstab.py."""

import json

from scripts import dataset_crosstab


def _config(tmp_path, rows):
    csv_path = tmp_path / "d.csv"
    csv_path.write_text("source,subject,body,label\n" + "\n".join(rows) + "\n", encoding="utf-8")
    config = tmp_path / "c.json"
    config.write_text(json.dumps({
        "path": str(csv_path),
        "columns": {"subject": "subject", "body": "body", "label": "label"},
        "label_map": {"0": "legitimate", "1": "phishing"},
    }), encoding="utf-8")
    return config


def test_crosstab_counts_rows_by_source_and_label_without_email_text(tmp_path):
    config = _config(tmp_path, ["TREC,s1,secret body one,0", "TREC,s2,secret body two,1",
                                "Nazario,s3,secret body three,1", "Nazario,s4,secret body four,1"])

    table = dataset_crosstab.crosstab(config, "source")

    assert "| Nazario | 0 | 2 | 2 |" in table
    assert "| TREC | 1 | 1 | 2 |" in table
    assert "| **all** | 1 | 3 | 4 |" in table
    assert "secret" not in table


def test_main_reports_a_missing_source_column(tmp_path, capsys):
    config = _config(tmp_path, ["TREC,s1,b,0"])

    code = dataset_crosstab.main(["--config", str(config), "--source-column", "nope"])

    assert code == 1
    assert "Column 'nope' not found" in capsys.readouterr().err
