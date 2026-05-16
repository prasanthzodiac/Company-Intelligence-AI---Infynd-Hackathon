import React, { useState, useEffect, useCallback } from 'react'
import Sidebar from './components/Sidebar'
import MainContent from './components/MainContent'
import ChatPanel from './components/ChatPanel'
import UploadScreen from './components/UploadScreen'
import CompanySelector from './components/CompanySelector'
import { getCompanies, getCompanyProfile, isProductionSameOriginApi } from './services/api'
import './App.css'

function App() {
  const [showUpload, setShowUpload] = useState(true)
  const [companies, setCompanies] = useState([])
  const [selectedDomain, setSelectedDomain] = useState(null)
  const [profile, setProfile] = useState(null)
  const [activePage, setActivePage] = useState('company-info')
  const [loading, setLoading] = useState(true)
  const [showCompanySelector, setShowCompanySelector] = useState(false)
  const [loadError, setLoadError] = useState(null)

  const loadCompanies = useCallback(async (retries = 2) => {
    setLoadError(null)
    let lastError = null
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
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
    if (isProductionSameOriginApi()) {
      setLoading(false)
      return
    }
    ;(async () => {
      const data = await loadCompanies(1)
      if (data.length > 0) {
        setShowUpload(false)
      }
      setLoading(false)
    })()
  }, [loadCompanies])

  useEffect(() => {
    if (!showUpload) {
      setLoading(true)
      loadCompanies().finally(() => setLoading(false))
    }
  }, [showUpload, loadCompanies])

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
        if (domain) {
          setSelectedDomain(domain)
        }
      }
    }

    window.addEventListener('popstate', handlePopState)

    if (!window.history.state) {
      window.history.replaceState({ view: 'upload' }, 'Upload', '#upload')
    }

    return () => {
      window.removeEventListener('popstate', handlePopState)
    }
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
      alert(
        `Could not load profile for ${domain}: ${error.message}\n\n` +
          'Try another company or re-run extraction from the upload screen.'
      )
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
        'Processing finished but no companies were found.\n\n' +
          'Check Render logs for pipeline errors, confirm LLM env vars, and ensure your CSV has a "domain" column.'
      )
      setShowUpload(true)
      return
    }

    if (typeof window !== 'undefined') {
      window.history.pushState({ view: 'selector' }, 'Companies', '#companies')
    }
  }

  if (loading && !showUpload && companies.length === 0 && !showCompanySelector) {
    return (
      <div className="app-loading-screen">
        <p>Loading company data…</p>
      </div>
    )
  }

  if (showUpload) {
    return <UploadScreen onProcessingComplete={handleProcessingComplete} />
  }

  if (showCompanySelector || !selectedDomain) {
    return (
      <CompanySelector
        companies={companies}
        loadError={loadError}
        onSelect={handleDomainChange}
        onBackToUpload={() => {
          setShowUpload(true)
          setShowCompanySelector(false)
        }}
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
