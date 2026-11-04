"""A very large email body must load instead of aborting the whole dataset."""

import json

from src import dataset


def test_loads_a_body_larger_than_the_default_csv_field_limit(tmp_path):
    big_body = "word " * 60_000  # 300,000 characters
    csv_path = tmp_path / "emails.csv"
    csv_path.write_text(
        'subject,body,label\n'
        f'Big,"{big_body}",0\n'
        'Small,"hello there",1\n',
        encoding="utf-8",
    )
    config_path = tmp_path / "dataset.json"
    config_path.write_text(json.dumps({
        "path": str(csv_path),
        "columns": {"subject": "subject", "body": "body", "label": "label"},
        "label_map": {"0": "legitimate", "1": "phishing"},
    }), encoding="utf-8")

    result = dataset.load_dataset(config_path)

    assert len(result.valid) == 2
    assert result.errors == []
    assert len(result.valid[0]["body"]) > 131_072
