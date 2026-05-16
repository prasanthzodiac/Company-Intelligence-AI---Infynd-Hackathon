import React from 'react'
import CompanyInfoPage from './pages/CompanyInfoPage'
import ServicesPage from './pages/ServicesPage'
import PeoplePage from './pages/PeoplePage'
import CertificationsPage from './pages/CertificationsPage'
import ContactPage from './pages/ContactPage'
import SocialPage from './pages/SocialPage'
import KnowledgeGraphPage from './pages/KnowledgeGraphPage'
import ReportsPage from './pages/ReportsPage'
import RawScrapedDataPage from './pages/RawScrapedDataPage'
import './MainContent.css'

function MainContent({ companies, selectedDomain, profile, activePage, loading, onDomainChange }) {
  const renderPage = () => {
    switch (activePage) {
      case 'company-info':
        return <CompanyInfoPage profile={profile} selectedDomain={selectedDomain} loading={loading} />
      case 'services':
        return <ServicesPage profile={profile} loading={loading} />
      case 'people':
        return <PeoplePage profile={profile} loading={loading} />
      case 'certifications':
        return <CertificationsPage profile={profile} loading={loading} />
      case 'contact':
        return <ContactPage profile={profile} selectedDomain={selectedDomain} loading={loading} />
      case 'social':
        return <SocialPage profile={profile} loading={loading} />
      case 'knowledge-graph':
        return <KnowledgeGraphPage profile={profile} loading={loading} />
      case 'reports':
        return <ReportsPage profile={profile} selectedDomain={selectedDomain} loading={loading} />
      case 'raw-scraped':
        return <RawScrapedDataPage selectedDomain={selectedDomain} loading={loading} />
      default:
        return <CompanyInfoPage profile={profile} selectedDomain={selectedDomain} loading={loading} />
    }
  }

  return (
    <main className="main-column">
      <div className="top-bar">
        <div />
        <span className="badge">Live extraction · session data</span>
      </div>

      <div className="content-scroll">{renderPage()}</div>
    </main>
  )
}

export default MainContent

