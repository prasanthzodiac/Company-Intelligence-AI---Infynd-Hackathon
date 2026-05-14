#!/usr/bin/env python3
"""
Start the Flask backend API server
"""
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir.parent))

from backend.api.app import app

if __name__ == '__main__':
    print("Starting InFynd Company Intelligence AI Backend API...")
    print("Access the UI at: http://localhost:5000")
    print("API endpoints available at: http://localhost:5000/api")
    app.run(host='0.0.0.0', port=5000, debug=True)

