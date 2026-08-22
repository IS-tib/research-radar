"""Unit tests for backend/eval/metrics.py, with hand-computed expected values."""

import math

from eval.metrics import (
    mean_reciprocal_rank,
    ndcg_at_k,
    precision_at_k,
    reciprocal_rank,
)


def test_precision_at_k_basic():
    ranked = ["a", "b", "c", "d", "e"]
    relevant = {"a", "c", "e"}
    # top 5: a(hit) b c(hit) d e(hit) -> 3/5
    assert precision_at_k(ranked, relevant, 5) == 3 / 5
    # top 2: a(hit) b -> 1/2
    assert precision_at_k(ranked, relevant, 2) == 1 / 2


def test_precision_at_k_all_relevant():
    assert precision_at_k(["a", "b"], {"a", "b"}, 2) == 1.0


def test_precision_at_k_none_relevant():
    assert precision_at_k(["a", "b"], {"z"}, 2) == 0.0


def test_precision_at_k_fewer_than_k_ranked():
    # only 2 ranked ids for k=5 -> denominator is 2, not 5
    assert precision_at_k(["a", "b"], {"a"}, 5) == 0.5


def test_precision_at_k_empty_ranking():
    assert precision_at_k([], {"a"}, 5) == 0.0


def test_reciprocal_rank_first_position():
    assert reciprocal_rank(["a", "b", "c"], {"a"}) == 1.0


def test_reciprocal_rank_third_position():
    # first relevant id ("c") is at rank 3 -> 1/3
    assert reciprocal_rank(["a", "b", "c"], {"c"}) == 1 / 3


def test_reciprocal_rank_no_relevant():
    assert reciprocal_rank(["a", "b", "c"], {"z"}) == 0.0


def test_mean_reciprocal_rank():
    # query 1: relevant at rank 1 -> RR=1.0
    # query 2: relevant at rank 2 -> RR=0.5
    # mean = 0.75
    per_query_ranked = [["a", "b"], ["x", "y"]]
    per_query_relevant = [{"a"}, {"y"}]
    assert mean_reciprocal_rank(per_query_ranked, per_query_relevant) == 0.75


def test_ndcg_at_k_perfect_ranking_is_one():
    ranked = ["a", "b", "c"]
    relevant = {"a", "b", "c"}
    assert ndcg_at_k(ranked, relevant, 3) == 1.0


def test_ndcg_at_k_hand_computed():
    # relevant = {b, d}; ranking = a b c d -> relevances [0, 1, 0, 1]
    # DCG = 0/log2(2) + 1/log2(3) + 0/log2(4) + 1/log2(5)
    ranked = ["a", "b", "c", "d"]
    relevant = {"b", "d"}
    dcg = 1 / math.log2(3) + 1 / math.log2(5)
    # ideal: both relevant docs first -> relevances [1, 1, 0, 0]
    idcg = 1 / math.log2(2) + 1 / math.log2(3)
    expected = dcg / idcg
    assert abs(ndcg_at_k(ranked, relevant, 4) - expected) < 1e-9


def test_ndcg_at_k_no_relevant_labels_is_zero():
    assert ndcg_at_k(["a", "b"], set(), 2) == 0.0


def test_ndcg_at_k_worst_ranking_below_best():
    relevant = {"d"}
    best = ndcg_at_k(["d", "a", "b", "c"], relevant, 4)
    worst = ndcg_at_k(["a", "b", "c", "d"], relevant, 4)
    assert best == 1.0
    assert worst < best
