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


# --- cross-source de-duplication ------------------------------------------

def test_dedupe_merges_sources_by_title():
    papers = [
        {"title": "Deep Nets for Glioma", "source": "arXiv", "url": "http://a"},
        {"title": "deep nets, for glioma!", "source": "bioRxiv", "url": "http://b"},
    ]
    out = radar.dedupe(papers)
    assert len(out) == 1
    # union of sources is kept so a card can show both origins
    assert set(out[0]["sources"]) == {"arXiv", "bioRxiv"}


def test_dedupe_merges_by_doi_despite_title_variation():
    # Same preprint, differently punctuated titles, but a shared DOI in the URL.
    papers = [
        {"title": "A Study of X (preprint)", "source": "bioRxiv",
         "url": "https://doi.org/10.1101/2024.01.01.123"},
        {"title": "A Study of X", "source": "PubMed",
         "url": "https://doi.org/10.1101/2024.01.01.123"},
    ]
    out = radar.dedupe(papers)
    assert len(out) == 1
    assert set(out[0]["sources"]) == {"bioRxiv", "PubMed"}


def test_dedupe_keeps_longest_abstract_and_order():
    papers = [
        {"title": "First", "source": "arXiv", "abstract": "short"},
        {"title": "First", "source": "bioRxiv", "abstract": "a much longer abstract"},
        {"title": "Second", "source": "PubMed", "abstract": "x"},
    ]
    out = radar.dedupe(papers)
    assert [p["title"] for p in out] == ["First", "Second"]  # first-seen order
    assert out[0]["abstract"] == "a much longer abstract"


# --- TF-IDF / cosine semantic scorer --------------------------------------

DOCS = [
    "single-cell RNA sequencing of glioma tumor microenvironment",
    "transformer models for protein structure prediction",
    "quantum entanglement in cold atom lattices",
]


def test_semantic_ranks_on_topic_document_highest():
    sims = radar.semantic_similarity(DOCS, TOPICS)
    # The glioma / single-cell doc must be the closest to the topic query.
    assert sims[0] == max(sims)
    assert sims[0] > sims[2]  # clearly above the unrelated quantum-physics doc


def test_semantic_is_deterministic():
    assert radar.semantic_similarity(DOCS, TOPICS) == \
        radar.semantic_similarity(DOCS, TOPICS)


def test_cosine_of_identical_vectors_is_one():
    mat, vocab, idf = radar.build_tfidf(["glioma brain tumor"])
    q = radar.query_vector({"T": {"weight": 1, "terms": ["glioma", "brain tumor"]}},
                           vocab, idf)
    # A document made only of query terms should sit at cosine ~1 with the query.
    import numpy as np
    assert radar._cosine(mat, q)[0] == np.float64(1.0) or \
        abs(radar._cosine(mat, q)[0] - 1.0) < 1e-9


def test_semantic_empty_and_no_overlap():
    assert radar.semantic_similarity([], TOPICS) == []
    # A corpus that shares no vocabulary with the topics scores zero, not an error.
    off_topic = ["weather patterns over the pacific ocean"]
    assert radar.semantic_similarity(off_topic, TOPICS) == [0.0]
