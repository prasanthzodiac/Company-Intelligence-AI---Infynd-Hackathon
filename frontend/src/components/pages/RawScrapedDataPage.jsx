import React, { useState, useEffect } from 'react'
import { getCompanyChunks } from '../../services/api'
import './Page.css'

function RawScrapedDataPage({ selectedDomain, loading: initialLoading }) {
  const [chunks, setChunks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [expandedChunk, setExpandedChunk] = useState(null)
  const [filter, setFilter] = useState('all') // all, contact, services, about, etc.

  useEffect(() => {
    if (selectedDomain) {
      loadChunks()
    }
  }, [selectedDomain])

  const loadChunks = async () => {
    if (!selectedDomain) return
    
    try {
      setLoading(true)
      setError(null)
      const data = await getCompanyChunks(selectedDomain)
      const list = Array.isArray(data) ? data : data?.chunks || []
      setChunks(list)
      if (list.length === 0) {
        setError(
          data?.message ||
            'No scraped content yet. Finish CSV processing on the upload screen, then click Retry.'
        )
      } else {
        setError(null)
      }
    } catch (err) {
      console.error('Error loading chunks:', err)
      setError(err.message || 'Failed to load raw scraped data')
      setChunks([])
    } finally {
      setLoading(false)
    }
  }

  const filteredChunks = chunks.filter(chunk => {
    if (filter === 'all') return true
    const section = (chunk.section || '').toLowerCase()
    return section.includes(filter.toLowerCase())
  })

  const getSectionStats = () => {
    const stats = {}
    chunks.forEach(chunk => {
      const section = chunk.section || 'Unknown'
      stats[section] = (stats[section] || 0) + 1
    })
    return stats
  }

  const toggleChunk = (index) => {
    setExpandedChunk(expandedChunk === index ? null : index)
  }

  const exportChunks = () => {
    const dataStr = JSON.stringify(chunks, null, 2)
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr)
    const linkElement = document.createElement('a')
    linkElement.setAttribute('href', dataUri)
    linkElement.setAttribute('download', `${selectedDomain || 'company'}_raw_chunks.json`)
    linkElement.click()
  }

  if (initialLoading || loading) {
    return (
      <div className="page active">
        <section className="card">
          <div className="card-title">Raw Scraped Data</div>
          <div className="skeleton" style={{ height: '200px', width: '100%' }}></div>
        </section>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page active">
        <section className="card">
          <div className="card-title">Raw Scraped Data</div>
          <div style={{ padding: '20px', color: '#ef4444' }}>
            {error}
            <div style={{ marginTop: '12px' }}>
              <button type="button" onClick={loadChunks} style={{ padding: '8px 14px', cursor: 'pointer' }}>
                Retry
              </button>
            </div>
          </div>
        </section>
      </div>
    )
  }

  const stats = getSectionStats()
  const sectionOptions = ['all', 'contact', 'services', 'about', 'team', 'products', 'location']

  return (
    <div className="page active">
      <section className="card">
        <div className="card-title">Raw Scraped Data</div>
        <div style={{ marginBottom: '20px', fontSize: '12px', color: '#9ca3af' }}>
          View the raw scraped data chunks extracted from the website. Each chunk represents a section of content.
        </div>

        {chunks.length > 0 && (
          <>
            <div style={{ marginBottom: '20px', display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
              <div style={{ fontSize: '13px', color: '#9ca3af' }}>
                Total Chunks: <strong style={{ color: '#ffffff' }}>{chunks.length}</strong>
              </div>
              <div style={{ fontSize: '13px', color: '#9ca3af' }}>
                Filtered: <strong style={{ color: '#ffffff' }}>{filteredChunks.length}</strong>
              </div>
              <div style={{ marginLeft: 'auto' }}>
                <button
                  onClick={exportChunks}
                  style={{
                    padding: '6px 12px',
                    background: '#ff5c4d',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontSize: '12px',
                    transition: 'background 0.2s',
                  }}
                  onMouseEnter={(e) => e.target.style.background = '#ff3d2a'}
                  onMouseLeave={(e) => e.target.style.background = '#ff5c4d'}
                >
                  Export JSON
                </button>
              </div>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <label style={{ fontSize: '12px', color: '#9ca3af', marginRight: '8px' }}>Filter by section:</label>
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                style={{
                  padding: '6px 12px',
                  background: '#1f1f1f',
                  color: '#ffffff',
                  border: '1px solid #2a2a2a',
                  borderRadius: '6px',
                  fontSize: '12px',
                  cursor: 'pointer',
                }}
              >
                <option value="all">All Sections</option>
                {sectionOptions.filter(opt => opt !== 'all').map(opt => (
                  <option key={opt} value={opt}>{opt.charAt(0).toUpperCase() + opt.slice(1)}</option>
                ))}
              </select>
            </div>

            {Object.keys(stats).length > 0 && (
              <div style={{ marginBottom: '20px', padding: '12px', background: '#1f1f1f', borderRadius: '8px', border: '1px solid #2a2a2a' }}>
                <div style={{ fontSize: '12px', fontWeight: 600, marginBottom: '8px', color: '#ffffff' }}>Section Statistics</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {Object.entries(stats).map(([section, count]) => (
                    <span
                      key={section}
                      className="chip"
                      style={{
                        fontSize: '11px',
                        padding: '4px 8px',
                        background: '#2a2a2a',
                        color: '#9ca3af',
                        borderRadius: '4px',
                      }}
                    >
                      {section}: {count}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {filteredChunks.map((chunk, index) => (
                <div
                  key={index}
                  style={{
                    padding: '16px',
                    background: '#1f1f1f',
                    borderRadius: '8px',
                    border: '1px solid #2a2a2a',
                    cursor: 'pointer',
                    transition: 'border-color 0.2s',
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.borderColor = '#ff5c4d'}
                  onMouseLeave={(e) => e.currentTarget.style.borderColor = '#2a2a2a'}
                  onClick={() => toggleChunk(index)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '8px' }}>
                    <div>
                      <div style={{ fontSize: '13px', fontWeight: 600, color: '#ffffff', marginBottom: '4px' }}>
                        {chunk.section || 'Unknown Section'}
                      </div>
                      <div style={{ fontSize: '11px', color: '#64748b' }}>
                        Page: {chunk.page || 'N/A'} | Domain: {chunk.domain || selectedDomain || 'N/A'}
                      </div>
                    </div>
                    <div style={{ fontSize: '11px', color: '#9ca3af' }}>
                      {expandedChunk === index ? '▼' : '▶'}
                    </div>
                  </div>
                  
                  {expandedChunk === index && (
                    <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid #2a2a2a' }}>
                      <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '8px', fontWeight: 600 }}>
                        Text Content:
                      </div>
                      <div
                        style={{
                          fontSize: '12px',
                          color: '#d1d5db',
                          lineHeight: '1.6',
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-word',
                          maxHeight: '400px',
                          overflowY: 'auto',
                          padding: '12px',
                          background: '#0f0f0f',
                          borderRadius: '4px',
                          fontFamily: 'monospace',
                        }}
                      >
                        {chunk.text || 'No text content'}
                      </div>
                      
                      {chunk.structured_data && Object.keys(chunk.structured_data).length > 0 && (
                        <div style={{ marginTop: '12px' }}>
                          <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '8px', fontWeight: 600 }}>
                            Structured Data:
                          </div>
                          <pre
                            style={{
                              fontSize: '11px',
                              color: '#d1d5db',
                              padding: '12px',
                              background: '#0f0f0f',
                              borderRadius: '4px',
                              overflowX: 'auto',
                              maxHeight: '300px',
                              overflowY: 'auto',
                            }}
                          >
                            {JSON.stringify(chunk.structured_data, null, 2)}
                          </pre>
                        </div>
                      )}
                      
                      {chunk.page_title && (
                        <div style={{ marginTop: '8px', fontSize: '11px', color: '#64748b' }}>
                          Page Title: {chunk.page_title}
                        </div>
                      )}
                      
                      {chunk.meta_description && (
                        <div style={{ marginTop: '4px', fontSize: '11px', color: '#64748b' }}>
                          Meta Description: {chunk.meta_description}
                        </div>
                      )}
                    </div>
                  )}
                  
                  {expandedChunk !== index && (
                    <div
                      style={{
                        fontSize: '12px',
                        color: '#9ca3af',
                        marginTop: '8px',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                      }}
                    >
                      {chunk.text || 'No preview available'}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {filteredChunks.length === 0 && (
              <div style={{ padding: '40px', textAlign: 'center', color: '#9ca3af' }}>
                No chunks found for the selected filter.
              </div>
            )}
          </>
        )}

        {chunks.length === 0 && !loading && (
          <div style={{ padding: '40px', textAlign: 'center', color: '#9ca3af' }}>
            No raw scraped data available for this company.
          </div>
        )}
      </section>
    </div>
  )
}

export default RawScrapedDataPage

