# Data folder

**Do not commit raw email data.** Phishing and legitimate email datasets can
contain real names, addresses and links, and their licenses may not allow
redistribution.

| Path            | Purpose                                              | Committed? |
|-----------------|------------------------------------------------------|------------|
| `data/README.md`| This file                                            | Yes        |
| `data/raw/`     | The dataset file(s) you downloaded yourself          | **No** (git-ignored) |
| `data/processed/` | Any generated intermediate data                    | **No** (git-ignored) |
| `data/history.db` | Local analysis history created by the app          | **No** (git-ignored) |

## How to set up the dataset locally

1. Read `docs/dataset-selection.md` to see which dataset the team chose and
   where to download it.
2. Download it yourself and save it as the file named in `configs/dataset.json`
   (the `path` field), normally inside `data/raw/`.
3. Check that it loads:

   ```
   python -c "from src.dataset import load_dataset; r = load_dataset('configs/dataset.json'); print(len(r.valid), 'valid rows,', len(r.errors), 'rejected')"
   ```

## Test data

Automated tests use a small **synthetic** (made-up) dataset in
`tests/fixtures/`. It uses reserved example domains only and contains no real
people or real links. It is for testing code, never for reporting results.

## Safe handling

- Treat every URL in the data as plain text. Never open links or attachments.
- Reports must contain statistics and record IDs, not copies of email bodies.
- Never put credentials or personal data in this repository.
