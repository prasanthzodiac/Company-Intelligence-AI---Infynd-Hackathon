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

const PROCESSING_KEY = 'company_intel_processing'

export function setProcessingActive(active) {
  if (typeof window === 'undefined') return
  if (active) {
    sessionStorage.setItem(PROCESSING_KEY, '1')
  } else {
    sessionStorage.removeItem(PROCESSING_KEY)
  }
}

export function isProcessingActive() {
  if (typeof window === 'undefined') return false
  return sessionStorage.getItem(PROCESSING_KEY) === '1'
}
