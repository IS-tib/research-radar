"""Unit tests for the BM25 implementation in radar.py."""

import radar

TOPIC = {"T": {"weight": 1, "terms": ["glioma"]}}


def test_term_frequency_saturates():
    """BM25's whole point versus raw term counting: a term appearing 10 times
    should score well above a single occurrence, but nowhere close to 10x —
    the marginal value of each extra occurrence shrinks."""
    once = "a study of glioma progression in adult patients over five years"
    ten_times = "glioma glioma glioma glioma glioma glioma glioma glioma glioma glioma"
    scores = radar.bm25_scores([once, ten_times], TOPIC)
    assert scores[1] > scores[0]  # more occurrences still scores higher...
    assert scores[1] < 10 * scores[0]  # ...but far from linearly


def test_longer_documents_are_length_normalized():
    """Two documents with the same single occurrence of the query term: the
    one padded with a lot of unrelated filler text should score lower, because
    BM25 penalizes documents longer than the corpus average."""
    short = "glioma outcomes in a small cohort"
    padding = " ".join(["unrelated filler word"] * 40)
    long_doc = "glioma outcomes in a small cohort " + padding
    scores = radar.bm25_scores([short, long_doc], TOPIC)
    assert scores[0] > scores[1]


def test_zero_for_no_vocabulary_overlap():
    scores = radar.bm25_scores(["a paper about quantum computing hardware"], TOPIC)
    assert scores == [0.0]


def test_empty_corpus():
    assert radar.bm25_scores([], TOPIC) == []


def test_is_deterministic():
    docs = [
        "glioma classification from MRI",
        "single-cell RNA sequencing of glioma",
        "an unrelated paper about robotics",
    ]
    assert radar.bm25_scores(docs, TOPIC) == radar.bm25_scores(docs, TOPIC)


def test_more_query_term_hits_scores_higher_than_fewer():
    topics = {"T": {"weight": 1, "terms": ["glioma", "IDH mutation"]}}
    both_terms = "IDH mutation status in glioma patients"
    one_term = "glioma patients treated with standard chemoradiation"
    scores = radar.bm25_scores([both_terms, one_term], topics)
    assert scores[0] > scores[1]


def test_topic_weight_scales_contribution():
    """A heavier topic should pull its matching documents up relative to a
    lighter topic with an equally strong match."""
    docs = ["glioma study", "connectomics study"]
    heavy_glioma = {
        "Glioma": {"weight": 5, "terms": ["glioma"]},
        "Neuro": {"weight": 1, "terms": ["connectomics"]},
    }
    scores = radar.bm25_scores(docs, heavy_glioma)
    assert scores[0] > scores[1]


def test_build_bm25_vocab_is_sorted():
    _, vocab, _, _, _ = radar.build_bm25(["zebra apple mango", "banana"])
    assert list(vocab.keys()) == sorted(vocab.keys())
