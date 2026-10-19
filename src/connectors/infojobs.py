# src/connectors/infojobs.py
import re
import json
import requests
import feedparser
from typing import List, Dict, Any
from .base import BaseConnector, HTTP_HEADERS, logger
from ..matching.normalizer import generar_hash, limpiar_html

class InfoJobsConnector(BaseConnector):
    """Conector para InfoJobs (Albacete, Teletrabajo, Tiempo Parcial y Fines de Semana)."""
    URLS = [
        ("InfoJobs Albacete Parcial/Tardes", "https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword=parcial&provinceIds=3"),
        ("InfoJobs Teletrabajo Parcial", "https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword=parcial&teleworkingIds=2"),
        ("InfoJobs Teletrabajo Tardes", "https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword=tarde&teleworkingIds=2"),
        ("InfoJobs Teletrabajo Fines de Semana", "https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword=fin+de+semana&teleworkingIds=2"),
        ("InfoJobs Teletrabajo Sistemas Parcial", "https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword=sistemas&workdayIds=2&teleworkingIds=2"),
    ]
    RSS_URL = "https://www.infojobs.net/trabajos.rss"

    def fetch(self) -> List[Dict[str, Any]]:
        ofertas = []
        urls_vistas = set()

        for nombre, url in self.URLS:
            logger.info("Consultando %s...", nombre)
            try:
                resp = requests.get(url, headers=HTTP_HEADERS, timeout=15)
                if resp.status_code != 200:
                    continue
                match = re.search(r'window\.__INITIAL_PROPS__\s*=\s*JSON\.parse\("(.*?)"\);', resp.text)
                if match:
                    raw_json = match.group(1).encode('utf-8').decode('unicode_escape')
                    data = json.loads(raw_json)
                    offers = data.get("offers", [])
                    for of in offers:
                        link = of.get("link", "")
                        if link.startswith("//"):
                            link = f"https:{link}"
                        link_clean = link.split("?")[0] if link else ""
                        if not link_clean or link_clean in urls_vistas:
                            continue
                        urls_vistas.add(link_clean)

                        puesto = of.get("title", "Sin título").strip()
                        empresa = of.get("companyName") or of.get("author", {}).get("name") or "Empresa Confidencial"
                        ciudad = of.get("city", "España")
                        teleworking = of.get("teleworking", "")
                        modalidad = "REMOTO" if any(r in str(teleworking).lower() for r in ["remoto", "teletrabajo"]) else "PRESENCIAL"
                        horario = of.get("workday", "No especificado")
                        salario = of.get("salaryDescription") or "No especificado"
                        desc = of.get("description", "") or puesto

                        ofertas.append({
                            "id": generar_hash(empresa, puesto, link_clean),
                            "puesto": puesto,
                            "empresa": empresa,
                            "ubicacion": ciudad,
                            "modalidad": modalidad,
                            "horario": horario,
                            "salario": salario,
                            "url": link,
                            "fuente": "InfoJobs",
                            "descripcion": desc,
                            "fecha_publicacion": of.get("publishedAt", "")
                        })
            except Exception as e:
                logger.warning("Error en %s: %s", nombre, e)

        if len(ofertas) < 5:
            logger.info("Consultando RSS de respaldo de InfoJobs...")
            try:
                r_rss = requests.get(self.RSS_URL, headers=HTTP_HEADERS, timeout=10)
                if r_rss.status_code == 200:
                    feed = feedparser.parse(r_rss.content)
                    for entry in feed.entries:
                        link = entry.get("link", "").strip()
                        link_clean = link.split("?")[0] if link else ""
                        if not link_clean or link_clean in urls_vistas:
                            continue
                        urls_vistas.add(link_clean)

                        puesto = entry.get("title", "").strip()
                        raw_desc = entry.get("description", "")
                        empresa = "InfoJobs"
                        m_emp = re.search(r'<strong>Empresa</strong>:\s*(?:<[^>]+>)?([^<]+)', raw_desc)
                        if m_emp:
                            empresa = m_emp.group(1).strip()

                        ofertas.append({
                            "id": generar_hash(empresa, puesto, link_clean),
                            "puesto": puesto,
                            "empresa": empresa,
                            "ubicacion": "España",
                            "modalidad": "No especificada",
                            "horario": "No especificado",
                            "salario": "No especificado",
                            "url": link,
                            "fuente": "InfoJobs",
                            "descripcion": limpiar_html(raw_desc),
                            "fecha_publicacion": entry.get("published", "")
                        })
            except Exception as e:
                logger.warning("Error en RSS de InfoJobs: %s", e)

        logger.info("InfoJobs: %d ofertas recopiladas.", len(ofertas))
        return ofertas
