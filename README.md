## Company Intelligence Offline Pipeline

**Purpose**: Given a CSV of domains, this tool:
- Validates and manifests companies
- Downloads each site as an offline snapshot
- Crawls local HTML only
- Extracts a structured company profile via local Ollama (LLaMA-3)

### Project Layout

- `main.py`: Orchestrates the full pipeline
- `config/settings.yaml`: Paths and runtime settings
- `services/csv_loader.py`: CSV parsing and manifest management
- `services/downloader.py`: httrack / wget snapshot downloader
- `services/crawler.py`: Local HTML crawler and chunk generator
- `services/llm_extractor.py`: Ollama LLaMA-3 profile extraction
- `prompts/profile_extraction.txt`: System prompt for JSON-only extraction
- `data/`: Working data directory (auto-created)
- `output/`: Per-domain chunks and profiles (auto-created)
- `logs/`: Runtime logs (auto-created)

### Dependencies

Install Python dependencies:

```bash
pip install -r requirements.txt
```

You also need one of:
- `httrack` on PATH **or**
- `wget` on PATH

And a running Ollama server with LLaMA-3:

```bash
ollama pull llama3
ollama serve
```

### Input CSV Format

`domains.csv`:

```csv
domain
infynd.com
zoho.com
freshworks.com
```

Constraints:
- No protocol (no `https://`)
- No paths (no `/something`)
- Must be a valid domain

### Running the Pipeline

From the `company_intel` directory:

```bash
python main.py --input domains.csv
```

Outputs:
- `data/companies.csv` and `data/companies.json`: manifest with status per company
- `output/<domain>/chunks.json`: extracted content chunks
- `output/<domain>/profile.json`: structured company intelligence JSON


