import React from 'react'
import './Page.css'

function SocialPage({ profile, loading }) {
  if (loading) {
    return (
      <div className="page active">
        <section className="card">
          <div className="card-title">Social Media & Content</div>
          <div className="skeleton" style={{ height: '200px', width: '100%' }}></div>
        </section>
      </div>
    )
  }

  // Create default profile structure if profile is null
  const defaultProfile = {
    domain: '',
    social: {
      linkedin: '',
      youtube: '',
      x: '',
      facebook: '',
      instagram: '',
      github: '',
      blog: '',
      articles: ''
    }
  }

  const displayProfile = profile || defaultProfile
  const social = displayProfile.social || {}
  const domain = displayProfile.domain || ''
  const socialLinks = [
    { key: 'linkedin', label: 'linkedin' },
    { key: 'youtube', label: 'youtube' },
    { key: 'x', label: 'x' },
    { key: 'facebook', label: 'facebook' },
    { key: 'instagram', label: 'instagram' },
    { key: 'github', label: 'github' },
    { key: 'blog', label: 'blog' },
    { key: 'articles', label: 'articles' },
  ]

  return (
    <div className="page active">
      <section className="card">
        <div className="card-title" style={{ fontSize: '18px', marginBottom: '16px' }}>Social Media & Content</div>
        <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '12px' }}>
          Social handles and content links are shown in stacked rows similar to the phone section.
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {/* Domain row - separate boxed row like phone numbers */}
          <div
            style={{
              padding: '12px',
              background: '#1f1f1f',
              borderRadius: '8px',
              border: '1px solid #2a2a2a',
            }}
          >
            <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '4px' }}>Domain</div>
            <div style={{ fontSize: '14px', fontWeight: 500, color: '#ffffff' }}>{domain || '—'}</div>
          </div>

          {/* Social rows - each in its own boxed row */}
          {socialLinks.map((link) => {
            const value = social[link.key]
            const hasValue = value && value.toString().trim()
            return (
              <div
                key={link.key}
                style={{
                  padding: '12px',
                  background: '#1f1f1f',
                  borderRadius: '8px',
                  border: '1px solid #2a2a2a',
                  opacity: hasValue ? 1 : 0.6,
                }}
              >
                <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '4px' }}>{link.label}</div>
                <div style={{ fontSize: '13px' }}>
                  {hasValue ? (
                    <a
                      href={value}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ color: '#ff5c4d', textDecoration: 'none', wordBreak: 'break-all' }}
                    >
                      {value}
                    </a>
                  ) : (
                    <span style={{ color: '#64748b' }}>—</span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </section>
    </div>
  )
}

export default SocialPage
