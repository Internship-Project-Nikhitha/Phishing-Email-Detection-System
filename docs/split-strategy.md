# Split strategy

How `src/splitting.py` divides the data, and why. (Member 4)

## Goals

1. **No leakage.** The same email (or a near copy) must never be in two splits.
2. **Same balance everywhere.** Train, validation and test should each keep roughly the dataset's phishing/legitimate proportions.
3. **Reproducible.** The same seed always gives the same split.
4. **Test set stays untouched** until the final evaluation.

## Steps

1. Duplicates and records with conflicting labels are removed first (`quality.deduplicate`; the scripts use the near-duplicate level).
2. Records are grouped by content key (`src/keys.py`). Everything with the same key is one group and always moves together.
3. Each label is handled separately. Its groups are sorted, shuffled with the seed, then placed one by one into whichever split is furthest below its target share.
4. Default ratios are 70% train, 15% validation, 15% test (configurable, must be positive and add up to 1).
5. `splitting.audit_split_leakage` re-checks that no key appears in two splits; `data_prep.prepare_splits` stops with an error if it does.
6. `splitting.fingerprint_split(...)` (stored as `split_fingerprint`) is saved with the trained model. `scripts/evaluate.py` refuses to run if the rebuilt splits differ, which proves the split (and so the test set) was not changed.

## How each split is used

| Split | Used for |
|---|---|
| train | fitting models and vocabularies (TF-IDF, scalers) |
| validation | choosing parameters and the best model |
| test | one final evaluation (`scripts/evaluate.py`) |

## Known limits

- Near-duplicate detection uses text templates (URLs, digits and punctuation ignored). Paraphrased copies of one email are not detected.
- Groups cannot be split, so very large groups make the ratios slightly inexact.
- A random split can be optimistic if the dataset mixes sources by time; if timestamps are available, a time-based split should be considered and documented.
- Each label needs at least 3 distinct emails to fill all three splits.
