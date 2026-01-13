import os
import json
import logging
from urllib.parse import urlparse

from config import DATA_ROOT

logger = logging.getLogger(__name__)

# Base directory for storing session states
SESSIONS_DIR = os.path.join(DATA_ROOT, "sessions")

class AccountService:
    @staticmethod
    def _ensure_sessions_dir():
        if not os.path.exists(SESSIONS_DIR):
            os.makedirs(SESSIONS_DIR)
            logger.info(f"Created sessions directory: {SESSIONS_DIR}")

    @staticmethod
    def _get_domain_filename(url_or_domain: str) -> str:
        """Extracts the domain and converts to a safe filename."""
        if "://" in url_or_domain:
            domain = urlparse(url_or_domain).netloc
        else:
            domain = url_or_domain
        
        # Basic sanitization
        return domain.replace(":", "_").replace("/", "_") + ".json"

    @classmethod
    def save_session(cls, domain: str, storage_state: dict):
        """Saves the Playwright storage state for a domain."""
        cls._ensure_sessions_dir()
        filename = cls._get_domain_filename(domain)
        filepath = os.path.join(SESSIONS_DIR, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(storage_state, f, indent=2)
            logger.info(f"✅ Session saved for domain: {domain}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save session for {domain}: {e}")
            return False

    @classmethod
    def get_session_path(cls, url_or_domain: str) -> str | None:
        """Returns the absolute path to the session file if it exists."""
        filename = cls._get_domain_filename(url_or_domain)
        filepath = os.path.join(SESSIONS_DIR, filename)
        
        if os.path.exists(filepath):
            return filepath
        return None

    @classmethod
    def list_accounts(cls) -> list[str]:
        """Lists all domains that have saved sessions."""
        cls._ensure_sessions_dir()
        sessions = []
        for filename in os.listdir(SESSIONS_DIR):
            if filename.endswith(".json"):
                sessions.append(filename[:-5]) 
        return sessions

    @classmethod
    def delete_session(cls, domain: str) -> bool:
        """Deletes the session for a domain."""
        filepath = cls.get_session_path(domain)
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"🗑️ Session deleted for {domain}")
            return True
        return False
