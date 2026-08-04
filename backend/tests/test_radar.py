"""
Unit tests for the scoring logic.

These test the PURE functions (no network) — the part that decides how relevant
a paper is. Run them with:

    cd backend
    pip install pytest
    pytest

A green test suite is what makes the CI badge on your README turn "passing".
"""

import radar

TOPICS = {
    "Single-cell": {"weight": 3, "terms": ["scGPT", "single-cell RNA"]},
    "Glioma": {"weight": 2, "terms": ["glioma", "brain tumor"]},
}


def test_score_counts_weighted_matches():
    total, hits = radar.score("scGPT applied to glioma classification", TOPICS)
    # scGPT (w=3) + glioma (w=2) = 5
    assert total == 5
    assert set(hits) == {"Single-cell", "Glioma"}


def test_score_zero_when_no_match():
    total, hits = radar.score("a paper about quantum computing", TOPICS)
    assert total == 0
    assert hits == []


def test_score_is_case_insensitive():
    total, _ = radar.score("SCGPT and BRAIN TUMOR", TOPICS)
    assert total == 5


def test_word_boundaries_avoid_false_positives():
    # "gliomas" should still match "glioma" (suffix), but a random substring won't
    total, hits = radar.score("gliomas were studied", TOPICS)
    assert "Glioma" in hits


def test_dedupe_removes_same_title():
    papers = [
        {"title": "A Great Paper", "source": "arXiv"},
        {"title": "a great paper", "source": "bioRxiv"},  # same title, diff case
        {"title": "Another One", "source": "PubMed"},
    ]
    out = radar.dedupe(papers)
    assert len(out) == 2
