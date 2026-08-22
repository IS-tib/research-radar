// Backend calls. VITE_API_URL points at the deployed API in production;
// in dev it's empty and Vite proxies /api to localhost:8000.
const BASE = import.meta.env.VITE_API_URL || ''

async function json(path, opts) {
  const res = await fetch(BASE + path, opts)
  if (!res.ok) throw new Error(`${res.status}`)
  return res.json()
}

export const fetchPapers = (days, top, ranker = 'tfidf') =>
  json(`/api/papers?days=${days}&top=${top}&ranker=${ranker}`)
export const fetchTopics = () => json('/api/topics')
export const saveTopics = (topics) =>
  json('/api/topics', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topics }),
  })
