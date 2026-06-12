"""Tunable, declarative thresholds for the insight rules.

Keeping thresholds out of rule logic makes rules config-driven and testable;
changing a cutoff never touches code paths.
"""
from __future__ import annotations

DEFAULT_CONFIG: dict[str, dict[str, float]] = {
    "rule_1_post_type": {"min_ratio": 1.5, "min_n": 5},
    "rule_2_day_of_week": {"min_ratio": 1.3, "min_n": 4},
    "rule_3_cadence": {"freq_drop": 0.30},
    "rule_4_conversion": {"visitor_growth_min": 0.10, "follower_flat_max": 0.02},
    "rule_5_demographic": {"growth_multiple": 2.0, "min_base": 50.0},
    "rule_6_ctr": {"impression_percentile": 0.75, "low_ctr": 0.005},
    "rule_7_post_length": {"max_chars": 1200.0, "min_ratio": 1.5, "min_n": 3.0},
    "rule_8_post_links": {"min_ratio": 1.5, "min_n": 3.0},
    "rule_9_hashtag_count": {"min_ratio": 1.2, "min_n": 4.0},
    "rule_10_tagging": {"min_ratio": 1.2, "min_n": 3.0},
    "rule_11_top_hashtag": {"min_ratio": 1.5, "min_uses": 3.0},
}

