import { useState, useEffect, useMemo } from 'react'
import { fetchPapers, fetchTopics, saveTopics } from './api.js'

const SOURCES = ['bioRxiv', 'arXiv', 'PubMed']
const SAVED_KEY = 'radar.saved'

const loadSaved = () => {
  try { return JSON.parse(localStorage.getItem(SAVED_KEY)) || [] } catch { return [] }
}

const pct = (x) => `${Math.round((x || 0) * 100)}%`

export default function App() {
  const [papers, setPapers] = useState([])
  const [meta, setMeta] = useState(null)
  const [days, setDays] = useState(7)
  const [top, setTop] = useState(25)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const [query, setQuery] = useState('')
  const [enabled, setEnabled] = useState(new Set(SOURCES))
  const [sort, setSort] = useState('relevance')
  const [saved, setSaved] = useState(loadSaved)
  const [view, setView] = useState('feed')        // 'feed' | 'saved'
  const [editing, setEditing] = useState(false)
  const [insights, setInsights] = useState(false)

  async function runScan() {
    setLoading(true); setError(null)
    try {
      const data = await fetchPapers(days, top)
      setPapers(data.papers); setMeta(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }
  useEffect(() => { runScan() }, [])  // eslint-disable-line

  // Persist bookmarks to the browser so they survive reloads.
  useEffect(() => { localStorage.setItem(SAVED_KEY, JSON.stringify(saved)) }, [saved])
  const isSaved = (p) => saved.some((s) => s.url === p.url)
  const toggleSave = (p) =>
    setSaved((prev) => isSaved(p) ? prev.filter((s) => s.url !== p.url) : [{ ...p }, ...prev])

  const toggleSource = (s) =>
    setEnabled((prev) => {
      const next = new Set(prev)
      next.has(s) ? next.delete(s) : next.add(s)
      return next
    })

  // Derive what's actually on screen: source filter -> text filter -> sort.
  const shown = useMemo(() => {
    const base = view === 'saved' ? saved : papers
    const q = query.trim().toLowerCase()
    let out = base.filter((p) => enabled.has(p.source))
    if (q) out = out.filter((p) =>
      (p.title + p.abstract + (p.authors || '')).toLowerCase().includes(q))
    out = [...out].sort(sort === 'date'
      ? (a, b) => (b.date || '').localeCompare(a.date || '')
      : (a, b) => b.score - a.score)
    return out
  }, [view, saved, papers, enabled, query, sort])

  return (
    <div className="page">
      <header className="masthead">
        <div className="brand">
          <span className="mark">◎</span>
          <div>
            <h1>Research Radar</h1>
            <p className="sub">New work from bioRxiv, arXiv &amp; PubMed, ranked to your interests.</p>
          </div>
        </div>
        <nav className="tabs">
          <button className={view === 'feed' ? 'on' : ''} onClick={() => setView('feed')}>Feed</button>
          <button className={view === 'saved' ? 'on' : ''} onClick={() => setView('saved')}>
            Saved{saved.length ? ` · ${saved.length}` : ''}
          </button>
        </nav>
      </header>

      <div className="toolbar">
        <input className="search" placeholder="Filter results…"
          value={query} onChange={(e) => setQuery(e.target.value)} />
        <div className="chips">
          {SOURCES.map((s) => (
            <button key={s} className={`chip src-${s.toLowerCase()} ${enabled.has(s) ? 'on' : ''}`}
              onClick={() => toggleSource(s)}>{s}</button>
          ))}
        </div>
        <select value={sort} onChange={(e) => setSort(e.target.value)}>
          <option value="relevance">Most relevant</option>
          <option value="date">Newest first</option>
        </select>
        {view === 'feed' && (
          <div className="scan">
            <label>days <input type="number" min="1" max="60" value={days}
              onChange={(e) => setDays(+e.target.value)} /></label>
            <button className="primary" onClick={runScan} disabled={loading}>
              {loading ? 'Scanning…' : 'Refresh'}
            </button>
            <button className="link" onClick={() => setInsights(!insights)}>
              {insights ? 'Hide stats' : 'Insights'}
            </button>
            <button className="link" onClick={() => setEditing(!editing)}>
              {editing ? 'Close' : 'Topics'}
            </button>
          </div>
        )}
      </div>

      {editing && view === 'feed' && <TopicsEditor onSaved={() => { setEditing(false); runScan() }} />}
      {insights && view === 'feed' && shown.length > 0 && <Insights papers={shown} />}

      {view === 'feed' && meta && !loading &&
        <p className="status">{shown.length} shown · {meta.scanned} scanned · updated {meta.generated.slice(0, 16).replace('T', ' ')}</p>}
      {error && <p className="status err">Couldn't load papers: {error}</p>}
      {loading && <p className="status">Searching the last {days} days…</p>}
      {!loading && shown.length === 0 &&
        <p className="empty">{view === 'saved' ? 'Nothing saved yet — tap the star on a paper.' : 'No matches. Widen the window or broaden your topics.'}</p>}

      <ol className="feed">
        {shown.map((p, i) => (
          <PaperCard key={p.url || i} p={p} rank={i + 1}
            saved={isSaved(p)} onSave={() => toggleSave(p)} showRank={view === 'feed' && sort === 'relevance'} />
        ))}
      </ol>

      <footer>Isabella Shen — React · FastAPI</footer>
    </div>
  )
}

function PaperCard({ p, rank, saved, onSave, showRank }) {
  // Cards may carry a single `source` (older saves) or a merged `sources` union.
  const sources = p.sources?.length ? p.sources : [p.source]
  const c = p.components
  const breakdown = c
    ? `keyword ${pct(c.keyword)} · semantic ${pct(c.semantic)} · recency ${pct(c.recency)}`
    : undefined
  return (
    <li className="entry">
      {showRank && <div className="num">{rank}</div>}
      <div className="col">
        <div className="line">
          {sources.map((s) => (
            <span key={s} className={`tag src-${s.toLowerCase()}`}>{s}</span>
          ))}
          <span className="dot">·</span>
          <span>{p.date}</span>
          {typeof p.match === 'number' &&
            <span className="pct" title={breakdown}>{p.match}% match</span>}
          {p.why?.length > 0 && <span className="match">{p.why.join(', ')}</span>}
          <button className={`star ${saved ? 'on' : ''}`} onClick={onSave}
            title={saved ? 'Remove bookmark' : 'Save'}>{saved ? '★' : '☆'}</button>
        </div>
        <a className="headline" href={p.url} target="_blank" rel="noopener">{p.title}</a>
        <div className="byline">{p.authors?.slice(0, 150)}</div>
        <p className="excerpt">{p.abstract}{p.abstract?.length >= 600 ? '…' : ''}</p>
      </div>
    </li>
  )
}

// Words that carry no topical signal — kept in sync in spirit with the backend's
// stopword list so the client-side keyword bar surfaces real terms, not glue.
const STOP = new Set(('the a an and or of to in for on with by is are was were be this '
  + 'that from as at it its into via using used we our their they show shows study '
  + 'studies results method methods based can new novel using single cell').split(' '))

function Insights({ papers }) {
  const stats = useMemo(() => {
    const bySource = {}
    const terms = {}
    const byWeek = {}
    for (const p of papers) {
      for (const s of (p.sources?.length ? p.sources : [p.source])) {
        bySource[s] = (bySource[s] || 0) + 1
      }
      for (const w of (p.title || '').toLowerCase().match(/[a-z][a-z0-9-]{2,}/g) || []) {
        if (!STOP.has(w)) terms[w] = (terms[w] || 0) + 1
      }
      const wk = weekKey(p.date)
      if (wk) byWeek[wk] = (byWeek[wk] || 0) + 1
    }
    const topTerms = Object.entries(terms)
      .filter(([, n]) => n > 1).sort((a, b) => b[1] - a[1]).slice(0, 8)
    const weeks = Object.keys(byWeek).sort().map((k) => ({ k, n: byWeek[k] }))
    return { bySource, topTerms, weeks }
  }, [papers])

  const srcMax = Math.max(1, ...Object.values(stats.bySource))
  const termMax = Math.max(1, ...stats.topTerms.map(([, n]) => n))

  return (
    <div className="insights">
      <div className="ins-col">
        <h4>By source</h4>
        {SOURCES.filter((s) => stats.bySource[s]).map((s) => (
          <div className="bar-row" key={s}>
            <span className="bar-label">{s}</span>
            <span className={`bar src-${s.toLowerCase()}`}
              style={{ width: `${(stats.bySource[s] / srcMax) * 100}%` }} />
            <span className="bar-n">{stats.bySource[s]}</span>
          </div>
        ))}
      </div>

      <div className="ins-col">
        <h4>Top keywords</h4>
        {stats.topTerms.length === 0 && <p className="ins-empty">Not enough data.</p>}
        {stats.topTerms.map(([t, n]) => (
          <div className="bar-row" key={t}>
            <span className="bar-label">{t}</span>
            <span className="bar accent" style={{ width: `${(n / termMax) * 100}%` }} />
            <span className="bar-n">{n}</span>
          </div>
        ))}
      </div>

      <div className="ins-col">
        <h4>Papers per week</h4>
        <Sparkline weeks={stats.weeks} />
      </div>
    </div>
  )
}

// ISO year-week bucket for a YYYY-MM-DD(-ish) date string; null if unparseable.
function weekKey(date) {
  const d = new Date((date || '').slice(0, 10))
  if (isNaN(d)) return null
  const t = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()))
  const day = (t.getUTCDay() + 6) % 7            // Mon=0
  t.setUTCDate(t.getUTCDate() - day + 3)         // nearest Thursday
  const first = new Date(Date.UTC(t.getUTCFullYear(), 0, 4))
  const week = 1 + Math.round(((t - first) / 864e5 - 3 + ((first.getUTCDay() + 6) % 7)) / 7)
  return `${t.getUTCFullYear()}-${String(week).padStart(2, '0')}`
}

function Sparkline({ weeks }) {
  if (weeks.length === 0) return <p className="ins-empty">No dated papers.</p>
  const W = 168, H = 44, max = Math.max(...weeks.map((w) => w.n))
  const step = weeks.length > 1 ? W / (weeks.length - 1) : 0
  const pts = weeks.map((w, i) => [i * step, H - (w.n / max) * (H - 6) - 3])
  const line = pts.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' ')
  const area = `0,${H} ${line} ${W},${H}`
  return (
    <svg className="spark" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
      <polygon points={area} className="spark-fill" />
      <polyline points={line} className="spark-line" />
      {pts.map(([x, y], i) => <circle key={i} cx={x} cy={y} r="1.6" className="spark-dot" />)}
    </svg>
  )
}

function TopicsEditor({ onSaved }) {
  const [topics, setTopics] = useState(null)
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState('')

  useEffect(() => { fetchTopics().then(setTopics) }, [])
  if (!topics) return <div className="editor">Loading topics…</div>

  const update = (name, field, value) =>
    setTopics({ ...topics, [name]: { ...topics[name], [field]: value } })
  const remove = (name) => { const c = { ...topics }; delete c[name]; setTopics(c) }
  const add = () => setTopics({ ...topics, [`Topic ${Object.keys(topics).length + 1}`]: { weight: 2, terms: [] } })

  async function save() {
    setSaving(true); setMsg('')
    try { await saveTopics(topics); onSaved?.() }
    catch (e) { setMsg(e.message) }
    finally { setSaving(false) }
  }

  return (
    <div className="editor">
      <p className="hint">Weight sets how strongly a topic pulls a paper up the ranking. Terms are comma-separated.</p>
      {Object.entries(topics).map(([name, cfg]) => (
        <div className="row" key={name}>
          <input className="w-name" value={name} readOnly />
          <input className="w-num" type="number" min="1" max="10" value={cfg.weight}
            onChange={(e) => update(name, 'weight', +e.target.value)} />
          <input className="w-terms" value={cfg.terms.join(', ')}
            onChange={(e) => update(name, 'terms', e.target.value.split(',').map((s) => s.trim()).filter(Boolean))} />
          <button className="x" onClick={() => remove(name)}>✕</button>
        </div>
      ))}
      <div className="row-actions">
        <button className="link" onClick={add}>+ topic</button>
        <button className="primary" onClick={save} disabled={saving}>{saving ? 'Saving…' : 'Save & rescan'}</button>
        {msg && <span className="err">{msg}</span>}
      </div>
    </div>
  )
}
