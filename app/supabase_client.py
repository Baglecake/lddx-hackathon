"""Supabase client for the synonym review backend."""

import os

_client = None


def get_supabase():
    """Get or create a Supabase client (singleton)."""
    global _client
    if _client is not None:
        return _client

    url = os.environ.get('SUPABASE_URL', '')
    key = os.environ.get('SUPABASE_ANON_KEY', '')
    if not url or not key:
        return None

    from supabase import create_client
    _client = create_client(url, key)
    return _client
