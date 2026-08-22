"""FastAPI server exposing the Research Radar ranking engine.

Run locally:  uvicorn main:app --reload  (docs at /docs)
"""

import hashlib
import json
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import radar
from cache import TTLCache

HERE = os.path.dirname(os.path.abspath(__file__))
TOPICS_PATH = os.path.join(HERE, "topics.json")

# Seconds a scan result stays cached — avoid re-hitting the paper APIs on every
# click. Configurable via env var so a deployment can tune it without a code
# change; ?refresh=1 on /api/papers bypasses a cached hit for one request.
CACHE_TTL = int(os.environ.get("RADAR_CACHE_TTL", "600"))

# The cache stores the full ranked set (FETCH_TOP items) rather than whatever
# `top` a particular request asked for, so bumping `top` in the UI doesn't force
# a refetch — it's just a different slice of an already-cached scan.
FETCH_TOP = 100

app = FastAPI(title="Research Radar API", version="2.1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_cache = TTLCache(CACHE_TTL)


def _topics_key(topics):
    """Short, stable hash of the topics dict for use as a cache key component."""
    blob = json.dumps(topics, sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()[:16]


def load_topics():
    with open(TOPICS_PATH) as f:
        return json.load(f)


def save_topics(topics):
    with open(TOPICS_PATH, "w") as f:
        json.dump(topics, f, indent=2)


class Topics(BaseModel):
    topics: dict


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "research-radar"}


@app.get("/api/topics")
def get_topics():
    return load_topics()


@app.put("/api/topics")
def put_topics(body: Topics):
    for name, cfg in body.topics.items():
        if not isinstance(cfg.get("terms"), list):
            raise HTTPException(400, f"topic '{name}' needs a 'terms' list")
    save_topics(body.topics)
    _cache.clear()
    return {"saved": True, "topics": body.topics}


@app.get("/api/papers")
def papers(days: int = 7, top: int = 25, ranker: str = "tfidf", refresh: bool = False):
    days = max(1, min(days, 60))
    top = max(1, min(top, 100))
    if ranker not in radar.RANKERS:
        raise HTTPException(400, f"ranker must be one of {radar.RANKERS}")

    topics = load_topics()
    key = (days, _topics_key(topics), ranker)

    cached = None if refresh else _cache.get(key)
    if cached is None:
        cached = radar.scan(topics, days=days, top=FETCH_TOP, ranker=ranker)
        _cache.set(key, cached)

    result = dict(cached)
    result["papers"] = cached["papers"][:top]
    result["count"] = len(result["papers"])
    return result
