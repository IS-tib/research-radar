"""FastAPI server exposing the Research Radar ranking engine.

Run locally:  uvicorn main:app --reload  (docs at /docs)
"""

import json
import os
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import radar

HERE = os.path.dirname(os.path.abspath(__file__))
TOPICS_PATH = os.path.join(HERE, "topics.json")
CACHE_TTL = 600  # seconds — avoid re-hitting the paper APIs on every click

app = FastAPI(title="Research Radar API", version="2.1")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_cache = {}  # (days, top) -> (fetched_at, result)


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
def papers(days: int = 7, top: int = 25):
    days = max(1, min(days, 60))
    top = max(1, min(top, 100))
    key = (days, top)
    now = time.time()
    if key in _cache and now - _cache[key][0] < CACHE_TTL:
        return _cache[key][1]
    result = radar.scan(load_topics(), days=days, top=top)
    _cache[key] = (now, result)
    return result
