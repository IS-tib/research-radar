import { useState, useEffect, useMemo } from 'react'
import { fetchPapers, fetchTopics, saveTopics } from './api.js'

const SOURCES = ['bioRxiv', 'arXiv', 'PubMed']
const SAVED_KEY = 'radar.saved'

const loadSaved = () => {
  try { return JSON.parse(localStorage.getItem(SAVED_KEY)) || [] } catch { return [] }
}

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
            <button className="link" onClick={() => setEditing(!editing)}>
              {editing ? 'Close' : 'Topics'}
            </button>
          </div>
        )}
      </div>

      {editing && view === 'feed' && <TopicsEditor onSaved={() => { setEditing(false); runScan() }} />}

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
  return (
    <li className="entry">
      {showRank && <div className="num">{rank}</div>}
      <div className="col">
        <div className="line">
          <span className={`tag src-${p.source.toLowerCase()}`}>{p.source}</span>
          <span className="dot">·</span>
          <span>{p.date}</span>
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
