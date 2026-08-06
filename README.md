# Research Radar

Keeping up with a fast-moving field means checking bioRxiv, arXiv, and PubMed
separately, every week, and still missing things. Research Radar pulls from all
three at once and ranks what's new against the topics you actually care about —
so the reading list comes to you, already sorted.

**Live:** [research-radar-gold.vercel.app](https://research-radar-gold.vercel.app/) · React · FastAPI

![Research Radar](docs/screenshots/app.png)

## Features

- **Three sources, one feed** — bioRxiv, arXiv (q-bio + cs.LG), and PubMed, fetched concurrently.
- **Hybrid relevance ranking** — weighted keyword matching (titles count double), **TF-IDF semantic similarity**, and an exponential **recency boost**, blended into a single transparent *match %*.
- **Cross-source de-duplication** — the same preprint on arXiv *and* bioRxiv (or PubMed) collapses into one card that shows every source it appeared on.
- **Insights strip** — client-side analytics over the current feed: counts by source, top title keywords, and a papers-per-week sparkline.
- **Tune it live** — edit your topics and weights in the UI and re-rank instantly.
- **Filter & sort** — search within results, toggle sources on/off, sort by relevance or date.
- **Save for later** — bookmark papers; they persist in your browser across visits.

## How the ranking works

Each topic is a weight plus a list of terms. Every paper gets three signals, each
normalized to `[0, 1]` and blended into one score (weights `0.55 / 0.30 / 0.15`)
that reads directly as a **match %**:

1. **Keyword** — the sum of weighted whole-word term hits across title and abstract
   (title matches counted twice), normalized against the strongest match in the batch.
2. **Semantic (TF-IDF + cosine)** — the whole fetched corpus is vectorized into a
   TF-IDF space (numpy only, no embeddings or model weights), the topic terms become
   a single weighted query vector, and each paper's cosine similarity to that query
   is measured. This catches on-topic work that uses different vocabulary than your
   exact terms, and lets a strongly-similar paper surface even with no literal hit.
3. **Recency** — an exponential freshness factor that halves every two weeks.

It stays intentionally transparent: each card shows *why* it matched (the topics it
hit) and its keyword/semantic/recency breakdown behind the match %. The TF-IDF space
is built deterministically (sorted vocabulary), so the same corpus always ranks the
same way.

## De-duplication

Records are merged when they share a **DOI** (pulled from the link) or a **normalized
title** (case/punctuation/whitespace stripped). The survivor keeps the union of
sources — so a card can read *bioRxiv · arXiv* — and the longest abstract seen.

## Architecture

`backend/radar.py` is the engine (fetch → score → rank), deliberately free of any
web code so it can run from the API, a script, or the scheduled job that emails me
a weekly digest. `backend/main.py` is a thin FastAPI layer with a short in-memory
cache. The frontend is a single React view; results, filtering, and bookmarks are
all derived client-side from one fetch.

## Run locally

```bash
# backend
cd backend && pip install -r requirements.txt && uvicorn main:app --reload

# frontend (second terminal)
cd frontend && npm install && npm run dev
```

Open the frontend and search a term like `CD3D` or `single-cell` to see it rank.

## Tests

```bash
cd backend && pytest      # keyword scoring, TF-IDF/cosine, and dedup logic
```

## License

MIT
