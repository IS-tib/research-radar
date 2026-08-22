"""Standard IR ranking metrics, implemented from their definitions (no
scikit-learn / no ranking library). Every function takes a ranked list of
document ids and a set of relevant ids — binary relevance, matching the
relevant/not-relevant labels in fixtures.py.
"""

import math


def precision_at_k(ranked_ids, relevant_ids, k):
    """Fraction of the top k ranked ids that are relevant.

    If fewer than k ids are ranked, the denominator is the number actually
    ranked (not k) — there's nothing meaningful to divide by otherwise, and the
    eval harness pads every ranker's output to the full candidate set before
    calling this, so in practice this only bites for pathological cases."""
    top_k = ranked_ids[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    return hits / len(top_k)


def reciprocal_rank(ranked_ids, relevant_ids):
    """1 / (rank of the first relevant id), 0 if none of `ranked_ids` is relevant."""
    for i, doc_id in enumerate(ranked_ids, start=1):
        if doc_id in relevant_ids:
            return 1.0 / i
    return 0.0


def _dcg(relevances):
    """Discounted cumulative gain of a list of 0/1 relevances, rank-1 first."""
    return sum(rel / math.log2(i + 2) for i, rel in enumerate(relevances))


def ndcg_at_k(ranked_ids, relevant_ids, k):
    """Normalized DCG@k for binary relevance: DCG@k of the actual ranking
    divided by the DCG@k of the ideal ranking (every relevant id first)."""
    actual = _dcg([1.0 if doc_id in relevant_ids else 0.0 for doc_id in ranked_ids[:k]])
    n_rel = len(relevant_ids)
    ideal_relevances = [1.0] * min(k, n_rel) + [0.0] * max(0, k - n_rel)
    ideal = _dcg(ideal_relevances)
    return actual / ideal if ideal > 0 else 0.0


def mean_reciprocal_rank(per_query_ranked_ids, per_query_relevant_ids):
    """MRR across queries: the mean of reciprocal_rank() over each query."""
    scores = [
        reciprocal_rank(ranked, relevant)
        for ranked, relevant in zip(per_query_ranked_ids, per_query_relevant_ids)
    ]
    return sum(scores) / len(scores) if scores else 0.0
