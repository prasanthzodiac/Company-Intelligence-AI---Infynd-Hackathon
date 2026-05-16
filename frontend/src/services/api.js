/**
 * API client — all data is scoped to an ephemeral browser session (sessionStorage).
 */
import {
  clearSessionId,
  getSessionId,
  setSessionId,
} from './session.js'

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

function sessionHeaders(extra = {}) {
  const sid = getSessionId()
  const headers = { ...extra }
  if (sid) {
    headers['X-Session-Id'] = sid
  }
  return headers
}

/**
 * Create a new server session (empty data). Call on app load.
 */
export async function createSession() {
  const { response, url } = await apiFetch('/session', {
    method: 'POST',
    skipSession: true,
  })
  if (!response.ok) {
    throw new Error(`Failed to start session (${response.status})`)
  }
  const data = await response.json()
  if (!data.session_id) {
    throw new Error('Invalid session response from API')
  }
  setSessionId(data.session_id)
  return data.session_id
}

/**
 * Delete server-side session data (tab close).
 */
export function endSessionBeacon() {
  const sid = getSessionId()
  if (!sid) return
  const url = `${API_BASE}/session?session_id=${encodeURIComponent(sid)}`
  try {
    fetch(url, {
      method: 'DELETE',
      headers: { 'X-Session-Id': sid },
      keepalive: true,
    }).catch(() => {})
  } finally {
    clearSessionId()
  }
}

export async function ensureSession() {
  if (getSessionId()) {
    return getSessionId()
  }
  return createSession()
}

export async function resetSession() {
  const sid = getSessionId()
  if (sid) {
    const url = `${API_BASE}/session?session_id=${encodeURIComponent(sid)}`
    try {
      await fetch(url, { method: 'DELETE', headers: { 'X-Session-Id': sid } })
    } catch {
      /* ignore */
    }
    clearSessionId()
  }
  return createSession()
}

export async function apiFetch(path, options = {}) {
  const { skipSession, headers: extraHeaders, ...rest } = options
  const url = path.startsWith('http')
    ? path
    : `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`
  const headers = skipSession
    ? { ...extraHeaders }
    : sessionHeaders(extraHeaders)

  try {
    const response = await fetch(url, { ...rest, headers })
    return { response, url }
  } catch (err) {
    const msg = err?.message || String(err)
    if (msg === 'Failed to fetch' || err instanceof TypeError) {
      throw new Error(
        `Cannot reach API at ${url}. Check Render is running and VITE_API_BASE_URL is set on Vercel.`
      )
    }
    throw err
  }
}

export const getCompanies = async () => {
  await ensureSession()
  const { response } = await apiFetch('/companies')
  if (!response.ok) {
    const body = await response.text().catch(() => '')
    throw new Error(`Failed to load companies (${response.status}): ${body || response.statusText}`)
  }
  return response.json()
}

export const getCompanyProfile = async (domain) => {
  await ensureSession()
  const { response } = await apiFetch(`/companies/${encodeURIComponent(domain)}/profile`)
  if (!response.ok) {
    throw new Error('Failed to load profile')
  }
  return response.json()
}

/**
 * @returns {{ chunks: array, message?: string|null }}
 */
export const getCompanyChunks = async (domain) => {
  await ensureSession()
  const { response } = await apiFetch(`/companies/${encodeURIComponent(domain)}/chunks`)
  let body = {}
  try {
    body = await response.json()
  } catch {
    body = {}
  }

  if (!response.ok) {
    return {
      chunks: [],
      message:
        body.error ||
        `Could not load scraped data (${response.status}). Check your session and try uploading again.`,
    }
  }

  if (Array.isArray(body)) {
    return {
      chunks: body,
      message: body.length ? null : 'No scraped content for this domain yet.',
    }
  }

  return {
    chunks: Array.isArray(body.chunks) ? body.chunks : [],
    message: body.message || null,
  }
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
