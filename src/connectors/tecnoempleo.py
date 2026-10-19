# src/connectors/tecnoempleo.py
import requests
import feedparser
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseConnector, HTTP_HEADERS, logger
from ..matching.normalizer import generar_hash, limpiar_html

class TecnoempleoConnector(BaseConnector):
    """Conector para los feeds RSS y búsquedas de Tecnoempleo (Albacete, Teletrabajo y General IT)."""
    FEEDS = [
        ("Tecnoempleo Albacete", "https://www.tecnoempleo.com/alertas-empleo-rss.php?pr=albacete"),
        ("Tecnoempleo Teletrabajo", "https://www.tecnoempleo.com/alertas-empleo-rss.php?te=teletrabajo"),
        ("Tecnoempleo General", "https://www.tecnoempleo.com/alertas-empleo-rss.php"),
    ]

    def fetch(self) -> List[Dict[str, Any]]:
        ofertas = []
        urls_vistas = set()
        for nombre, url in self.FEEDS:
            logger.info("Consultando %s...", nombre)
            try:
                resp = requests.get(url, headers=HTTP_HEADERS, timeout=15)
                if resp.status_code != 200:
                    continue
                feed = feedparser.parse(resp.content)
                for entry in feed.entries:
                    link = entry.get("link", "").strip()
                    if not link or link in urls_vistas:
                        continue
                    urls_vistas.add(link)

                    puesto = entry.get("title", "").strip()
                    raw_desc = entry.get("description", "")
                    soup = BeautifulSoup(raw_desc, "html.parser")
                    
                    empresa = "Empresa Confidencial"
                    provincia = "España"
                    salario = "No especificado"
                    tecnologias = ""
                    modalidad = "PRESENCIAL / NO ESPECIFICADA"

                    for b_tag in soup.find_all("b"):
                        campo = b_tag.get_text().strip().lower()
                        parent_text = b_tag.next_sibling
                        valor = str(parent_text).strip() if parent_text else ""
                        if "empresa" in campo and valor:
                            empresa = valor
                        elif "provincia" in campo and valor:
                            provincia = valor
                        elif "salario" in campo and valor:
                            salario = valor
                        elif "tecnolog" in campo and valor:
                            tecnologias = valor

                    desc_text = limpiar_html(raw_desc)
                    if any(t in desc_text.lower() or t in provincia.lower() for t in ["100% teletrabajo", "teletrabajo", "remoto"]):
                        modalidad = "REMOTO"
                    elif any(loc in provincia.lower() or loc in desc_text.lower() for loc in ["albacete", "hellin", "hellín"]):
                        modalidad = "PRESENCIAL / HÍBRIDO LOCAL"

                    ofertas.append({
                        "id": generar_hash(empresa, puesto, link),
                        "puesto": puesto,
                        "empresa": empresa,
                        "ubicacion": provincia,
                        "modalidad": modalidad,
                        "horario": "No especificado",
                        "salario": salario,
                        "url": link,
                        "fuente": "Tecnoempleo",
                        "descripcion": f"{desc_text} Tecnologías: {tecnologias}".strip(),
                        "fecha_publicacion": entry.get("published", "")
                    })
            except Exception as e:
                logger.warning("Error en %s: %s", nombre, e)
        logger.info("Tecnoempleo: %d ofertas recopiladas.", len(ofertas))
        return ofertas
