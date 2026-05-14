import React from 'react'
import './Page.css'

function ServicesPage({ profile, loading }) {
  if (loading) {
    return (
      <div className="page active">
        <section className="card">
          <div className="card-title">Products & Services</div>
          <div className="skeleton" style={{ height: '200px', width: '100%' }}></div>
        </section>
      </div>
    )
  }

  // Create default profile structure if profile is null
  const defaultProfile = {
    services: [],
    products: []
  }
  
  const displayProfile = profile || defaultProfile
  const services = displayProfile.services || []
  const products = displayProfile.products || []

  return (
    <div className="page active">
      {/* Services Section - Always show */}
      <section className="card" style={{ marginBottom: '20px' }}>
        <div className="card-title" style={{ fontSize: '18px', marginBottom: '16px' }}>Services</div>
        {services.length > 0 ? (
          <>
            <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '20px' }}>
              {services.length} service{services.length !== 1 ? 's' : ''} found
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
              {services.map((svc, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '16px',
                    background: '#1f1f1f',
                    borderRadius: '8px',
                    border: '1px solid #2a2a2a',
                    transition: 'border-color 0.2s',
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.borderColor = '#ff5c4d'}
                  onMouseLeave={(e) => e.currentTarget.style.borderColor = '#2a2a2a'}
                >
                  <div style={{ fontSize: '14px', fontWeight: 600, color: '#ffffff', marginBottom: '8px' }}>
                    {svc.name || 'Unnamed Service'}
                  </div>
                  {svc.type && (
                    <div style={{ display: 'inline-block' }}>
                      <span className="chip" style={{ fontSize: '11px', padding: '4px 8px', background: '#2a2a2a', color: '#9ca3af' }}>
                        {svc.type}
                      </span>
                    </div>
                  )}
                  {svc.description && (
                    <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '8px', lineHeight: '1.6' }}>
                      {svc.description}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </>
        ) : (
          <div style={{ padding: '40px', textAlign: 'center', color: '#9ca3af' }}>
            No services information available.
          </div>
        )}
      </section>

      {/* Products Section - Always show */}
      <section className="card">
        <div className="card-title" style={{ fontSize: '18px', marginBottom: '16px' }}>Products</div>
        {products.length > 0 ? (
          <>
            <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '20px' }}>
              {products.length} product{products.length !== 1 ? 's' : ''} found
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
              {products.map((prod, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '16px',
                    background: '#1f1f1f',
                    borderRadius: '8px',
                    border: '1px solid #2a2a2a',
                    transition: 'border-color 0.2s',
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.borderColor = '#ff5c4d'}
                  onMouseLeave={(e) => e.currentTarget.style.borderColor = '#2a2a2a'}
                >
                  <div style={{ fontSize: '14px', fontWeight: 600, color: '#ffffff', marginBottom: '8px' }}>
                    {typeof prod === 'string' ? prod : (prod.name || 'Unnamed Product')}
                  </div>
                  {typeof prod === 'object' && prod.description && (
                    <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '8px', lineHeight: '1.6' }}>
                      {prod.description}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </>
        ) : (
          <div style={{ padding: '40px', textAlign: 'center', color: '#9ca3af' }}>
            No products information available.
          </div>
        )}
      </section>
    </div>
  )
}

export default ServicesPage
