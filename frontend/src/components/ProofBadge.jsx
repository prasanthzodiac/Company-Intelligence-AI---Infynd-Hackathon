import React, { useState } from 'react'

function ProofBadge({ proofs, fieldName }) {
  const [showProofs, setShowProofs] = useState(false)

  if (!proofs || proofs.length === 0) {
    return null
  }

  return (
    <div style={{ position: 'relative', display: 'inline-block', marginLeft: '8px' }}>
      <button
        onClick={() => setShowProofs(!showProofs)}
        style={{
          background: 'transparent',
          border: '1px solid #2a2a2a',
          borderRadius: '4px',
          padding: '2px 6px',
          fontSize: '10px',
          color: '#9ca3af',
          cursor: 'pointer',
          transition: 'all 0.2s',
        }}
        onMouseEnter={(e) => {
          e.target.style.borderColor = '#ff5c4d'
          e.target.style.color = '#ff5c4d'
        }}
        onMouseLeave={(e) => {
          e.target.style.borderColor = '#2a2a2a'
          e.target.style.color = '#9ca3af'
        }}
        title={`${proofs.length} source${proofs.length !== 1 ? 's' : ''} available`}
      >
        📎 {proofs.length}
      </button>
      
      {showProofs && (
        <div
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            marginTop: '4px',
            background: '#1f1f1f',
            border: '1px solid #2a2a2a',
            borderRadius: '8px',
            padding: '12px',
            minWidth: '300px',
            maxWidth: '500px',
            maxHeight: '400px',
            overflowY: 'auto',
            zIndex: 1000,
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <div style={{ fontSize: '11px', fontWeight: 600, color: '#ffffff', marginBottom: '8px' }}>
            Sources for {fieldName}
          </div>
          {proofs.map((proof, idx) => (
            <div
              key={idx}
              style={{
                padding: '8px',
                background: '#0f0f0f',
                borderRadius: '4px',
                marginBottom: '8px',
                fontSize: '11px',
              }}
            >
              <div style={{ color: '#9ca3af', marginBottom: '4px' }}>
                Page: {proof.page || 'N/A'} | Section: {proof.section || 'N/A'}
              </div>
              <div style={{ color: '#d1d5db', lineHeight: '1.5' }}>
                {proof.text ? (proof.text.length > 150 ? proof.text.substring(0, 150) + '...' : proof.text) : 'No preview'}
              </div>
              {proof.source_path && (
                <div style={{ color: '#64748b', marginTop: '4px', fontSize: '10px' }}>
                  {proof.source_path.split('/').pop()}
                </div>
              )}
            </div>
          ))}
          <button
            onClick={() => setShowProofs(false)}
            style={{
              marginTop: '8px',
              padding: '4px 8px',
              background: '#2a2a2a',
              border: 'none',
              borderRadius: '4px',
              color: '#9ca3af',
              cursor: 'pointer',
              fontSize: '10px',
            }}
          >
            Close
          </button>
        </div>
      )}
    </div>
  )
}

export default ProofBadge

