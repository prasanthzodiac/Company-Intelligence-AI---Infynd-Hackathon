"""
WSGI entry for Gunicorn on Render, Railway, and other Linux hosts.
"""
from pathlib import Path
import sys

_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from backend.api.app import app  # noqa: E402

__all__ = ["app"]
