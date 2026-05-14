# Project Structure - Cleaned and Organized

## 📁 Directory Structure

```
company_intel/
├── backend/                    # Flask backend API
│   ├── api/
│   │   └── app.py             # Flask application
│   └── services/
│       ├── chatbot_service.py  # Ollama chatbot integration
│       └── proofs_service.py  # Evidence/proof tracking
│
├── config/                     # Configuration files
│   └── settings.yaml          # Pipeline and LLM settings
│
├── data/                       # Downloaded website HTML files
│   ├── companies.csv          # Company manifest (CSV)
│   ├── companies.json         # Company manifest (JSON)
│   └── <domain>/              # Per-domain HTML files
│
├── frontend/                   # React frontend application
│   ├── src/                   # React source code
│   │   ├── components/        # React components
│   │   ├── services/         # API service layer
│   │   ├── App.jsx            # Main app component
│   │   └── main.jsx           # Entry point
│   ├── index.html             # HTML template
│   ├── package.json           # NPM dependencies
│   └── vite.config.js         # Vite configuration
│
├── logs/                       # Application logs
│   ├── pipeline_run.log      # Pipeline execution logs
│   ├── reextract.log         # Re-extraction logs
│   └── run.log               # General runtime logs
│
├── output/                     # Generated profiles and chunks
│   └── <domain>/              # Per-domain output
│       ├── chunks.json        # Extracted content chunks
│       └── profile.json       # Structured company profile
│
├── prompts/                    # LLM prompts
│   └── profile_extraction.txt # Profile extraction prompt
│
├── services/                   # Core pipeline services
│   ├── csv_loader.py         # CSV parsing and manifest
│   ├── crawler.py            # HTML crawler and text extraction
│   ├── downloader.py         # Website downloader
│   └── llm_extractor.py      # LLM profile extraction
│
├── main.py                    # Main pipeline orchestrator
├── run_backend.py             # Backend server entry point
├── run_full_pipeline.py       # Full pipeline runner
├── re_extract_profiles.py     # Batch re-extraction utility
├── re_extract_single.py       # Single domain re-extraction utility
│
├── requirements.txt           # Python dependencies
├── domains.csv                # Input domains list
│
└── Documentation/
    ├── README.md              # Main project README
    ├── README_BACKEND.md      # Backend documentation
    ├── README_FRONTEND.md     # Frontend documentation
    ├── QUICK_START.md         # Quick start guide
    ├── IMPROVEMENTS_SCRAPING.md # Scraping improvements
    └── PROJECT_STRUCTURE.md   # This file
```

## ✅ Required Files

### Core Application Files
- ✅ `main.py` - Main pipeline orchestrator
- ✅ `run_backend.py` - Backend server
- ✅ `run_full_pipeline.py` - Full pipeline runner
- ✅ `services/*.py` - All service modules
- ✅ `backend/**/*.py` - All backend modules
- ✅ `config/settings.yaml` - Configuration

### Utility Scripts
- ✅ `re_extract_profiles.py` - Batch re-extraction
- ✅ `re_extract_single.py` - Single domain re-extraction

### Configuration & Data
- ✅ `requirements.txt` - Python dependencies
- ✅ `domains.csv` - Input domains
- ✅ `prompts/profile_extraction.txt` - LLM prompt
- ✅ `data/` - Downloaded HTML files
- ✅ `output/` - Generated profiles
- ✅ `logs/` - Application logs

### Frontend
- ✅ `frontend/` - Complete React application
- ✅ `frontend/package.json` - NPM dependencies
- ✅ `frontend/src/` - React source code

### Documentation
- ✅ `README.md` - Main documentation
- ✅ `README_BACKEND.md` - Backend docs
- ✅ `README_FRONTEND.md` - Frontend docs
- ✅ `QUICK_START.md` - Quick start
- ✅ `IMPROVEMENTS_SCRAPING.md` - Improvements log

## 🗑️ Removed Files (Cleanup Completed)

### Duplicate/Old Files Removed
- ❌ `reextract_profiles.py` - Duplicate of `re_extract_profiles.py`
- ❌ `ui/index.html` - Old vanilla JS UI (replaced by React)
- ❌ `frontend/templates/index.html` - Old template (replaced by React)
- ❌ `Topic1_Input_Records.csv` - Old input file
- ❌ `package-lock.json` (root) - Only needed in frontend/

### Outdated Documentation Removed
- ❌ `README_COMPLETE.md` - Outdated, info merged into other docs
- ❌ `IMPROVEMENTS.md` - Outdated, replaced by `IMPROVEMENTS_SCRAPING.md`

### Empty Folders Removed
- ❌ All empty domain folders in root (50+ folders)
  - These were duplicates of `data/<domain>/` folders
  - All empty folders have been removed

## 📊 File Count Summary

- **Python Files**: 11 core files + utilities
- **React Components**: 13 JSX files + 6 CSS files
- **Documentation**: 6 markdown files
- **Configuration**: 2 files (YAML, requirements.txt)
- **Data**: Variable (depends on scraped companies)

## 🎯 Clean Structure Benefits

1. **No Duplicates**: Removed all duplicate scripts and files
2. **Clear Separation**: Backend, frontend, and pipeline clearly separated
3. **Organized Data**: All data in `data/` and `output/` folders
4. **Up-to-Date Docs**: Only current, relevant documentation
5. **Easy Navigation**: Logical folder structure

## 🚀 Next Steps

The project is now clean and organized. All required files are in place:
- ✅ Core pipeline functionality
- ✅ Backend API server
- ✅ React frontend
- ✅ Utility scripts
- ✅ Documentation
- ✅ Configuration files

You can now:
1. Run the pipeline: `python main.py --input domains.csv`
2. Start the backend: `python run_backend.py`
3. Start the frontend: `cd frontend && npm run dev`
4. Re-extract profiles: `python re_extract_profiles.py`

