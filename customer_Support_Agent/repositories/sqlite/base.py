import sqlite3
from typing import Any, Dict, Optional

from customer_Support_Agent.core.settings import ensure_directories, get_settings

def connect() -> sqlite3.Connection:
    """Establish a connection to the SQLite database."""
    settings = get_settings()
    ensure_directories(settings)
    return sqlite3.connect(settings.db_path)

