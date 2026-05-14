import React from 'react'
import './Page.css'

function KnowledgeGraphPage({ profile, loading }) {
  if (loading) {
    return (
      <div className="page active">
        <section className="card">
          <div className="card-title">Knowledge Graph</div>
          <div className="skeleton" style={{ height: '400px', width: '100%' }}></div>
        </section>
      </div>
    )
  }

  // Extract entities and relationships from profile
  const entities = []
  const relationships = []

  if (profile) {
    // Company entity
    if (profile.company_name) {
      entities.push({ type: 'Company', name: profile.company_name, id: 'company' })
    }

    // Industry/Sector entities
    if (profile.industry) {
      entities.push({ type: 'Industry', name: profile.industry, id: 'industry' })
      if (profile.company_name) {
        relationships.push({ from: 'company', to: 'industry', type: 'operates_in' })
      }
    }

    // Location entities
    if (profile.headquarters) {
      entities.push({ type: 'Location', name: profile.headquarters, id: 'hq' })
      if (profile.company_name) {
        relationships.push({ from: 'company', to: 'hq', type: 'located_at' })
      }
    }

    // Technology entities
    if (profile.technology_signals && profile.technology_signals.length > 0) {
      profile.technology_signals.forEach((tech, idx) => {
        entities.push({ type: 'Technology', name: tech, id: `tech_${idx}` })
        if (profile.company_name) {
          relationships.push({ from: 'company', to: `tech_${idx}`, type: 'uses' })
        }
      })
    }

    // Service entities
    if (profile.services && profile.services.length > 0) {
      profile.services.forEach((svc, idx) => {
        if (svc.name) {
          entities.push({ type: 'Service', name: svc.name, id: `service_${idx}` })
          if (profile.company_name) {
            relationships.push({ from: 'company', to: `service_${idx}`, type: 'offers' })
          }
        }
      })
    }
  }

  return (
    <div className="page active">
      <section className="card" style={{ marginBottom: '20px' }}>
        <div className="card-title" style={{ fontSize: '18px', marginBottom: '16px' }}>Knowledge Graph</div>
        <div style={{ marginBottom: '20px', fontSize: '12px', color: '#9ca3af', lineHeight: '1.6' }}>
          Visual representation of company relationships, entities, and connections extracted from the data.
        </div>

        {/* Graph Visualization Placeholder */}
        <div
          style={{
            minHeight: '400px',
            padding: '20px',
            background: '#1f1f1f',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#9ca3af',
            border: '1px solid #2a2a2a',
            marginBottom: '20px',
          }}
        >
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔗</div>
            <div style={{ fontSize: '14px', marginBottom: '8px' }}>Knowledge Graph Visualization</div>
            <div style={{ fontSize: '12px', color: '#64748b' }}>Coming soon...</div>
          </div>
        </div>

        {/* Entity List */}
        {entities.length > 0 && (
          <div style={{ marginBottom: '20px' }}>
            <div style={{ fontSize: '14px', fontWeight: 600, color: '#ffffff', marginBottom: '12px' }}>
              Entities ({entities.length})
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' }}>
              {entities.map((entity, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '12px',
                    background: '#1f1f1f',
                    borderRadius: '8px',
                    border: '1px solid #2a2a2a',
                  }}
                >
                  <div style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '4px' }}>{entity.type}</div>
                  <div style={{ fontSize: '13px', fontWeight: 500, color: '#ffffff' }}>{entity.name}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Relationships List */}
        {relationships.length > 0 && (
          <div>
            <div style={{ fontSize: '14px', fontWeight: 600, color: '#ffffff', marginBottom: '12px' }}>
              Relationships ({relationships.length})
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {relationships.map((rel, idx) => {
                const fromEntity = entities.find(e => e.id === rel.from)
                const toEntity = entities.find(e => e.id === rel.to)
                if (!fromEntity || !toEntity) return null
                return (
                  <div
                    key={idx}
                    style={{
                      padding: '12px',
                      background: '#1f1f1f',
                      borderRadius: '8px',
                      border: '1px solid #2a2a2a',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                    }}
                  >
                    <div style={{ fontSize: '13px', fontWeight: 500, color: '#ffffff' }}>{fromEntity.name}</div>
                    <div style={{ fontSize: '11px', color: '#ff5c4d', padding: '4px 8px', background: '#2a2a2a', borderRadius: '4px' }}>
                      {rel.type.replace('_', ' ')}
                    </div>
                    <div style={{ fontSize: '13px', fontWeight: 500, color: '#ffffff' }}>{toEntity.name}</div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {entities.length === 0 && relationships.length === 0 && (
          <div style={{ padding: '40px', textAlign: 'center', color: '#9ca3af' }}>
            No entities or relationships found in the profile data.
          </div>
        )}
      </section>
    </div>
  )
}

export default KnowledgeGraphPage
