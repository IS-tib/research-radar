// api.js — all the talking-to-the-backend code lives here, in one place.
// Keeping network calls out of your components is a good habit: your UI code
// stays about "what to show", and this file is about "how to fetch it".

// In production (deployed), we set VITE_API_URL to the backend's public URL.
// In local dev it's empty, and the Vite proxy (vite.config.js) forwards /api.
const BASE = import.meta.env.VITE_API_URL || ''

async function get(path) {
  const res = await fetch(BASE + path)
  if (!res.ok) throw new Error(`Request failed: ${res.status}`)
  return res.json()
}

export function fetchPapers(days, top) {
  return get(`/api/papers?days=${days}&top=${top}`)
}

export function fetchTopics() {
  return get('/api/topics')
}

export async function saveTopics(topics) {
  const res = await fetch(BASE + '/api/topics', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topics }),
  })
  if (!res.ok) throw new Error(`Save failed: ${res.status}`)
  return res.json()
}
