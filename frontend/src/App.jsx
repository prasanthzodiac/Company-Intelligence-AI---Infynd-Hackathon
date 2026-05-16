import React, { useState, useEffect, useCallback } from 'react'
import Sidebar from './components/Sidebar'
import MainContent from './components/MainContent'
import ChatPanel from './components/ChatPanel'
import UploadScreen from './components/UploadScreen'
import CompanySelector from './components/CompanySelector'
import {
  endSessionBeacon,
  ensureSession,
  getCompanies,
  getCompanyProfile,
  resetSession,
} from './services/api'
import './App.css'

function App() {
  const [sessionReady, setSessionReady] = useState(false)
  const [showUpload, setShowUpload] = useState(true)
  const [companies, setCompanies] = useState([])
  const [selectedDomain, setSelectedDomain] = useState(null)
  const [profile, setProfile] = useState(null)
  const [activePage, setActivePage] = useState('company-info')
  const [loading, setLoading] = useState(true)
  const [showCompanySelector, setShowCompanySelector] = useState(false)
  const [loadError, setLoadError] = useState(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        await ensureSession()
        if (!cancelled) {
          setSessionReady(true)
          setLoading(false)
        }
      } catch (e) {
        console.error(e)
        if (!cancelled) {
          alert(`Could not start a session: ${e.message}`)
          setLoading(false)
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    const onLeave = () => endSessionBeacon()
    window.addEventListener('pagehide', onLeave)
    window.addEventListener('beforeunload', onLeave)
    return () => {
      window.removeEventListener('pagehide', onLeave)
      window.removeEventListener('beforeunload', onLeave)
    }
  }, [])

  const loadCompanies = useCallback(async (retries = 2) => {
    setLoadError(null)
    let lastError = null
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        await ensureSession()
        const data = await getCompanies()
        const list = Array.isArray(data) ? data : []
        setCompanies(list)
        if (list.length > 0) {
          setShowCompanySelector(true)
          if (typeof window !== 'undefined') {
            window.history.pushState({ view: 'selector' }, 'Companies', '#companies')
          }
        }
        return list
      } catch (error) {
        lastError = error
        console.error('Error loading companies:', error)
        if (attempt < retries) {
          await new Promise((r) => setTimeout(r, 1500))
        }
      }
    }
    setLoadError(lastError?.message || 'Failed to load companies')
    return []
  }, [])

  useEffect(() => {
    if (typeof window === 'undefined') return

    const handlePopState = (event) => {
      const view = event.state?.view
      if (view === 'upload') {
        setShowUpload(true)
        setShowCompanySelector(false)
        return
      }
      if (view === 'selector') {
        setShowUpload(false)
        setShowCompanySelector(true)
        return
      }
      if (view === 'company') {
        const domain = event.state?.domain
        setShowUpload(false)
        setShowCompanySelector(false)
        if (domain) setSelectedDomain(domain)
      }
    }

    window.addEventListener('popstate', handlePopState)
    if (!window.history.state) {
      window.history.replaceState({ view: 'upload' }, 'Upload', '#upload')
    }
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  useEffect(() => {
    if (selectedDomain && !showUpload && !showCompanySelector) {
      loadProfile(selectedDomain)
    }
  }, [selectedDomain, showUpload, showCompanySelector])

  const loadProfile = async (domain) => {
    try {
      setLoading(true)
      const data = await getCompanyProfile(domain)
      setProfile(data)
    } catch (error) {
      console.error('Error loading profile:', error)
      setProfile(null)
      alert(`Could not load profile for ${domain}: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleDomainChange = (domain) => {
    setSelectedDomain(domain)
    setShowCompanySelector(false)
    setProfile(null)
    if (typeof window !== 'undefined') {
      window.history.pushState(
        { view: 'company', domain },
        `Company: ${domain}`,
        `#company-${domain}`
      )
    }
  }

  const handleProcessingComplete = async () => {
    setShowUpload(false)
    setLoading(true)
    const data = await loadCompanies(3)
    setLoading(false)

    if (data.length === 0) {
      alert(
        'Processing finished but no companies were found. Check Render logs and your CSV format (domain column).'
      )
      setShowUpload(true)
      return
    }

    if (typeof window !== 'undefined') {
      window.history.pushState({ view: 'selector' }, 'Companies', '#companies')
    }
  }

  const handleStartOver = async () => {
    setCompanies([])
    setSelectedDomain(null)
    setProfile(null)
    setShowCompanySelector(false)
    setShowUpload(true)
    setLoading(true)
    try {
      await resetSession()
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  if (!sessionReady || (loading && !showUpload && companies.length === 0 && !showCompanySelector)) {
    return (
      <div className="app-loading-screen">
        <p>Starting secure session…</p>
      </div>
    )
  }

  if (showUpload) {
    return (
      <UploadScreen
        onProcessingComplete={handleProcessingComplete}
        onStartOver={handleStartOver}
      />
    )
  }

  if (showCompanySelector || !selectedDomain) {
    return (
      <CompanySelector
        companies={companies}
        loadError={loadError}
        onSelect={handleDomainChange}
        onBackToUpload={handleStartOver}
      />
    )
  }

  return (
    <div className="app-shell">
      <Sidebar activePage={activePage} onPageChange={setActivePage} />
      <MainContent
        companies={companies}
        selectedDomain={selectedDomain}
        profile={profile}
        activePage={activePage}
        loading={loading}
        onDomainChange={handleDomainChange}
      />
      <ChatPanel selectedDomain={selectedDomain} profile={profile} />
    </div>
  )
}

export default App
