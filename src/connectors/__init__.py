# src/connectors/__init__.py
from .base import BaseConnector, HTTP_HEADERS
from .tecnoempleo import TecnoempleoConnector
from .infojobs import InfoJobsConnector
from .linkedin import LinkedInConnector
from .indeed import IndeedConnector
from .jobtoday import JobTodayConnector

__all__ = [
    "BaseConnector",
    "HTTP_HEADERS",
    "TecnoempleoConnector",
    "InfoJobsConnector",
    "LinkedInConnector",
    "IndeedConnector",
    "JobTodayConnector",
]
