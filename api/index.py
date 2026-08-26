"""Vercel serverless entry point.

This file bridges Vercel's serverless runtime to the FastAPI app.
Vercel expects a handler at /api/index.py for Python apps.
"""
from app.main import app  # noqa: F401
