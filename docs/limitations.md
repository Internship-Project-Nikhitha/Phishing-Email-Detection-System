# Dataset and feature limitations

## Dataset scope and labels

The feature statistics in [`../reports/feature_stats.md`](../reports/feature_stats.md)
were computed on the MeAJOR v2.0 training split only. The project configuration
maps source label `0.0` to `legitimate` and `1.0` to `phishing`; the source calls
these classes `benign` and `phishing`. MeAJOR's release used here contains
TREC 2005-2007 spam-corpus messages, so the positive class includes spam and
does not represent verified phishing in general. See
[`dataset-selection.md`](dataset-selection.md) for the documented project-use
decision and remaining provenance, rights, and label questions.

## Feature review

- All sender features are exactly zero in both classes because the selected
  dataset configuration has no sender column. These features cannot provide
  signal on this dataset:
  `sender_has_sender`, `sender_has_domain`, `sender_free_mail`,
  `sender_display_name_mismatch`, `sender_local_digit_count`,
  `sender_domain_length`, `sender_subdomain_count`, `sender_hyphen_count`,
  `sender_suspicious_tld`, `sender_ip_domain`, and `sender_punycode`.
- URL-related means are near zero at the report's three-decimal precision,
  except `url_max_length` (0.001 for phishing and 0.000 for legitimate).
  URL indicators therefore appear sparse in these records and should not be
  treated as broadly available signals.
- `text_subject_length`, `text_exclamations`, `text_uppercase_ratio`,
  `text_urgent_words`, `text_credential_words`, and `text_money_words` have
  higher class means for the mapped phishing class. This is consistent with
  the feature descriptions as aggregate tendencies, not proof that any
  individual email is phishing.
- `text_body_words` and `text_digit_ratio` have similar means across classes.
  `text_fake_reply_prefix` is higher for legitimate records (0.437 versus
  0.079), illustrating that a feature can occur more often in the opposite
  class.
- Several other means display as `0.000`. The report rounds to three decimal
  places, so that value alone does not establish that a feature is always zero.

These are descriptive training-split averages, not model results. No manual
review of individual email contents was performed; feature behavior may differ
on modern email, other languages, or other datasets.
