"""
Loads environment variables from .env and validates required settings.
"""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# -------------------------------------------------------------------
# Load .env file (if present)
# -------------------------------------------------------------------
load_dotenv()

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def _require_env(name: str) -> str:
    """
    Fetch a required environment variable.
    Raise RuntimeError if missing.
    """
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value.strip('"')

def _path_from_env(name: str) -> Path:
    """
    Convert environment variable to Path.
    """
    return Path(_require_env(name)).expanduser().resolve()


# -------------------------------------------------------------------
# Blocklist configuration
# -------------------------------------------------------------------
BLOCKLIST_URL: str = _require_env("BLOCKLIST_URL")

RAW_FILE_PATH: Path = _path_from_env("RAW_FILE_PATH")
FORMATTED_FILE_PATH: Path = _path_from_env("FORMATTED_FILE_PATH")
PROCESSED_IP_FILE_PATH: Path = _path_from_env("PROCESSED_IP_FILE_PATH")


# -------------------------------------------------------------------
# OpenCTI configuration
# -------------------------------------------------------------------
OPENCTI_URL: str = _require_env("OPENCTI_URL")
OPENCTI_TOKEN: str = _require_env("OPENCTI_TOKEN")