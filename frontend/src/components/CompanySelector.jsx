import React from 'react'
import './CompanySelector.css'

function CompanySelector({ companies, onSelect }) {
  if (!companies || companies.length === 0) {
    return (
      <div className="company-selector-shell">
        <div className="company-selector-center">
          <div className="company-selector-title">Loading companies…</div>
          <div className="company-selector-subtitle">
            Once your ingestion finishes, you&apos;ll see companies here to explore.
          </div>
        </div>
      </div>
    )
  }

  const renderInitials = (domain) => {
    if (!domain) return '—'
    const base = domain.replace(/^www\./i, '').split('.')[0]
    if (!base) return domain[0]?.toUpperCase() || '—'
    return base[0]?.toUpperCase() || '—'
  }

  return (
    <div className="company-selector-shell">
      <header className="company-selector-header">
        <div className="sidebar-logo">
          <span className="logo-text-red">In</span>
          <span className="logo-text-white">Fynd</span>
          <span className="logo-subtitle">COMPANY INTELLIGENCE AI</span>
        </div>
      </header>

      <main className="company-selector-main">
        <div className="company-selector-copy">
          <h1>Choose a company workspace</h1>
          <p>
            Pick a company to open its full intelligence workspace – overview, people, services,
            certifications and more.
          </p>
        </div>

        <div className="company-grid">
          {companies.map((company, index) => {
            const domain = company.domain
            const initials = renderInitials(domain)
            const delay = (index % 6) * 0.12
            const logoUrl = `https://www.google.com/s2/favicons?domain=${encodeURIComponent(
              domain
            )}&sz=128`

            return (
              <button
                key={domain}
                className="company-card"
                style={{ animationDelay: `${delay}s` }}
                onClick={() => onSelect(domain)}
              >
                <div className="company-card-inner">
                  <div className="company-card-icon-large">
                    <img src={logoUrl} alt={domain} className="company-card-logo-img" />
                    <span className="company-card-initial">{initials}</span>
                  </div>
                  <div className="company-card-body centered">
                    <div className="company-card-title">{domain}</div>
                    <div className="company-card-subtitle">Company Intelligence Workspace</div>
                  </div>
                  <div className="company-card-footer centered-footer">Open workspace</div>
                </div>
              </button>
            )
          })}
        </div>
      </main>
    </div>
  )
}

export default CompanySelector


