# Deploy API to Render or Railway (Flask + Gunicorn)

The Vercel app is static React only. Run the **Flask API** on Render or Railway, then set **`VITE_API_BASE_URL`** on Vercel to your public API root (no trailing slash), e.g. `https://company-intelligence-api.onrender.com/api`, and redeploy the frontend.

## Prerequisites

- Repo pushed to GitHub (or GitLab) with `data/`, `output/`, and `config/` as needed for your demo.
- **LLM**: The app no longer assumes Ollama on `localhost` when you set environment variables on Render/Railway (see below). Without any LLM, scraping still runs; profiles use a **chunk-based fallback** when `LLM_FALLBACK_ON_ERROR=true` (default).

## Render

1. [Render Dashboard](https://dashboard.render.com) → **New** → **Web Service** (or **Blueprint** if you use the repo `render.yaml`).
2. Connect the repository; root directory stays the **repo root** (where `requirements.txt` and `wsgi.py` live).
3. **Runtime**: Python 3.11 (optional: `runtime.txt` pins `3.11.9`).
4. **Build command**: `pip install -r requirements.txt`
5. **Start command:** use exactly (do not use bare `gunicorn app:app` unless you have pulled the latest repo with root `app.py`):  
   `gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 180 wsgi:app`  
   Equivalent: `... gunicorn app:app` after **`app.py`** exists at repo root (re-exports the same application).
6. **Health check path** (optional): `/api/companies`
7. Deploy. Copy the service URL (e.g. `https://company-intelligence-api.onrender.com`).
8. On **Vercel**, set `VITE_API_BASE_URL` to `https://<your-render-host>/api` and redeploy the frontend.

**Notes:** Free web services spin down when idle; first request can be slow. Disk is ephemeral—uploads and new pipeline output can be lost on restart unless you add a disk or external storage.

### LLM on Render / Railway (required for full AI features)

Set these in the service **Environment** tab (copy from `.env.example`):

| Variable | Example (Ollama on another server) | Example (OpenAI) |
|----------|-----------------------------------|------------------|
| `LLM_PROVIDER` | `ollama` | `openai` |
| `LLM_API_URL` | `https://your-ollama-host:11434/api/chat` | `https://api.openai.com/v1/chat/completions` |
| `LLM_MODEL` | `llama3` | `gpt-4o-mini` |
| `LLM_API_KEY` | *(empty for Ollama)* | `sk-...` |

Optional: `LLM_MAX_WORKERS=2`, `LLM_FALLBACK_ON_ERROR=true`.

After deploy, open **`https://<your-api>/api/health`** — `llm.ok` should be `true`.

**Do not use `localhost` on Render** unless Ollama runs in the same container (unusual). Use a remote Ollama URL or OpenAI/Groq/etc.

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

## "Failed to fetch" / CSV upload error

1. Open **`https://<render-host>/api/health`** in a new tab. If it does not load, fix Render first.
2. **Vercel** → `VITE_API_BASE_URL` = `https://<render-host>/api` → **Redeploy** (required).
3. In DevTools → **Network**, the upload must go to **`onrender.com`**, not **`vercel.app`**.
4. Render free tier may **sleep** — wait 30–60s after first visit, then retry upload.
5. CSV must have a header column named **`domain`** (see repo `domains.csv`).

## Upload returns 404

1. Open **`https://<your-render-host>/api/health`** — must return `{"status":"ok",...}`. If this 404s, fix Render first (start command `wsgi:app` or `app:app`, latest code deployed).
2. **`VITE_API_BASE_URL`** must be the API root, e.g. `https://YOUR-SERVICE.onrender.com/api` (with `/api`). If you only set the host, the frontend now auto-appends `/api` after you redeploy Vercel.
3. **Redeploy Vercel** after changing env vars (build-time variable).
4. In the browser **Network** tab, the upload request must go to **`https://...onrender.com/api/upload-csv`**, not `...vercel.app/api/upload-csv`.
