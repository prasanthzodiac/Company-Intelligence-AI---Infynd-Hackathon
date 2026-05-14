import React, { useState, useRef, useEffect } from 'react'
import { sendChatMessage } from '../services/api'
import './ChatPanel.css'

// SVG Icons
const BotIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="3" y="11" width="18" height="10" rx="2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M7 15H7.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M17 15H17.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M12 7V3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M8 7H16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
)

const UserIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M20 21V19C20 17.9391 19.5786 16.9217 18.8284 16.1716C18.0783 15.4214 17.0609 15 16 15H8C6.93913 15 5.92172 15.4214 5.17157 16.1716C4.42143 16.9217 4 17.9391 4 19V21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <circle cx="12" cy="7" r="4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
)

const SendIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M22 2L11 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
)

const SparkleIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 2L13.09 8.26L19 9L13.09 9.74L12 16L10.91 9.74L5 9L10.91 8.26L12 2Z" fill="currentColor"/>
    <path d="M19 15L19.5 17.5L22 18L19.5 18.5L19 21L18.5 18.5L16 18L18.5 17.5L19 15Z" fill="currentColor"/>
  </svg>
)

function ChatPanel({ selectedDomain, profile }) {
  const [messages, setMessages] = useState([
    {
      type: 'bot',
      text: 'Hello! I am your offline autonomous intelligence analyst. I operate entirely on local data extracted from company websites. Select a company on the left and ask me about its products, technology, or positioning.',
    },
  ])
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [proofs, setProofs] = useState([])
  const chatBodyRef = useRef(null)

  useEffect(() => {
    if (selectedDomain && profile) {
      setMessages([
        {
          type: 'bot',
          text: `Loaded local intelligence for ${selectedDomain}. Ask a question in the box below.`,
        },
      ])
      setProofs([])
    }
  }, [selectedDomain, profile])

  useEffect(() => {
    if (chatBodyRef.current) {
      chatBodyRef.current.scrollTop = chatBodyRef.current.scrollHeight
    }
  }, [messages])

  const handleSend = async () => {
    const question = inputValue.trim()
    if (!question || !selectedDomain || loading) return

    setInputValue('')
    setLoading(true)
    setMessages((prev) => [...prev, { type: 'user', text: question }])

    try {
      const response = await sendChatMessage(selectedDomain, question)
      setMessages((prev) => [...prev, { type: 'bot', text: response.response }])
      if (response.proofs && response.proofs.length > 0) {
        setProofs(response.proofs)
      } else {
        setProofs([])
      }
    } catch (error) {
      console.error('Error sending message:', error)
      setMessages((prev) => [
        ...prev,
        { type: 'bot', text: 'Sorry, I encountered an error. Please try again.' },
      ])
      setProofs([])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <aside className="right-column">
      <section className="card chat-card">
        <div className="chat-header">
          <div className="chat-header-content">
            <div className="chat-header-icon">
              <BotIcon />
            </div>
            <div className="chat-header-text">
              <div className="chat-header-title">AI Intelligence Analyst</div>
              <div className="chat-subtitle">
                {selectedDomain ? `Analyzing: ${selectedDomain}` : 'Select a company to begin'}
              </div>
            </div>
          </div>
          <span className="chat-badge">
            <SparkleIcon />
            <span>Local</span>
          </span>
        </div>
        
        <div className="chat-body" ref={chatBodyRef}>
          {messages.map((msg, idx) => (
            <div key={idx} className={`chat-message ${msg.type}`}>
              <div className="chat-message-avatar">
                {msg.type === 'bot' ? <BotIcon /> : <UserIcon />}
              </div>
              <div className="chat-message-content">
                <div className="chat-message-text">{msg.text}</div>
                <div className="chat-message-time">
                  {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="chat-message bot">
              <div className="chat-message-avatar">
                <BotIcon />
              </div>
              <div className="chat-message-content">
                <div className="chat-message-text loading">
                  <span className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
        
        {proofs.length > 0 && (
          <div className="proofs-container">
            <div className="proofs-header">
              <SparkleIcon />
              <span className="proofs-title">Sources & References</span>
            </div>
            <div className="proofs-list">
              {proofs.map((proof, idx) => (
                <div key={idx} className="proof-item">
                  <div className="proof-item-header">
                    <div className="proof-source">{proof.source || 'Unknown source'}</div>
                  </div>
                  <div className="proof-text">{proof.text || proof.content || ''}</div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        <div className="chat-input-container">
          <div className="chat-input-wrapper">
            <input
              className="chat-input"
              placeholder={selectedDomain ? "Ask about products, technology, or leadership..." : "Select a company first..."}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading || !selectedDomain}
            />
            <button 
              className="chat-send" 
              onClick={handleSend} 
              disabled={loading || !selectedDomain || !inputValue.trim()}
              title="Send message"
            >
              <SendIcon />
            </button>
          </div>
          <div className="chat-input-hint">
            Press Enter to send • Shift+Enter for new line
          </div>
        </div>
      </section>
    </aside>
  )
}

export default ChatPanel

