"""
main.py — the web server (the "backend API").

This is the thin layer that turns radar.py's functions into HTTP endpoints the
frontend can call. Run it locally with:

    cd backend
    pip install -r requirements.txt
    uvicorn main:app --reload

Then open http://localhost:8000/docs  <-- FastAPI auto-generates interactive API
docs for you. Try the endpoints there; it's the fastest way to SEE what a
backend API actually is.

Endpoints:
    GET  /api/health            -> quick "is it alive?" check
    GET  /api/topics            -> the current topics being tracked
    PUT  /api/topics            -> replace the topics (saves to topics.json)
    GET  /api/papers?days=7&top=20  -> run a scan, return ranked papers as JSON
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

app = FastAPI(title="Research Radar API", version="2.0")

# CORS = the rule that lets your frontend (running on a different URL) call this
# backend from the browser. Without this, the browser blocks the request.
# "*" is fine for a personal project; for production you'd list your real domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- tiny in-memory cache so we don't hammer the paper APIs on every click ---
_cache = {}  # key -> (timestamp, result)
CACHE_TTL = 600  # seconds (10 min)


def load_topics():
    with open(TOPICS_PATH) as f:
        return json.load(f)


def save_topics(topics):
    with open(TOPICS_PATH, "w") as f:
        json.dump(topics, f, indent=2)


class Topics(BaseModel):
    # topics is a dict like {"name": {"weight": 3, "terms": ["a","b"]}}
    topics: dict


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "research-radar"}


@app.get("/api/topics")
def get_topics():
    return load_topics()


@app.put("/api/topics")
def put_topics(body: Topics):
    # basic validation: every topic needs a terms list
    for name, cfg in body.topics.items():
        if "terms" not in cfg or not isinstance(cfg["terms"], list):
            raise HTTPException(400, f"Topic '{name}' needs a 'terms' list")
    save_topics(body.topics)
    _cache.clear()  # topics changed -> old results are stale
    return {"saved": True, "topics": body.topics}


@app.get("/api/papers")
def papers(days: int = 7, top: int = 20):
    days = max(1, min(days, 60))
    top = max(1, min(top, 100))
    key = f"{days}:{top}"
    now = time.time()
    if key in _cache and now - _cache[key][0] < CACHE_TTL:
        return _cache[key][1]           # serve cached result
    result = radar.scan(load_topics(), days=days, top=top)
    _cache[key] = (now, result)
    return result
