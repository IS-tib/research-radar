# Research Radar

Keeping up with a fast-moving field means checking bioRxiv, arXiv, and PubMed
separately, every week, and still missing things. Research Radar pulls from all
three at once and ranks what's new against the topics you actually care about —
so the reading list comes to you, already sorted.

**Live:** [research-radar-gold.vercel.app](https://research-radar-gold.vercel.app/) · React · FastAPI

![Research Radar](docs/screenshots/app.png)

## Features

- **Three sources, one feed** — bioRxiv, arXiv (q-bio + cs.LG), and PubMed, fetched concurrently.
- **Relevance ranking** — weighted keyword matching (titles count double) blended with an exponential **recency boost**, so fresh, on-topic work rises to the top.
- **Tune it live** — edit your topics and weights in the UI and re-rank instantly.
- **Filter & sort** — search within results, toggle sources on/off, sort by relevance or date.
- **Save for later** — bookmark papers; they persist in your browser across visits.

## How the ranking works

Each topic is a weight plus a list of terms. A paper's score is the sum of
weighted term hits across its title and abstract (title matches counted twice),
multiplied by a freshness factor that halves every two weeks. Zero-score papers
are dropped; the rest sort by the blended score. It's intentionally transparent —
every result shows *why* it matched.

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
cd backend && pytest      # scoring + dedup logic
```

## License

MIT
