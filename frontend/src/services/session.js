/**
 * Ephemeral browser session — data is deleted when the tab closes.
 */
const STORAGE_KEY = 'company_intel_session_id'

export function getSessionId() {
  if (typeof window === 'undefined') return null
  return sessionStorage.getItem(STORAGE_KEY)
}

export function setSessionId(sessionId) {
  if (typeof window === 'undefined') return
  sessionStorage.setItem(STORAGE_KEY, sessionId)
}

export function clearSessionId() {
  if (typeof window === 'undefined') return
  sessionStorage.removeItem(STORAGE_KEY)
}
