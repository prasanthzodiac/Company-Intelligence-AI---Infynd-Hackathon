#!/usr/bin/env python3
"""
Start the Flask backend API server (development).
Production: use Gunicorn — see Procfile and DEPLOYMENT.md.
"""
import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir.parent))

from backend.api.app import app

if __name__ == '__main__':
    port = int(os.environ.get("PORT", "5000"))
    print("Starting InFynd Company Intelligence AI Backend API...")
    print(f"Access the UI at: http://localhost:{port}")
    print(f"API endpoints available at: http://localhost:{port}/api")
    app.run(host="0.0.0.0", port=port, debug=True)

