# Deploy API to Render or Railway (Flask + Gunicorn)

The Vercel app is static React only. Run the **Flask API** on Render or Railway, then set **`VITE_API_BASE_URL`** on Vercel to your public API root (no trailing slash), e.g. `https://company-intelligence-api.onrender.com/api`, and redeploy the frontend.

## Prerequisites

- Repo pushed to GitHub (or GitLab) with `data/`, `output/`, and `config/` as needed for your demo.
- **LLM**: `config/settings.yaml` defaults to Ollama at `http://localhost:11434`. On a PaaS host, `localhost` is wrong unless you run Ollama on the same machine. Point `llm.api_url` (and model) to a reachable HTTP chat API (Ollama on another server, or an OpenAI-compatible proxy). Chat and extraction will fail until this is reachable from the container.

## Render

1. [Render Dashboard](https://dashboard.render.com) → **New** → **Web Service** (or **Blueprint** if you use the repo `render.yaml`).
2. Connect the repository; root directory stays the **repo root** (where `requirements.txt` and `wsgi.py` live).
3. **Runtime**: Python 3.11 (optional: `runtime.txt` pins `3.11.9`).
4. **Build command**: `pip install -r requirements.txt`
5. **Start command**:  
   `gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 180 wsgi:app`
6. **Health check path** (optional): `/api/companies`
7. Deploy. Copy the service URL (e.g. `https://company-intelligence-api.onrender.com`).
8. On **Vercel**, set `VITE_API_BASE_URL` to `https://<your-render-host>/api` and redeploy the frontend.

**Notes:** Free web services spin down when idle; first request can be slow. Disk is ephemeral—uploads and new pipeline output can be lost on restart unless you add a disk or external storage.

## Railway

1. [Railway](https://railway.app) → **New Project** → **Deploy from GitHub repo** (select this repo).
2. Railway will detect Python via `requirements.txt` (Railpack). Ensure the service **root** is the repo root.
3. The repo **`railway.toml`** sets **start command** and **healthcheck** (`/api/companies`). Alternatively you can use the **`Procfile`** `web:` line or set the start command in the service **Settings**.
4. **Variables**: `PORT` is injected automatically; do not override unless you know what you are doing.
5. Generate a public domain (**Settings → Networking → Generate domain**), then set Vercel `VITE_API_BASE_URL` to `https://<your-railway-domain>/api` and redeploy the frontend.

**Notes:** Same caveats as Render for disk and LLM URL. Increase **timeout** in Railway if long pipeline steps hit HTTP limits.

## Quick local check (Linux / WSL / macOS)

```bash
pip install -r requirements.txt
export PORT=5000
gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 2 wsgi:app
```

Then open `http://127.0.0.1:5000/api/companies`.

## CORS

`flask-cors` is enabled for all origins by default in `backend/api/app.py`, so browser calls from your Vercel domain to the API URL are allowed.
