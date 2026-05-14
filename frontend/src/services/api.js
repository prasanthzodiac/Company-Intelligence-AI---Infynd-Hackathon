/**
 * Same-origin Flask: leave unset (uses `/api`).
 * Split deploy (e.g. Vercel UI + Flask on Railway): set `VITE_API_BASE_URL` to your API root, e.g. `https://your-api.example.com/api` (no trailing slash).
 */
function resolveApiBase() {
  const raw = import.meta.env.VITE_API_BASE_URL
  if (raw === undefined || raw === null || String(raw).trim() === '') {
    return '/api'
  }
  return String(raw).replace(/\/$/, '')
}

export const API_BASE = resolveApiBase()

export const getCompanies = async () => {
  const response = await fetch(`${API_BASE}/companies`)
  if (!response.ok) {
    throw new Error('Failed to load companies')
  }
  return response.json()
}

export const getCompanyProfile = async (domain) => {
  const response = await fetch(`${API_BASE}/companies/${domain}/profile`)
  if (!response.ok) {
    throw new Error('Failed to load profile')
  }
  return response.json()
}

export const getCompanyChunks = async (domain) => {
  const response = await fetch(`${API_BASE}/companies/${domain}/chunks`)
  if (!response.ok) {
    throw new Error('Failed to load chunks')
  }
  return response.json()
}

export const sendChatMessage = async (domain, question) => {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ domain, question }),
  })
  if (!response.ok) {
    throw new Error('Failed to send chat message')
  }
  return response.json()
}

export const getProofs = async (domain, query) => {
  const response = await fetch(`${API_BASE}/proofs/${domain}?query=${encodeURIComponent(query)}`)
  if (!response.ok) {
    throw new Error('Failed to load proofs')
  }
  return response.json()
}

