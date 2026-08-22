"""Offline ranking evaluation.

Scores each ranker in radar.RANKERS ("keyword", "tfidf", "bm25") against the
fixed fixture set in fixtures.py and prints a table of Precision@5, Precision@10,
MRR, and NDCG@10, averaged over the 4 topic profiles.

No network access, no external dependencies beyond numpy (already required by
radar.py) — every number below comes from running this script, not from
hand-waving.

Run from backend/:

    python -m eval.evaluate
"""

import radar
from eval.fixtures import LABELS, PAPERS, TOPICS
from eval.metrics import mean_reciprocal_rank, ndcg_at_k, precision_at_k

K_PRECISION = (5, 10)
K_NDCG = 10


def _ranked_ids_for(topic_name, ranker):
    """Full-corpus ranking of PAPERS against a single topic, using `ranker`.

    Recency is excluded (include_recency=False) because it's a freshness
    heuristic, not a relevance judgment, and the fixture set has fixed dates —
    scoring it in would make the eval numbers depend on how old the fixture
    dates happen to be relative to today, which defeats reproducibility.

    "keyword" mode drops non-matching papers instead of scoring them 0, so its
    ranked list can be shorter than the full corpus. The remainder is appended
    in original order so precision/MRR/NDCG@k always see a full-length ranking
    for every ranker — otherwise keyword mode's dropped candidates would just
    never enter the top-k denominator, which flatters it.
    """
    topic = {topic_name: TOPICS[topic_name]}
    ranked = radar.rank(PAPERS, topic, ranker=ranker, include_recency=False)
    ranked_ids = [p["id"] for p in ranked]
    seen = set(ranked_ids)
    ranked_ids += [p["id"] for p in PAPERS if p["id"] not in seen]
    return ranked_ids


def evaluate_ranker(ranker):
    """Per-topic metrics for one ranker, plus the mean across topics."""
    per_topic = {}
    all_ranked, all_relevant = [], []
    for topic_name, relevant in LABELS.items():
        ranked_ids = _ranked_ids_for(topic_name, ranker)
        per_topic[topic_name] = {
            f"P@{k}": precision_at_k(ranked_ids, relevant, k) for k in K_PRECISION
        } | {f"NDCG@{K_NDCG}": ndcg_at_k(ranked_ids, relevant, K_NDCG)}
        all_ranked.append(ranked_ids)
        all_relevant.append(relevant)

    mean = {
        f"P@{k}": sum(per_topic[t][f"P@{k}"] for t in LABELS) / len(LABELS)
        for k in K_PRECISION
    }
    mean[f"NDCG@{K_NDCG}"] = sum(
        per_topic[t][f"NDCG@{K_NDCG}"] for t in LABELS
    ) / len(LABELS)
    mean["MRR"] = mean_reciprocal_rank(all_ranked, all_relevant)
    return per_topic, mean


def main():
    print(f"Fixture set: {len(PAPERS)} papers, {len(TOPICS)} topics, "
          f"{sum(len(v) for v in LABELS.values())} relevance labels\n")

    rows = []
    for ranker in radar.RANKERS:
        _, mean = evaluate_ranker(ranker)
        rows.append((ranker, mean))

    cols = ["P@5", "P@10", "MRR", "NDCG@10"]
    header = f"{'ranker':<10}" + "".join(f"{c:>10}" for c in cols)
    print(header)
    print("-" * len(header))
    for ranker, mean in rows:
        print(f"{ranker:<10}" + "".join(f"{mean[c]:>10.3f}" for c in cols))


if __name__ == "__main__":
    main()
