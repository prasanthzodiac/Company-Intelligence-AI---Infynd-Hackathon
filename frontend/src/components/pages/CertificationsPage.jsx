import React from 'react'
import './Page.css'

function CertificationsPage({ profile, loading }) {
  if (loading) {
    return (
      <div className="page active">
        <section className="card">
          <div className="card-title">Certifications</div>
          <div className="skeleton" style={{ height: '200px', width: '100%' }}></div>
        </section>
      </div>
    )
  }

  // Create default profile structure if profile is null
  const defaultProfile = {
    certifications: []
  }
  
  const displayProfile = profile || defaultProfile
  const certs = displayProfile.certifications || []

  return (
    <div className="page active">
      <section className="card">
        <div className="card-title" style={{ fontSize: '18px', marginBottom: '16px' }}>Certifications</div>
        {certs.length > 0 ? (
          <>
            <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '20px' }}>
              {certs.length} certification{certs.length !== 1 ? 's' : ''} found
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
              {certs.map((cert, idx) => (
            <div
              key={idx}
              style={{
                padding: '16px',
                background: '#1f1f1f',
                borderRadius: '8px',
                border: '1px solid #2a2a2a',
                transition: 'border-color 0.2s',
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
              }}
              onMouseEnter={(e) => e.currentTarget.style.borderColor = '#ff5c4d'}
              onMouseLeave={(e) => e.currentTarget.style.borderColor = '#2a2a2a'}
            >
              <div style={{
                width: '40px',
                height: '40px',
                borderRadius: '8px',
                background: '#ff5c4d',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '18px',
                fontWeight: 700,
                color: '#ffffff',
                flexShrink: 0,
              }}>
                ✓
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '14px', fontWeight: 600, color: '#ffffff' }}>
                  {typeof cert === 'string' ? cert : (cert.name || cert)}
                </div>
                {typeof cert === 'object' && cert.description && (
                  <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '4px' }}>
                    {cert.description}
                  </div>
                )}
                {typeof cert === 'object' && cert.issued_date && (
                  <div style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
                    Issued: {cert.issued_date}
                  </div>
                )}
              </div>
            </div>
          ))}
            </div>
          </>
        ) : (
          <div style={{ padding: '40px', textAlign: 'center', color: '#9ca3af' }}>
            No certifications detected.
          </div>
        )}
      </section>
    </div>
  )
}

export default CertificationsPage
