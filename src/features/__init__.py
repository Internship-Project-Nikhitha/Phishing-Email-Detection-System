"""Hand-built features for phishing detection (sender, URL and text features).

Rules for every feature module (see ``docs/features.md``):

* Features are computed from the text of a cleaned record only.
* Nothing is ever fetched from the network; URLs are just strings.
* Each feature is a small function registered with a ``FeatureRegistry``.
"""
