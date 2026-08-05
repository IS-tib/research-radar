"""Core logic for Research Radar: fetch recent papers from bioRxiv, arXiv, and
PubMed, then rank them against a set of weighted topics. No web-server code lives
here so the same functions can back the API, a CLI, or a scheduled job."""

import datetime as dt
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

UA = {"User-Agent": "ResearchRadar/2.1"}

# Papers newer than this get a relevance boost; older ones decay to none.
RECENCY_HALFLIFE_DAYS = 14
RECENCY_WEIGHT = 0.4


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def _parse_date(s):
    """Best-effort parse of the differing date formats the three sources use."""
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y-%b-%d", "%Y-%b", "%Y"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


# --- ranking ---------------------------------------------------------------

def score(text, topics):
    """Weighted keyword score for a blob of text; also returns matched topics."""
    t = text.lower()
    total, hits = 0, []
    for name, cfg in topics.items():
        weight = cfg.get("weight", 1)
        matched = False
        for term in cfg["terms"]:
            # whole-word match, tolerant of a plural suffix but not substrings
            # (so "glioma" hits "gliomas" but "MIMIC" won't hit "mimicking").
            pat = r"(?<![a-z0-9])" + re.escape(term.lower()) + r"(?:e?s)?(?![a-z0-9])"
            if re.search(pat, t):
                total += weight * len(re.findall(pat, t))
                matched = True
        if matched:
            hits.append(name)
    return total, hits


def _recency_factor(date, today):
    """1.0 for a paper from today, decaying exponentially with age."""
    if date is None:
        return 0.0
    age = max(0, (today - date).days)
    return 0.5 ** (age / RECENCY_HALFLIFE_DAYS)


# --- sources ---------------------------------------------------------------

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


# --- orchestration ---------------------------------------------------------

def dedupe(papers):
    seen, out = set(), []
    for p in papers:
        key = re.sub(r"[^a-z0-9]", "", p["title"].lower())[:60]
        if key and key not in seen:
            seen.add(key)
            out.append(p)
    return out


def scan(topics, days=7, top=20):
    """Fetch, score, and rank. Returns the payload the API serves."""
    pubmed_query = " OR ".join(
        f'"{t}"' for cfg in topics.values() for t in cfg["terms"])

    # The three fetches are I/O-bound, so run them concurrently — total latency
    # is the slowest source, not the sum of all three.
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [
            pool.submit(fetch_biorxiv, days),
            pool.submit(fetch_arxiv, days),
            pool.submit(fetch_pubmed, days, pubmed_query),
        ]
        papers = [p for f in futures for p in f.result()]

    papers = dedupe(papers)
    today = dt.date.today()

    ranked = []
    for p in papers:
        # Title matches count double (titles are signal-dense).
        rel, hits = score(p["title"] + " " + p["abstract"], topics)
        rel += score(p["title"], topics)[0]
        if rel <= 0:
            continue
        recency = _recency_factor(_parse_date(p["date"]), today)
        p["score"] = rel
        p["why"] = hits
        p["abstract"] = p["abstract"][:600]
        # Blend keyword relevance with freshness for the final ordering.
        p["_rank"] = rel * (1 + RECENCY_WEIGHT * recency)
        ranked.append(p)

    ranked.sort(key=lambda p: p["_rank"], reverse=True)
    ranked = ranked[:top]
    for p in ranked:
        p.pop("_rank", None)

    return {
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "days": days,
        "count": len(ranked),
        "scanned": len(papers),
        "papers": ranked,
    }
