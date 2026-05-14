import React from 'react'
import './Page.css'

function ReportsPage({ profile, selectedDomain, loading }) {
  const handleExport = (format) => {
    if (!profile) {
      alert('No profile data available to export')
      return
    }

    let dataStr = ''
    let dataUri = ''
    let filename = `${selectedDomain || 'company'}_report.${format}`

    if (format === 'json') {
      dataStr = JSON.stringify(profile, null, 2)
      dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr)
    } else if (format === 'csv') {
      // Simple CSV conversion
      const rows = []
      rows.push(['Field', 'Value'])
      Object.entries(profile).forEach(([key, value]) => {
        if (typeof value === 'object' && value !== null) {
          rows.push([key, JSON.stringify(value)])
        } else {
          rows.push([key, value || ''])
        }
      })
      dataStr = rows.map((row) => row.map((cell) => `"${cell}"`).join(',')).join('\n')
      dataUri = 'data:text/csv;charset=utf-8,' + encodeURIComponent(dataStr)
    } else {
      alert('PDF export coming soon')
      return
    }

    const exportFileDefaultName = filename
    const linkElement = document.createElement('a')
    linkElement.setAttribute('href', dataUri)
    linkElement.setAttribute('download', exportFileDefaultName)
    linkElement.click()
  }

  if (loading) {
    return (
      <div className="page active">
        <section className="card">
          <div className="card-title">Reports & Exports</div>
          <div className="skeleton" style={{ height: '200px', width: '100%' }}></div>
        </section>
      </div>
    )
  }

  return (
    <div className="page active">
      <section className="card">
        <div className="card-title">Reports & Exports</div>
        <div style={{ marginBottom: '20px', fontSize: '12px', color: '#9ca3af' }}>
          Generate and export company intelligence reports in various formats.
        </div>
        <div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ padding: '16px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a' }}>
              <div style={{ fontWeight: 600, marginBottom: '8px', color: '#ffffff' }}>Export Options</div>
              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                <button
                  className="export-btn"
                  onClick={() => handleExport('json')}
                  style={{
                    padding: '8px 16px',
                    background: '#ff5c4d',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '13px',
                    transition: 'background 0.2s',
                  }}
                  onMouseEnter={(e) => e.target.style.background = '#ff3d2a'}
                  onMouseLeave={(e) => e.target.style.background = '#ff5c4d'}
                >
                  Export as JSON
                </button>
                <button
                  className="export-btn"
                  onClick={() => handleExport('csv')}
                  style={{
                    padding: '8px 16px',
                    background: '#ff5c4d',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '13px',
                    transition: 'background 0.2s',
                  }}
                  onMouseEnter={(e) => e.target.style.background = '#ff3d2a'}
                  onMouseLeave={(e) => e.target.style.background = '#ff5c4d'}
                >
                  Export as CSV
                </button>
                <button
                  className="export-btn"
                  onClick={() => handleExport('pdf')}
                  style={{
                    padding: '8px 16px',
                    background: '#ff5c4d',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '13px',
                    transition: 'background 0.2s',
                  }}
                  onMouseEnter={(e) => e.target.style.background = '#ff3d2a'}
                  onMouseLeave={(e) => e.target.style.background = '#ff5c4d'}
                >
                  Export as PDF
                </button>
              </div>
            </div>
            <div style={{ padding: '16px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a' }}>
              <div style={{ fontWeight: 600, marginBottom: '8px', color: '#ffffff' }}>Report Summary</div>
              <div style={{ fontSize: '13px', color: '#9ca3af', whiteSpace: 'pre-line' }}>
                {profile
                  ? `Company: ${profile.company_name || selectedDomain || 'Unknown'}\nDomain: ${selectedDomain || '—'}\nIndustry: ${profile.industry || '—'}`
                  : 'Select a company to generate report summary...'}
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

export default ReportsPage

