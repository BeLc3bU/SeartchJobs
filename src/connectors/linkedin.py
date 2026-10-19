# src/connectors/linkedin.py
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseConnector, HTTP_HEADERS, logger
from ..matching.normalizer import generar_hash

class LinkedInConnector(BaseConnector):
    """Conector para LinkedIn Jobs mediante la API pública guest search."""
    URLS = [
        ("LinkedIn Albacete Parcial", "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=tiempo%20parcial&location=Albacete%2C%20Castile-La%20Mancha%2C%20Spain"),
        ("LinkedIn Albacete Tardes", "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=tarde&location=Albacete%2C%20Castile-La%20Mancha%2C%20Spain"),
        ("LinkedIn Teletrabajo Media Jornada", "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=tiempo%20parcial&location=Spain&f_WT=2"),
        ("LinkedIn Teletrabajo Tardes", "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=tarde&location=Spain&f_WT=2"),
        ("LinkedIn Teletrabajo Fines de Semana", "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=fin%20de%20semana&location=Spain&f_WT=2"),
        ("LinkedIn España Aviónica Parcial", "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=avionica&location=Spain&f_JT=P")
    ]

    def fetch(self) -> List[Dict[str, Any]]:
        ofertas = []
        urls_vistas = set()

        for nombre, url in self.URLS:
            logger.info("Consultando %s...", nombre)
            try:
                resp = requests.get(url, headers=HTTP_HEADERS, timeout=15)
                if resp.status_code != 200:
                    continue
                soup = BeautifulSoup(resp.text, "html.parser")
                items = soup.find_all("li")
                for it in items:
                    link_elem = it.find("a", class_="base-card__full-link")
                    if not link_elem or not link_elem.get("href"):
                        continue
                    full_link = link_elem["href"].strip()
                    clean_url = full_link.split("?")[0]
                    if clean_url in urls_vistas:
                        continue
                    urls_vistas.add(clean_url)

                    title_elem = it.find("h3", class_="base-search-card__title")
                    puesto = title_elem.text.strip() if title_elem else "Sin título"

                    comp_elem = it.find("h4", class_="base-search-card__subtitle")
                    empresa = comp_elem.text.strip() if comp_elem else "Empresa Confidencial"

                    loc_elem = it.find("span", class_="job-search-card__location")
                    ubicacion = loc_elem.text.strip() if loc_elem else "España"

                    time_elem = it.find("time")
                    fecha = time_elem.get("datetime", "") if time_elem else ""

                    modalidad = "REMOTO" if "f_WT=2" in url else "PRESENCIAL / HÍBRIDO"

                    ofertas.append({
                        "id": generar_hash(empresa, puesto, clean_url),
                        "puesto": puesto,
                        "empresa": empresa,
                        "ubicacion": ubicacion,
                        "modalidad": modalidad,
                        "horario": "No especificado",
                        "salario": "No especificado",
                        "url": clean_url,
                        "fuente": "LinkedIn",
                        "descripcion": f"{puesto} en {empresa}. Ubicación: {ubicacion}.",
                        "fecha_publicacion": fecha
                    })
            except Exception as e:
                logger.warning("Error en %s: %s", nombre, e)

        logger.info("LinkedIn: %d ofertas recopiladas.", len(ofertas))
        return ofertas
