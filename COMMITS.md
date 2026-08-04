# 📝 Committing in realistic steps

You wanted to commit incrementally yourself — good instinct. A history that
shows the project *growing* is more credible (and more useful to you) than one
giant "initial commit." Here's a sensible order. Make each commit, read the
files you're adding as you go, and you'll actually understand the whole thing.

> These commands assume you've run `git init` already and are in the project root.
> Do them in order. After the last one, push with `git push -u origin main`.

```bash
# 1) Project skeleton + docs
git add README.md LICENSE .gitignore
git commit -m "Add README, license, and gitignore"

# 2) Backend: the core logic (fetching + scoring)
git add backend/radar.py backend/topics.json
git commit -m "Add paper-fetching and relevance-scoring logic"

# 3) Backend: the API server
git add backend/main.py backend/requirements.txt
git commit -m "Add FastAPI server exposing /api/papers and /api/topics"

# 4) Backend: tests
git add backend/tests/
git commit -m "Add unit tests for the scoring logic"

# 5) Frontend: project setup
git add frontend/package.json frontend/vite.config.js frontend/index.html frontend/.env.example
git commit -m "Set up React + Vite frontend project"

# 6) Frontend: the app itself
git add frontend/src/
git commit -m "Build UI: paper list, controls, and topic editor"

# 7) CI + architecture docs
git add .github/ docs/
git commit -m "Add GitHub Actions CI and architecture diagram"

# 8) Deployment guide
git add DEPLOY.md COMMITS.md
git commit -m "Add deployment guide"
```

## After it's live, real ongoing commits

Once it's deployed and you start *using* it, commit the real changes you make —
this is where your history becomes genuinely yours:

- `git commit -m "Add loading spinner while papers fetch"`
- `git commit -m "Fix: handle empty results gracefully"`
- `git commit -m "Add LLM one-line summaries to each paper"`
- `git commit -m "Cache results so repeated clicks are instant"`

Each of those is a feature *you* decided on and understand — exactly what you'll
talk about in an interview. That's the whole game.
