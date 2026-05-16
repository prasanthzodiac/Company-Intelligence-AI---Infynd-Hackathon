import React, { useState, useEffect } from 'react'
import Sidebar from './components/Sidebar'
import MainContent from './components/MainContent'
import ChatPanel from './components/ChatPanel'
import UploadScreen from './components/UploadScreen'
import CompanySelector from './components/CompanySelector'
import { getCompanies, getCompanyProfile } from './services/api'
import './App.css'

function App() {
  const [showUpload, setShowUpload] = useState(true)
  const [companies, setCompanies] = useState([])
  const [selectedDomain, setSelectedDomain] = useState(null)
  const [profile, setProfile] = useState(null)
  const [activePage, setActivePage] = useState('company-info')
  const [loading, setLoading] = useState(true)
  const [showCompanySelector, setShowCompanySelector] = useState(false)

  useEffect(() => {
    if (!showUpload) {
      loadCompanies()
    }
  }, [showUpload])

  // Sync simple views (upload → selector → main) with browser history
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

    // Initial state
    if (!window.history.state) {
      window.history.replaceState({ view: 'upload' }, 'Upload', '#upload')
    }

    return () => {
      window.removeEventListener('popstate', handlePopState)
    }
  }, [])

  useEffect(() => {
    if (selectedDomain && !showUpload) {
      loadProfile(selectedDomain)
    }
  }, [selectedDomain, showUpload])

  const loadCompanies = async () => {
    try {
      const data = await getCompanies()
      setCompanies(data)
      if (data.length > 0) {
        setShowCompanySelector(true)
        if (typeof window !== 'undefined') {
          window.history.pushState({ view: 'selector' }, 'Companies', '#companies')
        }
      }
    } catch (error) {
      console.error('Error loading companies:', error)
      alert(
        `Could not load companies from API: ${error.message}\n\n` +
          'Confirm VITE_API_BASE_URL on Vercel points to your Render URL + /api, then redeploy.'
      )
    } finally {
      setLoading(false)
    }
  }

  const loadProfile = async (domain) => {
    try {
      setLoading(true)
      const data = await getCompanyProfile(domain)
      setProfile(data)
    } catch (error) {
      console.error('Error loading profile:', error)
      setProfile(null)
    } finally {
      setLoading(false)
    }
  }

  const handleDomainChange = (domain) => {
    setSelectedDomain(domain)
    setShowCompanySelector(false)
    if (typeof window !== 'undefined') {
      window.history.pushState({ view: 'company', domain }, `Company: ${domain}`, `#company-${domain}`)
    }
  }

  const handleProcessingComplete = () => {
    setShowUpload(false)
    loadCompanies()
    if (typeof window !== 'undefined') {
      window.history.pushState({ view: 'selector' }, 'Companies', '#companies')
    }
  }

  if (showUpload) {
    return <UploadScreen onProcessingComplete={handleProcessingComplete} />
  }

  if (showCompanySelector) {
    return <CompanySelector companies={companies} onSelect={handleDomainChange} />
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
