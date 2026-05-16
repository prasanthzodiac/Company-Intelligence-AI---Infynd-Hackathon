/**
 * Same-origin Flask: leave unset (uses `/api`).
 * Split deploy (Vercel UI + Render API): set VITE_API_BASE_URL to your API root,
 * e.g. https://your-app.onrender.com/api (no trailing slash).
 */
function resolveApiBase() {
  const raw = import.meta.env.VITE_API_BASE_URL
  if (raw === undefined || raw === null || String(raw).trim() === '') {
    return '/api'
  }
  let base = String(raw).trim().replace(/\/+$/, '')
  if (/^https?:\/\//i.test(base) && !base.endsWith('/api')) {
    base = `${base}/api`
  }
  return base
}

export const API_BASE = resolveApiBase()

export const isProductionSameOriginApi = () =>
  Boolean(import.meta.env.PROD && API_BASE === '/api')

/**
 * fetch() with clearer errors for cross-origin / offline API issues.
 */
export async function apiFetch(path, options = {}) {
  const url = path.startsWith('http') ? path : `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`
  try {
    const response = await fetch(url, options)
    return { response, url }
  } catch (err) {
    const msg = err?.message || String(err)
    if (msg === 'Failed to fetch' || err instanceof TypeError) {
      throw new Error(
        `Cannot reach API at ${url}. ` +
          'Check Render is running, open /api/health in the browser, set VITE_API_BASE_URL on Vercel, and redeploy.'
      )
    }
    throw err
  }
}

export const getCompanies = async () => {
  const { response } = await apiFetch('/companies')
  if (!response.ok) {
    const body = await response.text().catch(() => '')
    throw new Error(`Failed to load companies (${response.status}): ${body || response.statusText}`)
  }
  return response.json()
}

export const getCompanyProfile = async (domain) => {
  const { response } = await apiFetch(`/companies/${encodeURIComponent(domain)}/profile`)
  if (!response.ok) {
    throw new Error('Failed to load profile')
  }
  return response.json()
}

export const getCompanyChunks = async (domain) => {
  const { response } = await apiFetch(`/companies/${encodeURIComponent(domain)}/chunks`)
  if (!response.ok) {
    throw new Error('Failed to load chunks')
  }
  return response.json()
}

export const sendChatMessage = async (domain, question) => {
  const { response } = await apiFetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ domain, question }),
  })
  if (!response.ok) {
    throw new Error('Failed to send chat message')
  }
  return response.json()
}

export const getProofs = async (domain, query) => {
  const { response } = await apiFetch(
    `/proofs/${encodeURIComponent(domain)}?query=${encodeURIComponent(query)}`
  )
  if (!response.ok) {
    throw new Error('Failed to load proofs')
  }
  return response.json()
}
