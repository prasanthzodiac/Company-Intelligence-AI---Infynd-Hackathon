"""
Gunicorn compatibility: many platforms default to `gunicorn app:app`.
The canonical entrypoint is `wsgi:app` (see wsgi.py).
"""
from wsgi import app  # noqa: F401

__all__ = ["app"]
