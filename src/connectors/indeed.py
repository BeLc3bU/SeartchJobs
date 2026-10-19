# src/connectors/indeed.py
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseConnector, HTTP_HEADERS, cffi_requests, logger
from ..matching.normalizer import generar_hash

class IndeedConnector(BaseConnector):
    """Conector para Indeed España mediante emulación TLS de navegador (curl_cffi)."""
    URLS = [
        ("Indeed Albacete Parcial", "https://es.indeed.com/jobs?q=tiempo+parcial&l=Albacete"),
        ("Indeed Albacete Tardes", "https://es.indeed.com/jobs?q=tarde&l=Albacete"),
        ("Indeed Remoto Parcial", "https://es.indeed.com/jobs?q=tiempo+parcial&l=remoto"),
        ("Indeed Remoto Tardes", "https://es.indeed.com/jobs?q=tarde&l=remoto"),
        ("Indeed Remoto Fin de Semana", "https://es.indeed.com/jobs?q=fin+de+semana&l=remoto"),
    ]

    def fetch(self) -> List[Dict[str, Any]]:
        ofertas = []
        seen_jks = set()
        client = cffi_requests if cffi_requests else requests

        for nombre, url in self.URLS:
            logger.info("Consultando %s...", nombre)
            try:
                if cffi_requests:
                    resp = client.get(url, impersonate="chrome120", timeout=15)
                else:
                    resp = client.get(url, headers=HTTP_HEADERS, timeout=15)

                if resp.status_code != 200:
                    logger.warning("Indeed respondió con status %s en %s", resp.status_code, nombre)
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                links = [a for a in soup.find_all("a", href=True) if "jk=" in a["href"]]

                for a in links:
                    m = re.search(r'jk=([a-zA-Z0-9]+)', a["href"])
                    if not m:
                        continue
                    jk = m.group(1)
                    if jk in seen_jks:
                        continue
                    seen_jks.add(jk)

                    title = a.get_text().strip()
                    parent = a
                    for _ in range(6):
                        if parent.parent:
                            parent = parent.parent
                    contenedor_texto = re.sub(r'\s+', ' ', parent.get_text()).strip()

                    empresa = "Empresa Confidencial"
                    cmp_match = re.search(r'&cmp=([^&]+)', a["href"])
                    if cmp_match:
                        empresa = urllib.parse.unquote_plus(cmp_match.group(1))

                    job_url = f"https://es.indeed.com/viewjob?jk={jk}"
                    ubicacion = "Albacete" if "albacete" in url.lower() else "Remoto España"
                    modalidad = "REMOTO" if "remoto" in url.lower() else "PRESENCIAL / HÍBRIDO"

                    salario = "No especificado"
                    sal_match = re.search(r'(\d{1,2}(?:\.\d{3})*(?:[,\.]\d+)?\s*€(?:\s*(?:al\s*año|al\s*mes|a\s*la\s*hora))?)', contenedor_texto)
                    if sal_match:
                        salario = sal_match.group(1)

                    if not title or len(title) < 3 or "sueldos de" in title.lower():
                        title = contenedor_texto.split("domestiko")[0].split("EUROPREVEN")[0].strip()[:80] or "Puesto Técnico"

                    ofertas.append({
                        "id": generar_hash(empresa, title, job_url),
                        "puesto": title,
                        "empresa": empresa,
                        "ubicacion": ubicacion,
                        "modalidad": modalidad,
                        "horario": "No especificado",
                        "salario": salario,
                        "url": job_url,
                        "fuente": "Indeed",
                        "descripcion": contenedor_texto[:600],
                        "fecha_publicacion": ""
                    })
            except Exception as e:
                logger.warning("Error en %s: %s", nombre, e)

        logger.info("Indeed: %d ofertas recopiladas.", len(ofertas))
        return ofertas
