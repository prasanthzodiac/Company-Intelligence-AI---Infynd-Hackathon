import React from 'react'
import './Page.css'

function PeoplePage({ profile, loading }) {
  if (loading) {
    return (
      <div className="page active">
        <section className="card">
          <div className="card-title">People & Team</div>
          <div className="skeleton" style={{ height: '200px', width: '100%' }}></div>
        </section>
      </div>
    )
  }

  // Create default profile structure if profile is null
  const defaultProfile = {
    domain: '',
    people: [],
    leadership: []
  }

  const displayProfile = profile || defaultProfile
  const people = displayProfile.people || []
  const leadership = displayProfile.leadership || []
  const domain = displayProfile.domain || ''

  return (
    <div className="page active">
      {/* Leadership Section - Always show */}
      <section className="card" style={{ marginBottom: '20px' }}>
        <div className="card-title" style={{ fontSize: '18px', marginBottom: '16px' }}>Leadership</div>
        <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '12px' }}>
          Leader details are shown in stacked rows similar to the phone section.
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {(leadership.length > 0 ? leadership : [{}]).map((person, idx) => {
            const name = person.name || person.people_name
            const title = person.title || person.people_title
            const email = person.email || person.people_email
            const url = person.url
            return (
              <div
                key={idx}
                style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}
              >
                {/* Domain box */}
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

                {/* Leader name box */}
                <div
                  style={{
                    padding: '12px',
                    background: '#1f1f1f',
                    borderRadius: '8px',
                    border: '1px solid #2a2a2a',
                    opacity: name ? 1 : 0.6,
                  }}
                >
                  <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '4px' }}>Leader Name</div>
                  <div style={{ fontSize: '14px', fontWeight: 500, color: name ? '#ffffff' : '#64748b' }}>{name || '—'}</div>
                </div>

                {/* Leader title box */}
                <div
                  style={{
                    padding: '12px',
                    background: '#1f1f1f',
                    borderRadius: '8px',
                    border: '1px solid #2a2a2a',
                    opacity: title ? 1 : 0.6,
                  }}
                >
                  <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '4px' }}>Leader Title</div>
                  <div style={{ fontSize: '14px', fontWeight: 500, color: title ? '#ffffff' : '#64748b' }}>{title || '—'}</div>
                </div>

                {/* Leader email box */}
                <div
                  style={{
                    padding: '12px',
                    background: '#1f1f1f',
                    borderRadius: '8px',
                    border: '1px solid #2a2a2a',
                    opacity: email ? 1 : 0.6,
                  }}
                >
                  <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '4px' }}>Leader Email</div>
                  <div style={{ fontSize: '13px' }}>
                    {email ? (
                      <a href={`mailto:${email}`} style={{ color: '#ff5c4d', textDecoration: 'none' }}>
                        {email}
                      </a>
                    ) : (
                      <span style={{ color: '#64748b' }}>—</span>
                    )}
                  </div>
                </div>

                {/* URL box */}
                <div
                  style={{
                    padding: '12px',
                    background: '#1f1f1f',
                    borderRadius: '8px',
                    border: '1px solid #2a2a2a',
                    opacity: url ? 1 : 0.6,
                  }}
                >
                  <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '4px' }}>URL</div>
                  <div style={{ fontSize: '13px' }}>
                    {url ? (
                      <a
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ color: '#ff5c4d', textDecoration: 'none' }}
                      >
                        Profile
                      </a>
                    ) : (
                      <span style={{ color: '#64748b' }}>—</span>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </section>

      {/* People/Team Section - Always show */}
      <section className="card">
        <div className="card-title" style={{ fontSize: '18px', marginBottom: '16px' }}>People</div>
        <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '12px' }}>
          People details are shown in stacked rows similar to the phone section.
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {(people.length > 0 ? people : [{}]).map((person, idx) => {
            const name = person.people_name || person.name
            const title = person.people_title || person.title
            const email = person.people_email || person.email
            const url = person.url
            return (
              <div
                key={idx}
                style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}
              >
                {/* Domain box */}
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

                {/* People name box */}
                <div
                  style={{
                    padding: '12px',
                    background: '#1f1f1f',
                    borderRadius: '8px',
                    border: '1px solid #2a2a2a',
                    opacity: name ? 1 : 0.6,
                  }}
                >
                  <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '4px' }}>People Name</div>
                  <div style={{ fontSize: '14px', fontWeight: 500, color: name ? '#ffffff' : '#64748b' }}>{name || '—'}</div>
                </div>

                {/* People title box */}
                <div
                  style={{
                    padding: '12px',
                    background: '#1f1f1f',
                    borderRadius: '8px',
                    border: '1px solid #2a2a2a',
                    opacity: title ? 1 : 0.6,
                  }}
                >
                  <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '4px' }}>People Title</div>
                  <div style={{ fontSize: '14px', fontWeight: 500, color: title ? '#ffffff' : '#64748b' }}>{title || '—'}</div>
                </div>

                {/* People email box */}
                <div
                  style={{
                    padding: '12px',
                    background: '#1f1f1f',
                    borderRadius: '8px',
                    border: '1px solid #2a2a2a',
                    opacity: email ? 1 : 0.6,
                  }}
                >
                  <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '4px' }}>People Email</div>
                  <div style={{ fontSize: '13px' }}>
                    {email ? (
                      <a href={`mailto:${email}`} style={{ color: '#ff5c4d', textDecoration: 'none' }}>
                        {email}
                      </a>
                    ) : (
                      <span style={{ color: '#64748b' }}>—</span>
                    )}
                  </div>
                </div>

                {/* URL box */}
                <div
                  style={{
                    padding: '12px',
                    background: '#1f1f1f',
                    borderRadius: '8px',
                    border: '1px solid #2a2a2a',
                    opacity: url ? 1 : 0.6,
                  }}
                >
                  <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '4px' }}>URL</div>
                  <div style={{ fontSize: '13px' }}>
                    {url ? (
                      <a
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ color: '#ff5c4d', textDecoration: 'none' }}
                      >
                        Profile
                      </a>
                    ) : (
                      <span style={{ color: '#64748b' }}>—</span>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </section>
    </div>
  )
}

export default PeoplePage
