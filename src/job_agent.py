"""
job_agent.py - Agente autónomo de búsqueda diaria de empleo personalizado.
Diseñado para Pedro Úbeda Sánchez.

Fachada modular compatible con:
- tests unitarios existentes (tests/test_agent.py)
- scripts de ejecución diaria (.bat y GitHub Actions)
- arquitectura modular desacoplada (src/core, src/db, src/matching, src/connectors, src/notifiers)
"""

import sys
import logging

# Configuración de codificación para consola Windows/Linux
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Configuración de Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("JobAgent")

# Re-exportaciones de la arquitectura modular
from src.matching.normalizer import generar_hash, limpiar_html, formatear_salario
from src.matching.profile import (
    LOCALIDADES_LOCALES,
    TECH_KEYWORDS,
    EXCLUDED_PROFESSIONS,
    EXCLUDED_DEGREE_TITLES,
    FP_ACCEPTED_KEYWORDS,
    MANDATORY_DEGREE_KEYWORDS,
    TARGET_TITLE_KEYWORDS,
    VERIFICAR_KEYWORDS
)
from src.matching.matcher import ProfileMatcher
from src.db.manager import DatabaseManager, DB_PATH
from src.connectors.base import BaseConnector, HTTP_HEADERS
from src.connectors.tecnoempleo import TecnoempleoConnector
from src.connectors.infojobs import InfoJobsConnector
from src.connectors.linkedin import LinkedInConnector
from src.connectors.indeed import IndeedConnector
from src.connectors.jobtoday import JobTodayConnector
from src.notifiers.telegram import TelegramDispatcher
from src.core.agent import JobAgent

__all__ = [
    "generar_hash",
    "limpiar_html",
    "formatear_salario",
    "ProfileMatcher",
    "DatabaseManager",
    "DB_PATH",
    "BaseConnector",
    "HTTP_HEADERS",
    "TecnoempleoConnector",
    "InfoJobsConnector",
    "LinkedInConnector",
    "IndeedConnector",
    "JobTodayConnector",
    "TelegramDispatcher",
    "JobAgent"
]

if __name__ == "__main__":
    agent = JobAgent()
    if "--reclasificar" in sys.argv:
        count = agent.db.reclasificar_bd(agent.matcher)
        agent.db.exportar_json()
        print(f"Reclasificación completada: {count} ofertas actualizadas. Archivo ofertas.json sincronizado.")
    else:
        agent.ejecutar()
