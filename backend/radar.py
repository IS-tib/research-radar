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

import numpy as np

UA = {"User-Agent": "ResearchRadar/2.1"}

# Papers newer than this get a relevance boost; older ones decay to none.
RECENCY_HALFLIFE_DAYS = 14

# The final ranking blends three transparent signals; the weights sum to 1 so the
# blended value reads directly as a "match %". Keyword still leads (it's the most
# precise), TF-IDF similarity catches on-topic work that happens to use different
# vocabulary, and recency nudges fresh papers up.
W_KEYWORD, W_SEMANTIC, W_RECENCY = 0.55, 0.30, 0.15

# A paper with no keyword hit is still surfaced if it sits close to the topics in
# TF-IDF space — that semantic reach is the whole point of the layer.
SEMANTIC_KEEP = 0.10


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


# --- semantic layer --------------------------------------------------------
# Keyword scoring only fires on the exact terms you listed. TF-IDF adds a second,
# softer signal: it represents every paper and the topic list as vectors over the
# words that actually appear, and measures the angle between them. That lets a
# paper about "tumour subtyping from expression profiles" rank for a "glioma /
# scRNA-seq" interest even without a literal term hit. numpy only — no embeddings,
# no model weights, and fully deterministic (the vocabulary is sorted).

# Function words carry no topical signal but would dominate the vectors, so drop
# them before counting.
_STOP = frozenset((
    "the a an and or of to in for on with by is are was were be been being this "
    "that these those from as at it its into via using used use we our their they "
    "here show shows shown study studies results result method methods approach "
    "based can may also however than then which when where while not no such more "
    "most both between within across during over under new novel paper"
).split())
_TOKEN_RE = re.compile(r"[a-z][a-z0-9-]{1,}")


def _tokens(text):
    return [t for t in _TOKEN_RE.findall((text or "").lower()) if t not in _STOP]


def build_tfidf(docs):
    """TF-IDF document-term matrix over `docs` (raw strings).

    Returns (matrix, vocab, idf). Deterministic: the vocabulary is sorted, so the
    same corpus always yields the same vectors. Uses smoothed inverse document
    frequency — ln((1+N)/(1+df)) + 1 — so a term in every paper still contributes
    a little rather than collapsing to zero."""
    tokenized = [_tokens(d) for d in docs]
    vocab = {t: i for i, t in
             enumerate(sorted({t for toks in tokenized for t in toks}))}
    tf = np.zeros((len(docs), len(vocab)))
    for i, toks in enumerate(tokenized):
        for t in toks:
            tf[i, vocab[t]] += 1.0
    n = len(docs)
    df = np.count_nonzero(tf > 0, axis=0)
    idf = np.log((1 + n) / (1 + df)) + 1.0
    return tf * idf, vocab, idf


def query_vector(topics, vocab, idf):
    """Fold the configured topic terms into a single TF-IDF query vector, each term
    weighted by its topic's weight so heavier topics pull harder in vector space
    too (mirroring how they dominate the keyword score)."""
    q = np.zeros(len(vocab))
    for cfg in topics.values():
        w = cfg.get("weight", 1)
        for term in cfg["terms"]:
            for t in _tokens(term):
                j = vocab.get(t)
                if j is not None:
                    q[j] += w
    return q * idf


def _cosine(mat, q):
    """Row-wise cosine similarity between each row of `mat` and vector `q`, in [0,1]
    for non-negative TF-IDF weights."""
    qn = np.linalg.norm(q)
    if qn == 0:
        return np.zeros(mat.shape[0])
    rn = np.linalg.norm(mat, axis=1)
    rn[rn == 0] = 1.0  # zero-length rows dot to 0 anyway; just avoid div-by-zero
    return (mat @ q) / (rn * qn)


def semantic_similarity(docs, topics):
    """Cosine similarity of each document to the topic query in one shared TF-IDF
    space. Returns a list aligned with `docs` (cosine is only comparable within a
    single space, so the whole corpus is vectorised together)."""
    if not docs:
        return []
    mat, vocab, idf = build_tfidf(docs)
    if not vocab:
        return [0.0] * len(docs)
    return _cosine(mat, query_vector(topics, vocab, idf)).tolist()


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

def _norm_title(title):
    """Case/punctuation/whitespace-stripped title used as a dedup key."""
    return re.sub(r"[^a-z0-9]", "", (title or "").lower())[:60]


def _doi_of(p):
    """Pull a DOI out of a paper's URL when one is present (bioRxiv links carry it;
    arXiv/PubMed links don't)."""
    m = re.search(r"doi\.org/(\S+)", p.get("url", ""))
    return m.group(1).lower().rstrip("/") if m else None


def dedupe(papers):
    """Collapse the same paper arriving from more than one source.

    Two records are the same when they share a DOI or a normalized title. The
    survivor keeps the union of sources (so a card can show it appeared on both
    arXiv and bioRxiv) and the longest abstract seen. First-seen order is kept."""
    title_idx, doi_idx, records = {}, {}, []
    for p in papers:
        tkey = _norm_title(p.get("title", ""))
        doi = _doi_of(p)
        if not tkey and not doi:
            continue  # nothing to key on — drop titleless noise
        rec = (doi and doi_idx.get(doi)) or (tkey and title_idx.get(tkey)) or None
        if rec is None:
            rec = dict(p)
            rec["sources"] = []
            records.append(rec)
        if p["source"] not in rec["sources"]:
            rec["sources"].append(p["source"])
        if len(p.get("abstract", "")) > len(rec.get("abstract", "")):
            rec["abstract"] = p["abstract"]
        if tkey:
            title_idx.setdefault(tkey, rec)
        if doi:
            doi_idx.setdefault(doi, rec)
    return records


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

    # Build the TF-IDF space once, over the whole fetched corpus, so every paper is
    # scored against the same vocabulary (cosine is only meaningful within one space).
    sims = semantic_similarity(
        [f"{p['title']} {p['abstract']}" for p in papers], topics)

    kept = []
    for i, p in enumerate(papers):
        # Title matches count double (titles are signal-dense).
        rel, hits = score(p["title"] + " " + p["abstract"], topics)
        rel += score(p["title"], topics)[0]
        sem = sims[i] if i < len(sims) else 0.0
        if rel <= 0 and sem < SEMANTIC_KEEP:
            continue
        recency = _recency_factor(_parse_date(p["date"]), today)
        kept.append((p, rel, sem, recency, hits))

    # Normalize keyword scores to [0,1] within this batch so all three components
    # share a scale before blending into a single, human-readable match percentage.
    max_rel = max((rel for _, rel, *_ in kept), default=0) or 1

    ranked = []
    for p, rel, sem, recency, hits in kept:
        kw = rel / max_rel
        blended = W_KEYWORD * kw + W_SEMANTIC * sem + W_RECENCY * recency
        p["score"] = round(blended, 4)
        p["match"] = round(blended * 100)
        # Exposed so the UI can explain *why* a paper ranked where it did.
        p["components"] = {
            "keyword": round(kw, 3),
            "semantic": round(sem, 3),
            "recency": round(recency, 3),
        }
        p["why"] = hits
        p["abstract"] = p["abstract"][:600]
        ranked.append(p)

    ranked.sort(key=lambda p: p["score"], reverse=True)
    ranked = ranked[:top]

    return {
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "days": days,
        "count": len(ranked),
        "scanned": len(papers),
        "papers": ranked,
    }
