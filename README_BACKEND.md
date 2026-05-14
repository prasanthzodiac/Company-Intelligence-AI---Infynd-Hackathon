# InFynd Company Intelligence AI - Backend & Frontend Structure

## Project Structure

```
company_intel/
├── backend/
│   ├── api/
│   │   └── app.py              # Flask API server
│   └── services/
│       ├── chatbot_service.py  # Ollama chatbot integration
│       └── proofs_service.py   # Evidence/proof tracking
├── frontend/
│   └── templates/
│       └── index.html          # Main UI
├── services/                   # Pipeline services (CSV, downloader, crawler, LLM)
├── config/
│   └── settings.yaml
└── main.py                     # Pipeline entry point
```

## Running the Backend API

### Prerequisites
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Ensure Ollama is running:
   ```bash
   ollama serve
   ```

### Start the Backend Server

```bash
python run_backend.py
```

The API will be available at `http://localhost:5000`

### API Endpoints

- `GET /api/companies` - List all companies
- `GET /api/companies/<domain>/profile` - Get company profile
- `GET /api/companies/<domain>/chunks` - Get company chunks
- `POST /api/chat` - Chatbot endpoint
  ```json
  {
    "question": "What products does this company offer?",
    "domain": "example.com"
  }
  ```
- `GET /api/proofs/<domain>?query=<query>` - Get proofs for a query

### Frontend Access

**Development Mode:**
- React dev server: `http://localhost:3000` (run `npm run dev` in `frontend/` directory)
- Flask API: `http://localhost:5000/api`

**Production Mode:**
- After building React (`npm run build` in `frontend/`), access the UI at:
```
http://localhost:5000
```
The Flask backend automatically serves the React build when `frontend/dist` exists.

## Features

### New Fields Added
- **Sectors**: Array of industry sectors
- **SSC Code**: Standard Industrial Classification code
- **Long Description**: Full company description
- **Short Description**: Brief company summary

### Chatbot
- Connects to local Ollama LLaMA-3 model
- Answers questions based on extracted company data
- Provides proof sources for responses

### Proofs System
- Tracks evidence sources for chatbot responses
- Shows relevant page sections and content
- Displays source paths and relevance scores

