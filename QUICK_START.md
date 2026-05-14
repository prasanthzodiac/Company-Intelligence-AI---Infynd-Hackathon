# Quick Start Guide - InFynd Company Intelligence AI

## ✅ Current Status

- ✅ Frontend dependencies installed
- ✅ Backend server running on `http://localhost:5000`
- ✅ Frontend dev server running on `http://localhost:3000`
- ✅ Web scraping improvements implemented
- ✅ LLM extraction improvements implemented

## 🚀 Access the Application

### Development Mode (Current Setup)
- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:5000/api

The React frontend automatically proxies API requests to the Flask backend.

## 📋 What Was Improved

### 1. Web Scraping (`services/crawler.py`)
- ✅ Added text cleaning and normalization
- ✅ Better HTML parsing with error handling
- ✅ Improved structured data extraction (emails, phones, social links)
- ✅ Enhanced people/leadership detection
- ✅ Better filtering of invalid data

### 2. LLM Extraction (`services/llm_extractor.py`)
- ✅ Improved JSON parsing with error recovery
- ✅ Better handling of markdown code fences
- ✅ Enhanced prompt instructions for cleaner output
- ✅ Multiple fallback strategies for data extraction
- ✅ Better post-processing of extracted data

### 3. Frontend-Backend Integration
- ✅ React frontend properly connected to Flask backend
- ✅ API service layer for clean communication
- ✅ CORS enabled for development
- ✅ Error handling in API calls

## 🔧 Running the Project

### Start Backend (Terminal 1)
```bash
cd company_intel
python run_backend.py
```

### Start Frontend (Terminal 2)
```bash
cd company_intel/frontend
npm run dev
```

### Access the UI
Open your browser to: **http://localhost:3000**

## 📊 Features Available

1. **Company Selection**: Select from available companies
2. **Company Overview**: View company profile, industry, technology stack
3. **Products & Services**: Browse company offerings
4. **Leadership & Locations**: View team members and office locations
5. **Claims & Evidence**: See certifications and compliance info
6. **Trust & Risk**: Contact information and risk indicators
7. **Peer Comparison**: Social media presence
8. **Chatbot**: Ask questions about companies using local LLM

## 🐛 Troubleshooting

### Backend Not Starting
- Check if port 5000 is available
- Ensure Python dependencies are installed: `pip install -r requirements.txt`
- Check if Ollama is running (for chatbot): `ollama serve`

### Frontend Not Starting
- Check if port 3000 is available
- Ensure Node.js dependencies are installed: `cd frontend && npm install`
- Check for port conflicts

### No Company Data
- Run the pipeline first: `python main.py --input domains.csv`
- Ensure `data/companies.json` exists
- Check `output/<domain>/profile.json` files exist

### Chatbot Not Working
- Ensure Ollama is running: `ollama serve`
- Check if LLaMA-3 model is installed: `ollama pull llama3`
- Verify Ollama API is accessible at `http://localhost:11434`

## 📝 Next Steps

1. **Test the UI**: Navigate to http://localhost:3000 and explore
2. **Test Chatbot**: Select a company and ask questions
3. **Run Pipeline**: If you need to scrape new companies:
   ```bash
   python main.py --input domains.csv
   ```

## 🎯 Key Improvements Summary

- **Cleaner Text Extraction**: Better normalization and cleaning
- **Better JSON Parsing**: Handles LLM response variations
- **Improved Error Handling**: Graceful failures and recovery
- **Enhanced Data Quality**: Better filtering and validation
- **Modern React Frontend**: Component-based architecture
- **Seamless Integration**: Frontend and backend working together

---

**Status**: ✅ All systems operational!
- Backend: http://localhost:5000 ✅
- Frontend: http://localhost:3000 ✅

