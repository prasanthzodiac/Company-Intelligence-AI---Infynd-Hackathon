import React, { useState, useEffect } from 'react'
import { getCompanyChunks } from '../../services/api'
import ProofBadge from '../ProofBadge'
import '../pages/Page.css'

function CompanyInfoPage({ profile, selectedDomain, loading }) {
  const [chunks, setChunks] = useState([])
  const [logoError, setLogoError] = useState(false)
  const [logoUrlOverride, setLogoUrlOverride] = useState(null)
  const [chunksLoading, setChunksLoading] = useState(true)

  useEffect(() => {
    if (selectedDomain) {
      loadChunks()
    }
  }, [selectedDomain])

  const loadChunks = async () => {
    try {
      setChunksLoading(true)
      const data = await getCompanyChunks(selectedDomain)
      setChunks(data?.chunks || [])
    } catch (error) {
      console.error('Error loading chunks:', error)
      setChunks([])
    } finally {
      setChunksLoading(false)
    }
  }

  const getProofsForField = (fieldName, searchText) => {
    if (!chunks || !searchText || !searchText.toString().trim()) return []
    const proofs = []
    const searchLower = searchText.toString().toLowerCase()
    
    for (const chunk of chunks) {
      const text = (chunk.text || '').toLowerCase()
      const section = (chunk.section || '').toLowerCase()
      const structured = chunk.structured_data || {}
      
      // Check in text
      if (text.includes(searchLower)) {
        proofs.push({
          page: chunk.page,
          section: chunk.section,
          text: chunk.text,
          source_path: chunk.source_path,
        })
        if (proofs.length >= 3) break
      }
      // Check in structured data
      else if (structured[fieldName.toLowerCase()] || 
               (structured.company_details && structured.company_details[fieldName.toLowerCase()])) {
        proofs.push({
          page: chunk.page,
          section: chunk.section,
          text: chunk.text,
          source_path: chunk.source_path,
        })
        if (proofs.length >= 3) break
      }
    }
    return proofs
  }

  const domainToName = (domain) => {
    if (!domain) return ''
    const core = domain.replace(/^www\./i, '').split('.')[0] || domain
    if (!core || core === 'www') return domain
    const titled = core.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
    return titled.includes('Inc') ? titled : `${titled}`
  }

  // Helper to check if value exists and is not empty
  const hasValue = (value) => {
    if (value === null || value === undefined) return false
    if (typeof value === 'string') return value.trim() !== ''
    if (Array.isArray(value)) return value.length > 0
    if (typeof value === 'object') return Object.keys(value).length > 0
    return true
  }

  if (loading) {
    return (
      <div className="page active">
        <div className="card">
          <div className="card-title">Company Overview</div>
          <div className="skeleton" style={{ height: '24px', width: '200px', marginBottom: '10px' }}></div>
          <div className="skeleton" style={{ height: '100px', width: '100%' }}></div>
        </div>
      </div>
    )
  }

  // Create a default minimal profile if profile is null/undefined
  // This ensures we can still display the page with basic info from domain
  const defaultProfile = {
    company_name: profile?.company_name || (selectedDomain ? selectedDomain.split('.')[0].replace(/-/g, ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ') : 'Unknown Company'),
    domain: selectedDomain || '',
    description_short: '',
    description_long: '',
    industry: '',
    sub_industry: '',
    sectors: [],
    sector: '',
    ssc_code: '',
    sic_code: '',
    sic_text: '',
    tags: [],
    products: [],
    domain_status: '',
    company_registration: '',
    vat_number: '',
    acronym: '',
    logo_url: '',
    headquarters: '',
    locations: [],
    leadership: [],
    people: [],
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
    social: {
      linkedin: '',
      facebook: '',
      x: '',
      instagram: '',
      youtube: '',
      blog: '',
      articles: ''
    },
    certifications: [],
    services: [],
    business_type: '',
    company_size: '',
    technology_signals: [],
    extraction_confidence: 0.0,
    pipeline_status: '',
    pipeline_message: '',
  }
  
  // Use profile if available, otherwise use default
  const displayProfile = profile || defaultProfile
  const effectiveDomain = displayProfile?.domain || selectedDomain || ''
  const currentLogoUrl = !logoError ? (logoUrlOverride || displayProfile.logo_url || '') : ''
  
  if (!profile) {
    // Show a warning but still render the page with default data
    console.warn(`Profile not available for ${selectedDomain}, using default profile`)
  }

  return (
    <div className="page active">
      {/* Warning message if profile not loaded */}
      {(displayProfile.pipeline_message || !profile) && (
        <div
          className="card"
          style={{
            marginBottom: '20px',
            background: String(displayProfile.pipeline_status || '').includes('failed')
              ? '#3b1f1f'
              : '#3b2a1f',
            border: `1px solid ${String(displayProfile.pipeline_status || '').includes('failed') ? '#ef4444' : '#f59e0b'}`,
          }}
        >
          <div style={{ padding: '12px', color: '#fbbf24', fontSize: '13px' }}>
            {displayProfile.pipeline_message ||
              'Profile data not fully available. Wait for processing to finish or upload again.'}
          </div>
        </div>
      )}
      
      {/* Company Header Section */}
      <section className="card" style={{ marginBottom: '20px' }}>
        <div className="card-title">Company Information</div>
        <div style={{ marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
            {/* Company Logo / Avatar */}
            <div
              style={{
                width: '64px',
                height: '64px',
                borderRadius: '12px',
                background:
                  currentLogoUrl
                    ? '#111827'
                    : 'linear-gradient(135deg, #0f766e, #1d4ed8)',
                border: '1px solid #1f2937',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                overflow: 'hidden',
                flexShrink: 0,
              }}
            >
              {currentLogoUrl ? (
                <img
                  src={currentLogoUrl}
                  alt={`${displayProfile.company_name || effectiveDomain} logo`}
                  onError={() => setLogoError(true)}
                  style={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'contain',
                  }}
                />
              ) : (
                <span
                  style={{
                    fontSize: '20px',
                    fontWeight: 700,
                    color: '#e5e7eb',
                  }}
                >
                  {effectiveDomain
                    ? effectiveDomain
                        .split('.')[0]
                        .slice(0, 3)
                        .toUpperCase()
                    : '—'}
                </span>
              )}
            </div>
            <div style={{ flex: 1 }}>
              <div className="company-name" style={{ fontSize: '24px', fontWeight: 700, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                {displayProfile.company_name && displayProfile.company_name.trim()
                  ? displayProfile.company_name
                  : domainToName(selectedDomain)}
                {effectiveDomain && (
                  <span style={{ fontSize: '13px', fontWeight: 400, color: '#9ca3af' }}>
                    - "{effectiveDomain}"
                  </span>
                )}
                {displayProfile.company_name && (
                  <ProofBadge 
                    proofs={getProofsForField('company_name', displayProfile.company_name)} 
                    fieldName="Company Name"
                  />
                )}
              </div>
            </div>
          </div>
          {/* Logo helpers */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', gap: '12px' }}>
            <div style={{ fontSize: '11px', color: '#9ca3af' }}>
              Company name and logo are resolved from the extracted profile. You can also fetch a favicon-based logo from the live domain.
            </div>
            {effectiveDomain && !currentLogoUrl && (
              <button
                style={{
                  fontSize: '11px',
                  padding: '6px 10px',
                  borderRadius: '999px',
                  border: '1px solid #374151',
                  background: 'transparent',
                  color: '#e5e7eb',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                }}
                onClick={() => {
                  setLogoError(false)
                  setLogoUrlOverride(`https://${effectiveDomain}/favicon.ico`)
                }}
              >
                Fetch logo from domain
              </button>
            )}
          </div>
          
          {/* Short Description - always visible */}
          <div style={{ 
            fontSize: '15px', 
            color: hasValue(displayProfile.description_short) ? '#d1d5db' : '#64748b', 
            marginBottom: '16px', 
            lineHeight: '1.7',
            padding: '16px',
            background: '#1f1f1f',
            borderRadius: '8px',
            border: '1px solid #2a2a2a',
            opacity: hasValue(displayProfile.description_short) ? 1 : 0.75,
          }}>
            <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '8px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              Short Description
              {hasValue(displayProfile.description_short) && (
                <ProofBadge 
                  proofs={getProofsForField('description_short', displayProfile.description_short)} 
                  fieldName="Short Description"
                />
              )}
            </div>
            <div>
              {hasValue(displayProfile.description_short) ? displayProfile.description_short : '—'}
            </div>
          </div>

          {/* Long Description - always visible */}
          <div style={{ 
            fontSize: '14px', 
            lineHeight: '1.7', 
            color: hasValue(displayProfile.description_long) ? '#d1d5db' : '#64748b',
            padding: '16px',
            background: '#1f1f1f',
            borderRadius: '8px',
            border: '1px solid #2a2a2a',
            opacity: hasValue(displayProfile.description_long) ? 1 : 0.75,
          }}>
            <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '8px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              Detailed Description
              {hasValue(displayProfile.description_long) && (
                <ProofBadge 
                  proofs={getProofsForField('description_long', displayProfile.description_long)} 
                  fieldName="Long Description"
                />
              )}
            </div>
            <div style={{ whiteSpace: 'pre-wrap' }}>
              {hasValue(displayProfile.description_long) ? displayProfile.description_long : '—'}
            </div>
          </div>
        </div>
      </section>

      {/* Company Details Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px', marginBottom: '20px' }}>
        <section className="card">
          <div className="card-title" style={{ fontSize: '16px', marginBottom: '16px' }}>Basic Information</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div className="detail-pill" style={{ flexDirection: 'column', alignItems: 'flex-start', padding: '12px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a' }}>
              <div className="detail-label" style={{ fontSize: '11px', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                Domain
                {hasValue(displayProfile.domain || selectedDomain) && (
                  <ProofBadge 
                    proofs={getProofsForField('domain', displayProfile.domain || selectedDomain)} 
                    fieldName="Domain"
                  />
                )}
              </div>
              <div className="detail-value" style={{ fontSize: '14px', fontWeight: 500 }}>{displayProfile.domain || selectedDomain || '—'}</div>
            </div>
            <div className="detail-pill" style={{ flexDirection: 'column', alignItems: 'flex-start', padding: '12px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a', opacity: hasValue(currentLogoUrl || displayProfile.logo_url) ? 1 : 0.6 }}>
              <div className="detail-label" style={{ fontSize: '11px', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                Logo URL
                {hasValue(currentLogoUrl || displayProfile.logo_url) && (
                  <ProofBadge 
                    proofs={getProofsForField('logo_url', currentLogoUrl || displayProfile.logo_url)} 
                    fieldName="Logo URL"
                  />
                )}
              </div>
              <div className="detail-value" style={{ fontSize: '13px', wordBreak: 'break-all', color: hasValue(currentLogoUrl || displayProfile.logo_url) ? '#93c5fd' : '#64748b' }}>
                {currentLogoUrl || displayProfile.logo_url ? (
                  <a
                    href={currentLogoUrl || displayProfile.logo_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ color: '#93c5fd', textDecoration: 'none' }}
                  >
                    {currentLogoUrl || displayProfile.logo_url}
                  </a>
                ) : (
                  '—'
                )}
              </div>
            </div>
            <div className="detail-pill" style={{ flexDirection: 'column', alignItems: 'flex-start', padding: '12px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a', opacity: hasValue(displayProfile.domain_status) ? 1 : 0.6 }}>
              <div className="detail-label" style={{ fontSize: '11px', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                Domain Status
                {hasValue(displayProfile.domain_status) && (
                  <ProofBadge 
                    proofs={getProofsForField('domain_status', displayProfile.domain_status)} 
                    fieldName="Domain Status"
                  />
                )}
              </div>
              <div className="detail-value" style={{ fontSize: '14px', fontWeight: 500, color: hasValue(displayProfile.domain_status) ? '#ffffff' : '#64748b' }}>
                {displayProfile.domain_status || '—'}
                {displayProfile.domain_status === 'Active' && (
                  <span style={{ marginLeft: '8px', color: '#10b981', fontSize: '12px' }}>●</span>
                )}
              </div>
            </div>
            <div className="detail-pill" style={{ flexDirection: 'column', alignItems: 'flex-start', padding: '12px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a', opacity: hasValue(displayProfile.acronym) ? 1 : 0.6 }}>
              <div className="detail-label" style={{ fontSize: '11px', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                Acronym
                {hasValue(displayProfile.acronym) && (
                  <ProofBadge 
                    proofs={getProofsForField('acronym', displayProfile.acronym)} 
                    fieldName="Acronym"
                  />
                )}
              </div>
              <div className="detail-value" style={{ fontSize: '14px', fontWeight: 500, color: hasValue(displayProfile.acronym) ? '#ffffff' : '#64748b' }}>{displayProfile.acronym || '—'}</div>
            </div>
          </div>
        </section>

        <section className="card">
          <div className="card-title" style={{ fontSize: '16px', marginBottom: '16px' }}>Business Classification</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div className="detail-pill" style={{ flexDirection: 'column', alignItems: 'flex-start', padding: '12px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a', opacity: hasValue(displayProfile.industry) ? 1 : 0.6 }}>
              <div className="detail-label" style={{ fontSize: '11px', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                Industry
                {hasValue(displayProfile.industry) && (
                  <ProofBadge 
                    proofs={getProofsForField('industry', displayProfile.industry)} 
                    fieldName="Industry"
                  />
                )}
              </div>
              <div className="detail-value" style={{ fontSize: '14px', fontWeight: 500, color: hasValue(displayProfile.industry) ? '#ffffff' : '#64748b' }}>{displayProfile.industry || '—'}</div>
            </div>
            <div className="detail-pill" style={{ flexDirection: 'column', alignItems: 'flex-start', padding: '12px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a', opacity: hasValue(displayProfile.sub_industry) ? 1 : 0.6 }}>
              <div className="detail-label" style={{ fontSize: '11px', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                Sub-Industry
                {hasValue(displayProfile.sub_industry) && (
                  <ProofBadge 
                    proofs={getProofsForField('sub_industry', displayProfile.sub_industry)} 
                    fieldName="Sub-Industry"
                  />
                )}
              </div>
              <div className="detail-value" style={{ fontSize: '14px', fontWeight: 500, color: hasValue(displayProfile.sub_industry) ? '#ffffff' : '#64748b' }}>{displayProfile.sub_industry || '—'}</div>
            </div>
            <div className="detail-pill" style={{ flexDirection: 'column', alignItems: 'flex-start', padding: '12px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a', opacity: hasValue(displayProfile.business_type) ? 1 : 0.6 }}>
              <div className="detail-label" style={{ fontSize: '11px', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                Business Type
                {hasValue(displayProfile.business_type) && (
                  <ProofBadge 
                    proofs={getProofsForField('business_type', displayProfile.business_type)} 
                    fieldName="Business Type"
                  />
                )}
              </div>
              <div className="detail-value" style={{ fontSize: '14px', fontWeight: 500, color: hasValue(displayProfile.business_type) ? '#ffffff' : '#64748b' }}>{displayProfile.business_type || '—'}</div>
            </div>
            <div className="detail-pill" style={{ flexDirection: 'column', alignItems: 'flex-start', padding: '12px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a', opacity: hasValue(displayProfile.company_size) ? 1 : 0.6 }}>
              <div className="detail-label" style={{ fontSize: '11px', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                Company Size
                {hasValue(displayProfile.company_size) && (
                  <ProofBadge 
                    proofs={getProofsForField('company_size', displayProfile.company_size)} 
                    fieldName="Company Size"
                  />
                )}
              </div>
              <div className="detail-value" style={{ fontSize: '14px', fontWeight: 500, color: hasValue(displayProfile.company_size) ? '#ffffff' : '#64748b' }}>{displayProfile.company_size || '—'}</div>
            </div>
          </div>
        </section>

        <section className="card">
          <div className="card-title" style={{ fontSize: '16px', marginBottom: '16px' }}>Registration Details</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div className="detail-pill" style={{ flexDirection: 'column', alignItems: 'flex-start', padding: '12px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a', opacity: hasValue(displayProfile.company_registration) ? 1 : 0.6 }}>
              <div className="detail-label" style={{ fontSize: '11px', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                Company Registration
                {hasValue(displayProfile.company_registration) && (
                  <ProofBadge 
                    proofs={getProofsForField('company_registration', displayProfile.company_registration)} 
                    fieldName="Company Registration"
                  />
                )}
              </div>
              <div className="detail-value" style={{ fontSize: '14px', fontWeight: 500, color: hasValue(displayProfile.company_registration) ? '#ffffff' : '#64748b' }}>{displayProfile.company_registration || '—'}</div>
            </div>
            <div className="detail-pill" style={{ flexDirection: 'column', alignItems: 'flex-start', padding: '12px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a', opacity: hasValue(displayProfile.vat_number) ? 1 : 0.6 }}>
              <div className="detail-label" style={{ fontSize: '11px', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                VAT Number
                {hasValue(displayProfile.vat_number) && (
                  <ProofBadge 
                    proofs={getProofsForField('vat_number', displayProfile.vat_number)} 
                    fieldName="VAT Number"
                  />
                )}
              </div>
              <div className="detail-value" style={{ fontSize: '14px', fontWeight: 500, color: hasValue(displayProfile.vat_number) ? '#ffffff' : '#64748b' }}>{displayProfile.vat_number || '—'}</div>
            </div>
            <div className="detail-pill" style={{ flexDirection: 'column', alignItems: 'flex-start', padding: '12px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a', opacity: hasValue(displayProfile.ssc_code) ? 1 : 0.6 }}>
              <div className="detail-label" style={{ fontSize: '11px', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                SSC Code
                {hasValue(displayProfile.ssc_code) && (
                  <ProofBadge 
                    proofs={getProofsForField('ssc_code', displayProfile.ssc_code)} 
                    fieldName="SSC Code"
                  />
                )}
              </div>
              <div className="detail-value" style={{ fontSize: '14px', fontWeight: 500, color: hasValue(displayProfile.ssc_code) ? '#ffffff' : '#64748b' }}>{displayProfile.ssc_code || '—'}</div>
            </div>
          </div>
        </section>
      </div>

      {/* Sectors Section - Always show */}
      <section className="card" style={{ marginBottom: '20px' }}>
        <div className="card-title" style={{ fontSize: '16px', marginBottom: '16px' }}>Sectors</div>
        {hasValue(displayProfile.sectors) ? (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {displayProfile.sectors.map((sector, idx) => (
              <span key={idx} className="chip" style={{ fontSize: '13px', padding: '8px 14px' }}>
                {sector}
              </span>
            ))}
          </div>
        ) : (
          <div style={{ padding: '16px', textAlign: 'center', color: '#9ca3af' }}>No sectors information available</div>
        )}
      </section>

      {/* Location Section - Always show */}
      <section className="card" style={{ marginBottom: '20px' }}>
        <div className="card-title" style={{ fontSize: '16px', marginBottom: '16px' }}>Headquarters & Locations</div>
        {hasValue(displayProfile.headquarters) ? (
          <div style={{ marginBottom: '12px', padding: '16px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a' }}>
            <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
              Headquarters
              <ProofBadge 
                proofs={getProofsForField('headquarters', displayProfile.headquarters)} 
                fieldName="Headquarters"
              />
            </div>
            <div style={{ fontSize: '14px', color: '#ffffff', fontWeight: 500 }}>{displayProfile.headquarters}</div>
          </div>
        ) : (
          <div style={{ marginBottom: '12px', padding: '16px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a', opacity: 0.6 }}>
            <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '6px' }}>Headquarters</div>
            <div style={{ fontSize: '14px', color: '#64748b' }}>—</div>
          </div>
        )}
        {hasValue(displayProfile.locations) ? (
          <div style={{ padding: '16px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a' }}>
            <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '8px' }}>Other Locations</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {displayProfile.locations.map((loc, idx) => (
                <span key={idx} className="chip" style={{ fontSize: '12px', padding: '6px 12px' }}>
                  {loc}
                </span>
              ))}
            </div>
          </div>
        ) : (
          <div style={{ padding: '16px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a', opacity: 0.6 }}>
            <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '8px' }}>Other Locations</div>
            <div style={{ fontSize: '14px', color: '#64748b' }}>—</div>
          </div>
        )}
      </section>

      {/* Products Section - Always show */}
      <section className="card" style={{ marginBottom: '20px' }}>
        <div className="card-title" style={{ fontSize: '16px', marginBottom: '16px' }}>Products</div>
        {hasValue(displayProfile.products) ? (
          <>
            <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '12px' }}>
              {displayProfile.products.length} product{displayProfile.products.length !== 1 ? 's' : ''} found
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '12px' }}>
              {displayProfile.products.map((prod, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '12px',
                    background: '#1f1f1f',
                    borderRadius: '8px',
                    border: '1px solid #2a2a2a',
                  }}
                >
                  <div style={{ fontSize: '13px', fontWeight: 500, color: '#ffffff' }}>
                    {typeof prod === 'string' ? prod : (prod.name || 'Unnamed Product')}
                  </div>
                  {typeof prod === 'object' && prod.description && (
                    <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '4px' }}>
                      {prod.description}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </>
        ) : (
          <div style={{ padding: '16px', textAlign: 'center', color: '#9ca3af' }}>No products information available</div>
        )}
      </section>

      {/* Technology Stack - Always show */}
      <section className="card" style={{ marginBottom: '20px' }}>
        <div className="card-title" style={{ fontSize: '16px', marginBottom: '16px' }}>Technology Stack Signals</div>
        {hasValue(displayProfile.technology_signals) ? (
          <div className="chip-row">
            {displayProfile.technology_signals.map((sig, idx) => (
              <span key={idx} className="chip" style={{ fontSize: '13px', padding: '8px 14px' }}>
                {sig}
              </span>
            ))}
          </div>
        ) : (
          <div style={{ padding: '16px', textAlign: 'center', color: '#9ca3af' }}>No technology stack information available</div>
        )}
      </section>

      {/* Extraction Confidence - Always show */}
      <section className="card">
        <div className="card-title" style={{ fontSize: '16px', marginBottom: '16px' }}>Data Quality</div>
        <div style={{ padding: '16px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a' }}>
          <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '8px' }}>Extraction Confidence</div>
          {displayProfile.extraction_confidence !== undefined && displayProfile.extraction_confidence !== null ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ flex: 1, height: '8px', background: '#2a2a2a', borderRadius: '4px', overflow: 'hidden' }}>
                <div 
                  style={{ 
                    height: '100%', 
                    background: displayProfile.extraction_confidence > 0.7 ? '#10b981' : displayProfile.extraction_confidence > 0.4 ? '#f59e0b' : '#ef4444',
                    width: `${Math.max(0, Math.min(100, (displayProfile.extraction_confidence * 100)))}%`,
                    transition: 'width 0.3s',
                  }}
                />
              </div>
              <div style={{ fontSize: '13px', fontWeight: 500, color: '#ffffff', minWidth: '60px', textAlign: 'right' }}>
                {(displayProfile.extraction_confidence * 100).toFixed(0)}%
              </div>
            </div>
          ) : (
            <div style={{ fontSize: '14px', color: '#64748b' }}>—</div>
          )}
        </div>
      </section>
    </div>
  )
}

export default CompanyInfoPage
