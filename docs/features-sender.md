# Sender features: interpretation guide

**Owner: Member 1.** These features use only the sender text in a cleaned email record.
They perform no DNS lookups, network requests, or sender contact. Generate the current
feature descriptions with:

```bash
python -c "from src.features import sender; print(sender.descriptions())"
```

## Feature list

| Feature | What it measures | Why it can matter | Possible false alarm / limitation |
|---|---|---|---|
| `sender_has_sender` | Whether the sender field contains non-whitespace text. | Missing sender metadata can be a useful data-quality signal. | Legitimate forwarded or imported messages may lack sender metadata. |
| `sender_has_domain` | Whether the parsed sender contains a domain. | A missing domain limits sender attribution. | Some valid non-email sender identifiers do not contain a domain. |
| `sender_free_mail` | Whether the domain matches a small set of common public webmail providers. | A free-mail address may be unexpected for an organisation claiming to send official notices. | Many legitimate people and small organisations use public webmail. |
| `sender_display_name_mismatch` | Whether a domain-like token in the display name conflicts with the sender domain. | Brand/domain impersonation can use a trusted name with an unrelated address. | It is heuristic; uncommon TLDs may be missed and ambiguous display names may still look domain-like. |
| `sender_local_digit_count` | Number of digits before the `@` sign. | Long digit sequences can occur in automatically generated or disposable accounts. | Many legitimate usernames contain digits. |
| `sender_domain_length` | Number of characters in the parsed domain. | Unusually long domains can be harder to inspect. | Long domains can be legitimate; length alone is not suspicious. |
| `sender_subdomain_count` | Number of labels above the final two domain labels. | Extra subdomain levels can obscure the organisation's actual domain. | This is a simple label count, not a Public Suffix List calculation. |
| `sender_hyphen_count` | Number of hyphens in the domain. | Brand-like words separated by hyphens can appear in impersonation domains. | Hyphens are valid in ordinary domains. |
| `sender_suspicious_tld` | Whether the final domain label belongs to a small heuristic list. | Some listed suffixes are frequently seen in abuse reports. | TLD reputation changes; legitimate sites also use these suffixes. |
| `sender_ip_domain` | Whether the parsed domain is a valid IP literal. | Direct IP sender domains can be unusual in ordinary business email. | Some internal or automated systems legitimately use IP literals. |
| `sender_punycode` | Whether the domain contains the `xn--` punycode marker. | Punycode can represent internationalized domains and may be used in look-alike attacks. | Internationalized domains are also legitimate. |

## Validation status

Unit tests cover representative positive and negative cases, including missing sender values,
valid and invalid IP literals, display-name mismatch, and domain-shape indicators. The real
project dataset is not committed to this repository, so class-by-class review and feature
distribution checks against real emails remain pending dataset availability.

## Limits

These are weak indicators, not proof that an email is phishing. They must be interpreted
alongside message content and other evidence. Sender text can be forged, and no single
sender feature should determine the classification on its own.
