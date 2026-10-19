# src/connectors/jobtoday.py
import json
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from .base import BaseConnector, HTTP_HEADERS, logger
from ..matching.normalizer import generar_hash, limpiar_html, formatear_salario

class JobTodayConnector(BaseConnector):
    """Conector para Job Today (Albacete, Teletrabajo y puestos en tiempo parcial / tardes / fin de semana)."""
    URLS = [
        ("Job Today Albacete", "https://jobtoday.com/es/trabajos-albacete"),
        ("Job Today Albacete Parcial", "https://jobtoday.com/es/trabajos-albacete?q=media+jornada"),
        ("Job Today Teletrabajo", "https://jobtoday.com/es/trabajos-teletrabajo"),
        ("Job Today Teletrabajo Parcial", "https://jobtoday.com/es/trabajos-teletrabajo?q=media+jornada"),
        ("Job Today Teletrabajo Fines de Semana", "https://jobtoday.com/es/trabajos-teletrabajo?q=fin+de+semana"),
        ("Job Today Teletrabajo Tardes", "https://jobtoday.com/es/trabajos-teletrabajo?q=tardes"),
        ("Job Today Media Jornada", "https://jobtoday.com/es/trabajos?q=media+jornada"),
        ("Job Today Tardes", "https://jobtoday.com/es/trabajos?q=tardes"),
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
                s = soup.find("script", id="__NEXT_DATA__")
                if not s or not s.string:
                    continue
                jt_json = json.loads(s.string)
                props = jt_json.get("props", {}).get("pageProps", {})
                feed = props.get("feed", {})
                sections = feed.get("sections", [])

                for sec in sections:
                    if sec.get("type") != "items":
                        continue
                    items = sec.get("items", [])
                    for it in items:
                        p = it.get("payload", {})
                        if not p:
                            continue
                        role = p.get("role") or p.get("title")
                        if not role:
                            continue
                        
                        can_url = p.get("canonicalUrl") or p.get("slug") or ""
                        if not can_url:
                            key = p.get("key", "")
                            can_url = f"/es/trabajo/{key}" if key else ""
                        if can_url.startswith("/"):
                            job_url = f"https://jobtoday.com{can_url}"
                        else:
                            job_url = can_url

                        if not job_url or job_url in urls_vistas:
                            continue
                        urls_vistas.add(job_url)

                        empresa = p.get("companyName") or (p.get("company") or {}).get("name") or "Empresa Confidencial"
                        desc = p.get("description") or p.get("descriptionDeMarkdown") or role
                        direccion = p.get("address") or ""
                        addr_info = p.get("addressInfo") or {}
                        ciudad = addr_info.get("display", {}).get("city") or direccion or "España"

                        modalidad = "REMOTO" if "teletrabajo" in url.lower() or "remoto" in desc.lower() else "PRESENCIAL"
                        
                        emp_type = (p.get("employmentType") or "").upper()
                        if emp_type == "PART_TIME":
                            horario = "Tiempo parcial"
                        elif emp_type == "FULL_TIME":
                            horario = "Jornada completa"
                        else:
                            horario = "No especificado"

                        salario_raw = p.get("salary")
                        salario_limpio = formatear_salario(salario_raw)

                        ofertas.append({
                            "id": generar_hash(empresa, role, job_url),
                            "puesto": role.strip(),
                            "empresa": empresa.strip(),
                            "ubicacion": ciudad,
                            "modalidad": modalidad,
                            "horario": horario,
                            "salario": salario_limpio,
                            "url": job_url,
                            "fuente": "Job Today",
                            "descripcion": limpiar_html(desc),
                            "fecha_publicacion": p.get("createDate", "") or p.get("updateDate", "")
                        })
            except Exception as e:
                logger.warning("Error en %s: %s", nombre, e)

        logger.info("Job Today: %d ofertas recopiladas.", len(ofertas))
        return ofertas
