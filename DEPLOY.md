# 🚀 Deploying Research Radar (beginner-friendly)

Goal: get your app on a **real public URL** you can put on your resume. It's
free. Don't worry if none of this is familiar yet — just follow along.

## The three tools you'll use (and what each one is)

| Tool | What it is | What we use it for |
|------|-----------|--------------------|
| **GitHub** | Where your code lives online | Store the project + show it to recruiters |
| **Render** | A host that runs *servers* | Run your Python **backend** |
| **Vercel** | A host that runs *websites* | Serve your React **frontend** |

Why two hosts? Because a backend (a running Python program) and a frontend (files
a browser downloads) are different kinds of things. This split is exactly how
real companies deploy apps — learning it is part of the point.

You'll need free accounts on all three. Sign up for **Render and Vercel using
your GitHub account** (there's a "Continue with GitHub" button) — it makes
connecting your repo one click.

---

## Step 1 — Put the code on GitHub

If you've never used git, install it (`git --version` to check; Mac will offer
to install it). Then, in Terminal, from the project folder:

```bash
cd ~/claudeee/research-radar-web
git init
git add .
git commit -m "Initial project structure"
```

Now make an empty repo on github.com (green **New** button, name it
`research-radar`, leave everything unchecked), then connect and push:

```bash
git remote add origin https://github.com/YOUR-USERNAME/research-radar.git
git branch -M main
git push -u origin main
```

> 💡 **Prefer committing in steps?** See [COMMITS.md](COMMITS.md) for a sequence
> of smaller, realistic commits instead of one big one — it makes your history
> look like real building (because it is).

---

## Step 2 — Deploy the backend on Render

1. Go to **render.com** → **New +** → **Web Service**.
2. Connect your GitHub and pick your `research-radar` repo.
3. Fill in these settings:
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free
4. Click **Create Web Service**. Wait ~2–3 min for it to build.
5. When it's live, copy its URL — it'll look like
   `https://research-radar-api.onrender.com`. **Save this.**
6. Test it: open `THAT-URL/api/health` in your browser. You should see
   `{"status":"ok",...}`. 🎉 Your backend is on the internet.

> ⚠️ Render's free tier "sleeps" after 15 min idle, so the first request after a
> nap takes ~30s to wake up. Totally fine for a portfolio project — just mention
> it's a free-tier cold start if anyone asks.

---

## Step 3 — Deploy the frontend on Vercel

1. Go to **vercel.com** → **Add New** → **Project** → import your `research-radar` repo.
2. Settings:
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend` (click "Edit" and pick it)
3. Expand **Environment Variables** and add one:
   - **Name:** `VITE_API_URL`
   - **Value:** your Render URL from Step 2 (e.g. `https://research-radar-api.onrender.com`)
4. Click **Deploy**. Wait ~1 min.
5. Vercel gives you a URL like `https://research-radar.vercel.app`. **Open it.**

That's your live app. This is the link you put on your resume and GitHub README.

---

## Step 4 — Final wiring check

- Open your Vercel URL, click **Refresh** → papers should load (give the Render
  backend a few seconds to wake up the first time).
- If you see no papers or an error, it's almost always the `VITE_API_URL` env var.
  Double-check it exactly matches your Render URL (no trailing slash), then in
  Vercel hit **Redeploy**.

## Step 5 — Make your repo shine

- Add your live URL to the top of `README.md`.
- Take a screenshot of the running app, save it to `docs/screenshots/app.png`,
  and uncomment the image line in the README.
- Add the CI badge: at the top of `README.md`, paste (with your username):
  `![CI](https://github.com/YOUR-USERNAME/research-radar/actions/workflows/ci.yml/badge.svg)`

Done. You built and deployed a real full-stack app. 🔭
