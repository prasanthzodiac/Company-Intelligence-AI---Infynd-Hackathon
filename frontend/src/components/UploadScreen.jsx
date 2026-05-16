import React, { useState, useRef } from 'react'
import { API_BASE, apiFetch, ensureSession, isProductionSameOriginApi } from '../services/api.js'
import { setProcessingActive } from '../services/session.js'
import './UploadScreen.css'

// SVG Icon Components
const FileIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M14 2V8H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M16 13H8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M16 17H8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M10 9H9H8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
)

const DownloadIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M21 15V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M7 10L12 15L17 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M12 15V3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
)

const SearchIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="11" cy="11" r="8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M21 21L16.65 16.65" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
)

const BotIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="3" y="11" width="18" height="10" rx="2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M7 15H7.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M17 15H17.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M12 7V3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M8 7H16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
)

const CheckIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M20 6L9 17L4 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
)

const XIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
)

const WarningIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 9V13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M12 17H12.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M10.29 3.86L1.82 18C1.64543 18.3024 1.55291 18.6453 1.552 19C1.55108 19.3547 1.64181 19.6981 1.81482 20.0015C1.98784 20.3049 2.23726 20.5581 2.53773 20.7359C2.8382 20.9137 3.17958 21.0099 3.53 21.015H20.47C20.8204 21.0099 21.1618 20.9137 21.4623 20.7359C21.7627 20.5581 22.0122 20.3049 22.1852 20.0015C22.3582 19.6981 22.4489 19.3547 22.448 19C22.4471 18.6453 22.3546 18.3024 22.18 18L13.71 3.86C13.5318 3.56631 13.2807 3.32311 12.9812 3.15447C12.6817 2.98584 12.3438 2.89725 12 2.89725C11.6562 2.89725 11.3183 2.98584 11.0188 3.15447C10.7193 3.32311 10.4682 3.56631 10.29 3.86Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
)

const CloudUploadIcon = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M6.667 8.333C5.562 8.333 4.5 8.772 3.757 9.515C3.014 10.258 2.575 11.32 2.575 12.425C2.575 13.53 3.014 14.592 3.757 15.335C4.5 16.078 5.562 16.517 6.667 16.517H15C15.8841 16.517 16.7319 16.1658 17.357 15.5407C17.9821 14.9156 18.3333 14.0678 18.3333 13.1837C18.3333 12.2995 17.9821 11.4517 17.357 10.8266C16.7319 10.2015 15.8841 9.85026 15 9.85026C14.89 8.30826 14.2701 6.84159 13.2441 5.71559C12.2181 4.58959 10.8566 3.88126 9.375 3.72526C7.8934 3.56926 6.39159 3.97659 5.16659 4.86659C3.94159 5.75659 3.07526 7.07126 2.75833 8.53326" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M10 12.5V7.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M7.5 10L10 7.5L12.5 10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
)

const ArrowRightIcon = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M7.5 15L12.5 10L7.5 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
)

function UploadScreen({ onProcessingComplete, onStartOver }) {
  const [csvFile, setCsvFile] = useState(null)
  const [csvFileName, setCsvFileName] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [status, setStatus] = useState({
    stage: 'idle',
    message: '',
    progress: 0,
    currentCompany: '',
    totalCompanies: 0,
    processedCompanies: 0
  })
  const fileInputRef = useRef(null)

  const handleFileSelect = (e) => {
    const file = e.target.files[0]
    if (file && (file.type === 'text/csv' || file.name.endsWith('.csv'))) {
      setCsvFile(file)
      setCsvFileName(file.name)
    } else {
      alert('Please select a CSV file')
    }
  }

  const handleUpload = async () => {
    if (!csvFile) {
      alert('Please select a CSV file first')
      return
    }

    if (isProductionSameOriginApi()) {
      alert(
        'This Vercel site only serves the UI. Deploy the Flask API elsewhere, then in Vercel → Project → Settings → Environment Variables set VITE_API_BASE_URL to your API root (for example https://your-app.onrender.com/api), save, and trigger a new deployment.'
      )
      return
    }

    try {
      await ensureSession()
    } catch (e) {
      alert('Could not start session: ' + e.message)
      return
    }

    setIsProcessing(true)
    setProcessingActive(true)
    setStatus({
      stage: 'uploading',
      message: 'Uploading CSV file...',
      progress: 0
    })

    const formData = new FormData()
    formData.append('csv_file', csvFile)
    try {
      const { response: uploadResponse, url: uploadUrl } = await apiFetch('/upload-csv', {
        method: 'POST',
        body: formData,
      })

      if (!uploadResponse.ok) {
        // Try to get error message from response
        let errorMessage = 'Failed to upload CSV'
        try {
          const errorData = await uploadResponse.json()
          errorMessage = errorData.error || errorMessage
        } catch (e) {
          errorMessage = `Failed to upload CSV: ${uploadResponse.status} ${uploadResponse.statusText}`
        }
        if (uploadResponse.status === 404) {
          errorMessage += `\n\nRequested: ${uploadUrl}\nCheck Render is live and VITE_API_BASE_URL is your API root (e.g. https://YOUR-SERVICE.onrender.com/api), then redeploy Vercel.`
        }
        throw new Error(errorMessage)
      }

      const uploadData = await uploadResponse.json()
      const jobId = uploadData.job_id

      setStatus({
        stage: 'downloading',
        message: 'Starting processing pipeline...',
        progress: 5
      })

      let pollErrors = 0
      const pollInterval = setInterval(async () => {
        try {
          const { response: statusResponse } = await apiFetch(`/processing-status/${jobId}`)
          const statusData = await statusResponse.json()
          pollErrors = 0

          if (
            statusData.stage === 'error' &&
            (statusData.message || '').toLowerCase().includes('job not found')
          ) {
            pollErrors += 1
            if (pollErrors < 8) {
              return
            }
          }

          setStatus({
            stage: statusData.stage || 'processing',
            message: statusData.message || 'Processing...',
            progress: statusData.progress || 0,
            currentCompany: statusData.current_company || '',
            totalCompanies: statusData.total_companies || 0,
            processedCompanies: statusData.processed_companies || 0
          })

          if (statusData.stage === 'complete' || statusData.stage === 'error') {
            clearInterval(pollInterval)
            setIsProcessing(false)
            setProcessingActive(false)
            if (statusData.stage === 'error') {
              alert(`Processing failed: ${statusData.message || 'Unknown error'}`)
              return
            }
            if (statusData.stage === 'complete' && onProcessingComplete) {
              // If all companies were already complete, redirect immediately
              const delay = statusData.all_complete ? 500 : 1000
              setTimeout(() => {
                onProcessingComplete()
              }, delay)
            }
          }
        } catch (error) {
          console.error('Error polling status:', error)
          pollErrors += 1
          if (pollErrors < 5) {
            return
          }
          clearInterval(pollInterval)
          setIsProcessing(false)
          setProcessingActive(false)
          alert(`Lost connection to API while processing: ${error.message}`)
          setStatus({
            stage: 'error',
            message: error.message,
            progress: 0,
          })
        }
      }, 2000)

    } catch (error) {
      console.error('Error processing CSV:', error)
      alert('Error processing CSV: ' + error.message)
      setIsProcessing(false)
      setProcessingActive(false)
      setStatus({
        stage: 'error',
        message: 'Error: ' + error.message,
        progress: 0
      })
    }
  }

  const getStatusIcon = () => {
    switch (status.stage) {
      case 'downloading':
        return <DownloadIcon />
      case 'scraping':
        return <SearchIcon />
      case 'llm':
        return <BotIcon />
      case 'complete':
        return <CheckIcon />
      case 'error':
        return <XIcon />
      default:
        return <div className="status-dot"></div>
    }
  }

  const hasActivity = status.stage !== 'idle'

  return (
    <div className="upload-screen">
      <div className="upload-header">
        <div className="sidebar-logo">
          <span className="logo-text-red">In</span>
          <span className="logo-text-white">Fynd</span>
          <span className="logo-subtitle">COMPANY INTELLIGENCE AI</span>
        </div>

        <div className="upload-header-meta">
          <div className="meta-pill meta-pill--status">
            <span className="meta-dot" />
            <span>{hasActivity ? 'Pipeline running' : 'Ready for ingestion'}</span>
          </div>
          <div className="meta-divider" />
          <div className="meta-env">
            <span className="meta-label">Mode</span>
            <span className="meta-value">Offline Analyst · Local / Air‑gapped</span>
          </div>
        </div>
      </div>

      <div className="upload-content">
        <div className="upload-layout">
          <div className="upload-main">
            <div className="upload-heading">
              <h1>Upload domains into your company intelligence workspace</h1>
              <p>
                Start by uploading a CSV of company domains. InFynd will crawl each site, extract
                structured profiles, and make them available across your Company Intelligence AI
                workspace.
              </p>
            </div>

              <div className="upload-card">
                <div className={`card-status-tag ${hasActivity ? 'processing' : 'ready'}`}>
                  {hasActivity ? 'Processing' : 'Ready to ingest'}
                </div>

                <div className="card-header-row">
                  <div className="card-icon green">
                    <FileIcon />
                  </div>
                  <div className="card-header-copy">
                    <div className="card-title">Upload domains CSV</div>
                    <div className="card-description">
                      This CSV becomes the source of truth for your workspace. Upload a clean
                      list of domains and we&apos;ll handle crawling, enrichment and profile
                      generation for each company.
                    </div>
                  </div>
                </div>

                <div className="card-input-field">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv"
                    onChange={handleFileSelect}
                    style={{ display: 'none' }}
                  />

                  <div
                    className="input-display"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <div className="input-main">
                      <span className="input-icon">
                        <CloudUploadIcon />
                      </span>
                      <div className="input-copy">
                        <div className="input-title">
                          {csvFileName || 'Drag & drop or browse for your domains CSV'}
                        </div>
                        <div className="input-subtitle">
                          Single header column named <code>domain</code> with values like
                          <code> example.com</code>, <code> contoso.co.uk</code>.
                        </div>
                      </div>
                    </div>
                    <div className="input-meta">
                      <span className="input-hint">
                        Max 100MB · .csv only
                        {csvFileName && csvFile && ` · ${(csvFile.size / 1024).toFixed(1)} KB`}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="upload-footer-row">
                  <div className="upload-notes">
                    <span className="upload-note-label">Ingestion behaviour</span>
                    <span className="upload-note-text">
                      Re‑uploading an updated CSV will refresh existing companies and add any
                      new domains to your workspace. No historical data is lost.
                    </span>
                  </div>

                  <button
                    className="process-button"
                    onClick={handleUpload}
                    disabled={!csvFile || isProcessing}
                  >
                    <span className="button-icon">
                      <ArrowRightIcon />
                    </span>
                    <span>{isProcessing ? 'Processing in progress…' : 'Ingest & process data'}</span>
                  </button>
                </div>
              </div>

            {hasActivity && (
              <div className="processing-status professional">
                <div className="status-icon-wrapper">{getStatusIcon()}</div>
                <div className="status-content">
                  <div className="status-header-row">
                    <div className="status-message">{status.message}</div>
                    <div className="status-stage-pill">
                      {status.stage === 'downloading' && 'Stage 1 · Snapshot & download'}
                      {status.stage === 'scraping' && 'Stage 2 · Crawl & normalize content'}
                      {status.stage === 'llm' && 'Stage 3 · LLM profile extraction'}
                      {status.stage === 'complete' && 'Pipeline complete'}
                      {status.stage === 'error' && 'Attention required'}
                    </div>
                  </div>

                  <div className="status-meta-row">
                    {status.currentCompany && (
                      <div className="status-company">
                        Current company: <strong>{status.currentCompany}</strong>
                      </div>
                    )}
                    {status.totalCompanies > 0 && (
                      <div className="status-progress">
                        {status.processedCompanies} of {status.totalCompanies} companies processed
                      </div>
                    )}
                  </div>

                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{ width: `${status.progress || 0}%` }}
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          <aside className="upload-aside">
            <div className="aside-card">
              <div className="aside-title-row">
                <BotIcon />
                <div>
                  <div className="aside-title">Secure, local‑only processing</div>
                  <div className="aside-subtitle">Designed for sensitive corporate data</div>
                </div>
              </div>
              <ul className="aside-list">
                <li>
                  <span className="aside-bullet" />
                  No outbound calls to OpenAI, Anthropic or third‑party APIs.
                </li>
                <li>
                  <span className="aside-bullet" />
                  All enrichment runs against your local Ollama LLaMA‑3 deployment.
                </li>
                <li>
                  <span className="aside-bullet" />
                  Profiles, chunks and logs remain on your infrastructure.
                </li>
              </ul>
            </div>

            <div className="aside-card secondary">
              <div className="aside-section-label">CSV requirements</div>
              <ul className="aside-list compact">
                <li>
                  Single header column named <code>domain</code>
                </li>
                <li>No protocol (no https://) and no paths</li>
                <li>Valid domains only, one per row</li>
              </ul>
            </div>
          </aside>
        </div>
      </div>
    </div>
  )
}

export default UploadScreen
