"""
radar.py — the "brain" of Research Radar.

This module has NO web-server code in it on purpose. It just knows how to:
  1. fetch recent papers from bioRxiv, arXiv, and PubMed
  2. score each paper against a set of topics
  3. return plain Python dicts/lists

Keeping this separate from the web server (main.py) is a real software-design
habit: the "business logic" doesn't care whether it's called by a command-line
script, a web API, or a scheduled job. main.py is just a thin wrapper that
exposes these functions over HTTP.
"""

import datetime as dt
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UA = {"User-Agent": "ResearchRadar/2.0 (personal research tool)"}


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


# --------------------------- scoring ---------------------------------------

def score(text, topics):
    """Return (total_score, [matched topic names]) for a blob of text."""
    t = text.lower()
    total, hits = 0, []
    for name, cfg in topics.items():
        weight = cfg.get("weight", 1)
        matched = False
        for term in cfg["terms"]:
            # match the term as a whole word, tolerating a plural suffix
            # ("glioma" -> "gliomas", "transformer" -> "transformers") but not
            # random substrings ("MIMIC" won't match "mimicking").
            pat = r"(?<![a-z0-9])" + re.escape(term.lower()) + r"(?:e?s)?(?![a-z0-9])"
            n = len(re.findall(pat, t))
            if n:
                total += weight * n
                matched = True
        if matched:
            hits.append(name)
    return total, hits


# --------------------------- sources ---------------------------------------

def fetch_biorxiv(days):
    end = dt.date.today()
    start = end - dt.timedelta(days=days)
    out, cursor = [], 0
    for _ in range(6):
        url = (f"https://api.biorxiv.org/details/biorxiv/"
               f"{start.isoformat()}/{end.isoformat()}/{cursor}")
        try:
            data = json.loads(_get(url))
        except Exception:
            break
        coll = data.get("collection", [])
        for p in coll:
            out.append({
                "source": "bioRxiv",
                "title": (p.get("title") or "").strip(),
                "abstract": (p.get("abstract") or "").strip(),
                "authors": (p.get("authors") or "").strip(),
                "date": p.get("date", ""),
                "url": f"https://doi.org/{p.get('doi')}" if p.get("doi") else "",
            })
        if len(coll) < 100:
            break
        cursor += 100
    return out


def fetch_arxiv(days, categories=("q-bio.GN", "q-bio.QM", "q-bio.NC", "cs.LG")):
    cat_q = "+OR+".join(f"cat:{c}" for c in categories)
    url = ("http://export.arxiv.org/api/query?search_query=" + cat_q +
           "&sortBy=submittedDate&sortOrder=descending&max_results=120")
    try:
        xml = _get(url)
    except Exception:
        return []
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml)
    cutoff = dt.date.today() - dt.timedelta(days=days)
    out = []
    for e in root.findall("a:entry", ns):
        pub = (e.findtext("a:published", "", ns) or "")[:10]
        try:
            if dt.date.fromisoformat(pub) < cutoff:
                continue
        except ValueError:
            pass
        authors = ", ".join(a.findtext("a:name", "", ns)
                            for a in e.findall("a:author", ns))
        out.append({
            "source": "arXiv",
            "title": " ".join((e.findtext("a:title", "", ns) or "").split()),
            "abstract": " ".join((e.findtext("a:summary", "", ns) or "").split()),
            "authors": authors,
            "date": pub,
            "url": e.findtext("a:id", "", ns),
        })
    return out


def fetch_pubmed(days, query):
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    term = urllib.parse.quote(query)
    es = (f"{base}esearch.fcgi?db=pubmed&term={term}"
          f"&reldate={days}&datetype=pdat&retmax=60&retmode=json&sort=date")
    try:
        ids = json.loads(_get(es)).get("esearchresult", {}).get("idlist", [])
    except Exception:
        return []
    if not ids:
        return []
    ef = f"{base}efetch.fcgi?db=pubmed&id={','.join(ids)}&retmode=xml"
    try:
        root = ET.fromstring(_get(ef))
    except Exception:
        return []
    out = []
    for art in root.findall(".//PubmedArticle"):
        node = art.find(".//ArticleTitle")
        title = "".join(node.itertext()) if node is not None else ""
        abst = " ".join("".join(a.itertext())
                        for a in art.findall(".//Abstract/AbstractText"))
        pmid = art.findtext(".//PMID", "")
        y = art.findtext(".//PubDate/Year", "")
        m = art.findtext(".//PubDate/Month", "")
        d = art.findtext(".//PubDate/Day", "")
        auths = []
        for a in art.findall(".//Author")[:6]:
            ln, fn = a.findtext("LastName", ""), a.findtext("ForeName", "")
            if ln:
                auths.append(f"{fn} {ln}".strip())
        out.append({
            "source": "PubMed",
            "title": title.strip(),
            "abstract": abst.strip(),
            "authors": ", ".join(auths),
            "date": "-".join(x for x in (y, m, d) if x),
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
        })
    return out


# --------------------------- orchestration ---------------------------------

def dedupe(papers):
    seen, out = set(), []
    for p in papers:
        key = re.sub(r"[^a-z0-9]", "", p["title"].lower())[:60]
        if key and key not in seen:
            seen.add(key)
            out.append(p)
    return out


def scan(topics, days=7, top=20):
    """
    The one function the web server calls. Returns a dict:
        {"generated": "...", "days": 7, "count": N, "papers": [ {...}, ... ]}
    Each paper gets a "_score" and "why" (matched topic names).
    """
    papers = fetch_biorxiv(days) + fetch_arxiv(days) + fetch_pubmed(
        days, " OR ".join(f'"{t}"' for cfg in topics.values() for t in cfg["terms"]))
    papers = dedupe(papers)

    for p in papers:
        body_score, hits = score(p["title"] + " " + p["abstract"], topics)
        title_score, _ = score(p["title"], topics)  # title matches count double
        p["score"] = body_score + title_score
        p["why"] = hits
        # trim abstract for transport
        p["abstract"] = p["abstract"][:600]

    ranked = sorted([p for p in papers if p["score"] > 0],
                    key=lambda p: p["score"], reverse=True)[:top]

    return {
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "days": days,
        "count": len(ranked),
        "scanned": len(papers),
        "papers": ranked,
    }
