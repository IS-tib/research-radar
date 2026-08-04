// App.jsx — the whole UI.
//
// Two React ideas do 90% of the work here:
//   1. useState  — a piece of data that, when it changes, re-renders the screen.
//   2. useEffect — run some code (like fetching data) after the screen renders.
//
// Read the comments top-to-bottom and you'll have a real mental model of React.

import { useState, useEffect } from 'react'
import { fetchPapers, fetchTopics, saveTopics } from './api.js'

export default function App() {
  // --- state: the "live" values that drive what you see ---
  const [papers, setPapers] = useState([])     // the ranked results
  const [meta, setMeta] = useState(null)        // {generated, scanned, count...}
  const [days, setDays] = useState(7)
  const [top, setTop] = useState(20)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showTopics, setShowTopics] = useState(false)

  // Ask the backend for papers. useState setters (setLoading, etc.) trigger
  // React to re-draw the page with the new values.
  async function runScan() {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchPapers(days, top)
      setPapers(data.papers)
      setMeta(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  // useEffect with an empty [] means "run once, right after the first render."
  // Perfect for loading data when the page opens.
  useEffect(() => { runScan() }, [])   // eslint-disable-line

  return (
    <div className="app">
      <header>
        <h1>🔭 Research Radar</h1>
        <p className="tag">
          Newest papers from bioRxiv · arXiv · PubMed, ranked for your research.
        </p>
      </header>

      {/* --- controls --- */}
      <div className="controls">
        <label>Last
          <input type="number" min="1" max="60" value={days}
            onChange={(e) => setDays(Number(e.target.value))} /> days
        </label>
        <label>Show top
          <input type="number" min="1" max="100" value={top}
            onChange={(e) => setTop(Number(e.target.value))} />
        </label>
        <button className="primary" onClick={runScan} disabled={loading}>
          {loading ? 'Scanning…' : 'Refresh'}
        </button>
        <button className="ghost" onClick={() => setShowTopics(!showTopics)}>
          {showTopics ? 'Hide topics' : 'Edit topics'}
        </button>
      </div>

      {/* --- topics editor (only shown when toggled) --- */}
      {showTopics && <TopicsEditor onSaved={runScan} />}

      {/* --- status line --- */}
      {meta && !loading && (
        <p className="status">
          {meta.count} relevant papers · scanned {meta.scanned} · {meta.generated}
        </p>
      )}
      {error && <p className="error">⚠️ {error}</p>}
      {loading && <p className="status">Searching the last {days} days…</p>}

      {/* --- results --- */}
      {!loading && papers.length === 0 && !error && (
        <p className="empty">No matches yet. Try more days, or broaden your topics.</p>
      )}
      <div className="list">
        {papers.map((p, i) => <PaperCard key={p.url || i} p={p} rank={i + 1} />)}
      </div>

      <footer>Built by Isabella · FastAPI + React</footer>
    </div>
  )
}

// A single paper. `p` and `rank` are "props" — inputs passed from the parent.
function PaperCard({ p, rank }) {
  return (
    <article className="card">
      <div className="rank">#{rank}</div>
      <div className="body">
        <div className="meta">
          <span className={`src src-${p.source.toLowerCase()}`}>{p.source}</span>
          <span className="date">{p.date}</span>
          <span className="score">relevance {p.score}</span>
        </div>
        <a className="title" href={p.url} target="_blank" rel="noopener">{p.title}</a>
        {p.why?.length > 0 && <div className="why">🎯 {p.why.join(' · ')}</div>}
        <div className="auth">{p.authors?.slice(0, 160)}</div>
        <p className="abs">{p.abstract}{p.abstract?.length >= 600 ? '…' : ''}</p>
      </div>
    </article>
  )
}

// The topics editor. Loads topics from the backend, lets you edit weight + terms,
// add/remove topics, and PUTs them back.
function TopicsEditor({ onSaved }) {
  const [topics, setTopics] = useState(null)
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState('')

  useEffect(() => { fetchTopics().then(setTopics) }, [])

  if (!topics) return <div className="topics">Loading topics…</div>

  // Helper to update one topic immutably (React needs a NEW object to re-render).
  function update(name, field, value) {
    setTopics({ ...topics, [name]: { ...topics[name], [field]: value } })
  }
  function removeTopic(name) {
    const copy = { ...topics }; delete copy[name]; setTopics(copy)
  }
  function addTopic() {
    const name = `New topic ${Object.keys(topics).length + 1}`
    setTopics({ ...topics, [name]: { weight: 2, terms: [] } })
  }

  async function save() {
    setSaving(true); setMsg('')
    try {
      await saveTopics(topics)
      setMsg('Saved ✓  (refreshing results…)')
      onSaved?.()
    } catch (e) {
      setMsg('Error: ' + e.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="topics">
      <p className="hint">Higher weight = ranks papers higher. Terms are comma-separated.</p>
      {Object.entries(topics).map(([name, cfg]) => (
        <div className="topicrow" key={name}>
          <input className="tname" value={name} readOnly />
          <input className="tweight" type="number" min="1" max="10" value={cfg.weight}
            onChange={(e) => update(name, 'weight', Number(e.target.value))} />
          <input className="tterms" value={cfg.terms.join(', ')}
            onChange={(e) => update(name, 'terms', e.target.value.split(',').map(s => s.trim()).filter(Boolean))} />
          <button className="del" onClick={() => removeTopic(name)}>✕</button>
        </div>
      ))}
      <div className="topicactions">
        <button className="ghost" onClick={addTopic}>+ Add topic</button>
        <button className="primary" onClick={save} disabled={saving}>
          {saving ? 'Saving…' : 'Save topics'}
        </button>
        <span className="savemsg">{msg}</span>
      </div>
    </div>
  )
}
