import React from 'react'
import './Page.css'

function ContactPage({ profile, selectedDomain, loading }) {
  if (loading) {
    return (
      <div className="page active">
        <section className="card">
          <div className="card-title">Contact Information</div>
          <div className="skeleton" style={{ height: '200px', width: '100%' }}></div>
        </section>
      </div>
    )
  }

  // Create default profile structure if profile is null
  const defaultProfile = {
    contact: {
      domain: selectedDomain || '',
      company_name: '',
      full_address: '',
      phone: '',
      sales_phone: '',
      fax: '',
      mobile: '',
      other_numbers: [],
      email: '',
      hours_of_operation: '',
      hq_indicator: ''
    },
    domain: selectedDomain || ''
  }
  
  const displayProfile = profile || defaultProfile
  const contact = displayProfile.contact || {}
  
  // Normalize email - handle array case (backend should fix this, but add fallback)
  if (contact.email && Array.isArray(contact.email)) {
    contact.email = contact.email.find(e => typeof e === 'string' && e.includes('@')) || ''
  }

  // Helper to check if value exists
  const hasValue = (value) => {
    if (value === null || value === undefined) return false
    if (typeof value === 'string') return value.trim() !== ''
    if (Array.isArray(value)) return value.length > 0
    return true
  }

  return (
    <div className="page active">
      {/* Address Section - Always show */}
      <section className="card" style={{ marginBottom: '20px' }}>
        <div className="card-title" style={{ fontSize: '18px', marginBottom: '16px' }}>Address</div>
        {contact.full_address ? (
          <div style={{ padding: '16px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a' }}>
            <div style={{ fontSize: '14px', color: '#ffffff', lineHeight: '1.7', whiteSpace: 'pre-line' }}>
              {contact.full_address}
            </div>
          </div>
        ) : (
          <div style={{ padding: '16px', textAlign: 'center', color: '#9ca3af' }}>No address information available</div>
        )}
      </section>

      {/* Contact Details Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px', marginBottom: '20px' }}>
        {/* Phone Numbers - Always show all fields */}
        <section className="card">
          <div className="card-title" style={{ fontSize: '16px', marginBottom: '16px' }}>Phone Numbers</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ padding: '12px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a', opacity: contact.phone ? 1 : 0.6 }}>
              <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '4px' }}>Primary Phone</div>
              <div style={{ fontSize: '14px', fontWeight: 500, color: contact.phone ? '#ffffff' : '#64748b' }}>
                {contact.phone ? <a href={`tel:${contact.phone}`} style={{ color: '#ff5c4d' }}>{contact.phone}</a> : '—'}
              </div>
            </div>
            <div style={{ padding: '12px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a', opacity: contact.sales_phone ? 1 : 0.6 }}>
              <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '4px' }}>Sales Phone</div>
              <div style={{ fontSize: '14px', fontWeight: 500, color: contact.sales_phone ? '#ffffff' : '#64748b' }}>
                {contact.sales_phone ? <a href={`tel:${contact.sales_phone}`} style={{ color: '#ff5c4d' }}>{contact.sales_phone}</a> : '—'}
              </div>
            </div>
            <div style={{ padding: '12px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a', opacity: contact.mobile ? 1 : 0.6 }}>
              <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '4px' }}>Mobile</div>
              <div style={{ fontSize: '14px', fontWeight: 500, color: contact.mobile ? '#ffffff' : '#64748b' }}>
                {contact.mobile ? <a href={`tel:${contact.mobile}`} style={{ color: '#ff5c4d' }}>{contact.mobile}</a> : '—'}
              </div>
            </div>
            <div style={{ padding: '12px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a', opacity: contact.fax ? 1 : 0.6 }}>
              <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '4px' }}>Fax</div>
              <div style={{ fontSize: '14px', fontWeight: 500, color: contact.fax ? '#ffffff' : '#64748b' }}>
                {contact.fax || '—'}
              </div>
            </div>
            <div style={{ padding: '12px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a', opacity: (contact.other_numbers && contact.other_numbers.length > 0) ? 1 : 0.6 }}>
              <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '4px' }}>Other Numbers</div>
              <div style={{ fontSize: '14px', fontWeight: 500, color: (contact.other_numbers && contact.other_numbers.length > 0) ? '#ffffff' : '#64748b' }}>
                {contact.other_numbers && contact.other_numbers.length > 0 ? (
                  contact.other_numbers.map((num, idx) => (
                    <div key={idx}>
                      <a href={`tel:${num}`} style={{ color: '#ff5c4d' }}>{num}</a>
                    </div>
                  ))
                ) : '—'}
              </div>
            </div>
          </div>
        </section>

        {/* Email & Other Info - Always show all fields */}
        <section className="card">
          <div className="card-title" style={{ fontSize: '16px', marginBottom: '16px' }}>Email & Details</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ padding: '12px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a', opacity: contact.email ? 1 : 0.6 }}>
              <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '4px' }}>Email</div>
              <div style={{ fontSize: '14px', fontWeight: 500, color: contact.email ? '#ffffff' : '#64748b' }}>
                {contact.email ? <a href={`mailto:${contact.email}`} style={{ color: '#ff5c4d' }}>{contact.email}</a> : '—'}
              </div>
            </div>
            <div style={{ padding: '12px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a', opacity: contact.hours_of_operation ? 1 : 0.6 }}>
              <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '4px' }}>Hours of Operation</div>
              <div style={{ fontSize: '14px', fontWeight: 500, color: contact.hours_of_operation ? '#ffffff' : '#64748b', whiteSpace: 'pre-line' }}>
                {contact.hours_of_operation || '—'}
              </div>
            </div>
            <div style={{ padding: '12px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a' }}>
              <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '4px' }}>Domain</div>
              <div style={{ fontSize: '14px', fontWeight: 500, color: '#ffffff' }}>
                {contact.domain || displayProfile.domain || selectedDomain || '—'}
              </div>
            </div>
            <div style={{ padding: '12px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a' }}>
              <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '4px' }}>Company Name</div>
              <div style={{ fontSize: '14px', fontWeight: 500, color: '#ffffff' }}>
                {contact.company_name || displayProfile.company_name || '—'}
              </div>
            </div>
            <div style={{ padding: '12px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a', opacity: contact.hq_indicator ? 1 : 0.6 }}>
              <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '4px' }}>HQ Indicator</div>
              <div style={{ fontSize: '14px', fontWeight: 500, color: contact.hq_indicator ? '#ffffff' : '#64748b' }}>
                {contact.hq_indicator || '—'}
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}

export default ContactPage
