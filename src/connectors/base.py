# src/connectors/base.py
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any

try:
    from curl_cffi import requests as cffi_requests
except ImportError:
    cffi_requests = None

logger = logging.getLogger("JobAgent.Connectors")

HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}

class BaseConnector(ABC):
    @abstractmethod
    def fetch(self) -> List[Dict[str, Any]]:
        """Recupera ofertas crudas del portal correspondiente."""
        pass
