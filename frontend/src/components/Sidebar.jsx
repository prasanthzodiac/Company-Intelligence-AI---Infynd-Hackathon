import React from 'react'
import './Sidebar.css'

const navItems = [
  { id: 'company-info', label: 'Overview', icon: '◉' },
  { id: 'services', label: 'Products & Services', icon: '◈' },
  { id: 'people', label: 'People & Team', icon: '◎' },
  { id: 'certifications', label: 'Certifications', icon: '◇' },
  { id: 'contact', label: 'Contact Information', icon: '◆' },
  { id: 'social', label: 'Social Media', icon: '◐' },
  { id: 'knowledge-graph', label: 'Knowledge Graph', icon: '◑' },
  { id: 'reports', label: 'Reports & Exports', icon: '◒' },
  { id: 'raw-scraped', label: 'Raw Scraped Data', icon: '◓' },
]

function Sidebar({ activePage, onPageChange }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <span className="logo-text-red">In</span>
        <span className="logo-text-white">Fynd</span>
        <span className="logo-subtitle">COMPANY INTELLIGENCE AI</span>
      </div>

      <nav className="nav-section">
        <div className="sidebar-section-title">Analysis Modules</div>
        <div className="nav-list">
          {navItems.map((item) => (
            <div
              key={item.id}
              className={`nav-item ${activePage === item.id ? 'active' : ''}`}
              onClick={() => onPageChange(item.id)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </div>
          ))}
        </div>
      </nav>

      <div className="sidebar-footer">
        <a href="https://www.infynd.com" target="_blank" rel="noopener noreferrer" className="book-call-btn">
          Book a Call
        </a>
        <div className="sidebar-footer-text">
          Powered by InFynd AI
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
