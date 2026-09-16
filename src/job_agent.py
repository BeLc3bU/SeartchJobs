"""
job_agent.py - Agente autónomo de búsqueda diaria de empleo personalizado.
Diseñado para Pedro Úbeda Sánchez.

Fuentes: Remotive API, Tecnoempleo RSS, WeWorkRemotely RSS, etc.
Persistencia: SQLite (data/empleo.db).
Notificaciones: Telegram Bot REST API.
"""

import os
import sys
import re
import json
import sqlite3
import hashlib
import logging
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
import urllib.parse

import requests
import feedparser
from bs4 import BeautifulSoup

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


# Rutas de base de datos
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "empleo.db")

# Headers estándar para peticiones
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}


# =====================================================================
# 1. GESTIÓN DE BASE DE DATOS SQLITE
# =====================================================================

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()


    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ofertas (
                    id TEXT PRIMARY KEY,
                    puesto TEXT NOT NULL,
                    empresa TEXT NOT NULL,
                    ubicacion TEXT,
                    modalidad TEXT,
                    horario TEXT,
                    salario TEXT,
                    url TEXT NOT NULL,
                    fuente TEXT NOT NULL,
                    clasificacion TEXT NOT NULL,  -- 'A', 'B', 'C'
                    estado TEXT DEFAULT 'NUEVA',  -- 'NUEVA', 'INTERESANTE', 'SOLICITADA', 'DESCARTADA'
                    requisitos_cumple TEXT,
                    requisitos_verificar TEXT,
                    motivo TEXT,
                    fecha_publicacion TEXT,
                    fecha_procesada TEXT NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ofertas_clasificacion ON ofertas(clasificacion)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ofertas_estado ON ofertas(estado)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ofertas_fecha ON ofertas(fecha_procesada)")
            conn.commit()
            logger.info("Base de datos SQLite verificada en %s", self.db_path)

    def existe_oferta(self, oferta_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM ofertas WHERE id = ?", (oferta_id,))
            return cursor.fetchone() is not None

    def guardar_oferta(self, oferta: Dict[str, Any]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO ofertas (
                    id, puesto, empresa, ubicacion, modalidad, horario, salario,
                    url, fuente, clasificacion, estado, requisitos_cumple,
                    requisitos_verificar, motivo, fecha_publicacion, fecha_procesada
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                oferta["id"],
                oferta["puesto"],
                oferta["empresa"],
                oferta.get("ubicacion", "No especificada"),
                oferta.get("modalidad", "No especificada"),
                oferta.get("horario", "No especificado"),
                oferta.get("salario", "No especificado"),
                oferta["url"],
                oferta.get("fuente", "Desconocida"),
                oferta["clasificacion"],
                oferta.get("estado", "NUEVA" if oferta["clasificacion"] in ("A", "B") else "DESCARTADA"),
                json.dumps(oferta.get("requisitos_cumple", []), ensure_ascii=False),
                json.dumps(oferta.get("requisitos_verificar", []), ensure_ascii=False),
                oferta.get("motivo", ""),
                oferta.get("fecha_publicacion", ""),
                oferta.get("fecha_procesada", datetime.now(timezone.utc).isoformat())
            ))
            conn.commit()

    def obtener_nuevas_relevantes(self, horas: int = 24) -> List[Dict[str, Any]]:
        """Recupera ofertas A o B insertadas recientemente."""
        limite_tiempo = (datetime.now(timezone.utc) - timedelta(hours=horas)).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM ofertas 
                WHERE clasificacion IN ('A', 'B') 
                  AND estado = 'NUEVA'
                  AND fecha_procesada >= ?
                ORDER BY clasificacion ASC, fecha_procesada DESC
            """, (limite_tiempo,))
            filas = cursor.fetchall()
            resultado = []
            for f in filas:
                d = dict(f)
                d["requisitos_cumple"] = json.loads(d["requisitos_cumple"] or "[]")
                d["requisitos_verificar"] = json.loads(d["requisitos_verificar"] or "[]")
                resultado.append(d)
            return resultado


# =====================================================================
# 2. MOTOR DE FILTRADO GEOGRÁFICO, HORARIO Y PERFIL DE PEDRO
# =====================================================================

class ProfileMatcher:
    """
    Evalúa y clasifica ofertas según el perfil multidisciplinar de Pedro:
    - 22 años Ejército del Aire y del Espacio (Cabo Primero).
    - Grado Superior ASIR / Informática de Gestión / INCIBE Ciberseguridad / NATO CRYPTO.
    - Aviónica, instrumentación, simuladores de vuelo (C-101, Pilatus).
    - Sysadmin (Linux, Windows Server, AD, Redes LAN/WAN, Soporte L2/L3).
    - Desarrollo & Automatización: Python, JavaScript, TypeScript, SQLite, Bash.
    - Logística de material aeronáutico/militar, almacén técnico, control de calidad y procedimientos.
    """

    # Localidades presenciales autorizadas
    LOCALIDADES_LOCALES = ["albacete", "hellin", "hellín", "chinchilla", "la gineta"]

    def __init__(self):
        # Mapeo léxico de competencias
        self.tech_keywords = {
            "sistemas_redes": [
                "linux", "debian", "ubuntu", "redhat", "centos", "rocky", "windows server",
                "active directory", "ldap", "redes", "lan", "wan", "routing", "switching",
                "vlan", "firewall", "vpn", "tcp/ip", "dns", "dhcp", "cisco", "mikrotik",
                "soporte", "helpdesk", "l2", "l3", "sysadmin", "administrador de sistemas",
                "asir", "virtualizacion", "vmware", "vsphere", "proxmox", "hyper-v"
            ],
            "avionica_electronica": [
                "avionica", "aviónica", "aeronautica", "aeronáutica", "simulador", "simuladores",
                "electronica", "electrónica", "hardware", "calibracion", "calibración",
                "banco de pruebas", "mantenimiento electronico", "mantenimiento electrónico",
                "instrumentacion", "instrumentación", "soldadura", "pcb", "osciloscopio",
                "multimetro", "multímetro", "c-101", "pilatus", "defensa", "militar"
            ],
            "desarrollo_automatizacion": [
                "python", "bash", "shell script", "powershell", "scripting", "automatizacion",
                "automatización", "sql", "sqlite", "javascript", "typescript", "react",
                "api rest", "git", "scraping", "ci/cd", "ansible"
            ],
            "logistica_calidad": [
                "almacen", "almacén", "logistica", "logística", "repuestos", "stock",
                "inventario", "compras tecnicas", "compras técnicas", "calidad",
                "procedimientos", "normativa", "documentacion tecnica", "documentación técnica",
                "iso 9001", "gestion de material", "gestión de material"
            ],
            "ciberseguridad": [
                "ciberseguridad", "seguridad informatica", "seguridad de la informacion",
                "incibe", "soc", "siem", "criptografia", "hardening", "iso 27001", "ens"
            ]
        }

        # Certificaciones o requisitos civiles a verificar para Clase B
        self.verificar_keywords = [
            ("easa", "Verificar requisito de licencia/normativa civil aeronáutica EASA (Parte 66 / Parte 145) frente a experiencia militar"),
            ("ccna", "Verificar exigencia de certificación oficial Cisco CCNA"),
            ("ccnp", "Verificar nivel avanzado Cisco CCNP"),
            ("aws", "Verificar certificación específica AWS Cloud"),
            ("azure", "Verificar certificación específica Microsoft Azure"),
            ("itil", "Verificar certificación en marco ITIL"),
            ("ingles", "Verificar nivel de inglés requerido (B2/C1) para operativa diaria"),
            ("b2", "Verificar nivel de inglés formal B2"),
            ("c1", "Verificar nivel de inglés formal C1")
        ]

    def _es_remoto_espana(self, texto: str, ubicacion: str, modalidad: str) -> bool:
        """Determina si la oferta es 100% teletrabajo compatible con España."""
        t_completo = f"{texto} {ubicacion} {modalidad}".lower()
        
        # Palabras de descarte de presencialidad pura obligatoria fuera de Albacete
        if "100% presencial" in t_completo or "presencial en madrid" in t_completo or "presencial en barcelona" in t_completo:
            return False

        # Comprobación de teletrabajo explícito
        remoto_terms = [
            "remoto", "teletrabajo", "100% remoto", "remoto 100%", "full remote",
            "remote from spain", "remote in spain", "remote (spain)", "spain remote",
            "desde casa", "trabajo a distancia", "distancia", "cualquier lugar de españa"
        ]
        if any(term in t_completo for term in remoto_terms):
            return True
        if modalidad.upper() == "REMOTO":
            return True
        return False

    def _es_local_tarde(self, texto: str, ubicacion: str, horario: str) -> Tuple[bool, str]:
        """
        Determina si es presencial/híbrido en Albacete o Hellín y si es compatible con turno de tarde.
        Descarta tajantemente turnos de mañana o jornada partida clásica presencial.
        """
        t_completo = f"{texto} {ubicacion} {horario}".lower()

        es_local = any(loc in t_completo for loc in self.LOCALIDADES_LOCALES)
        if not es_local:
            return False, "Ubicación fuera de Hellín o Albacete"

        # Comprobación de turno
        es_turno_manana = any(m in t_completo for m in ["turno de mañana", "solo mañanas", "horario de mañana", "jornada partida", "08:00 a 14:00", "09:00 a 14:00", "partida presencial"])
        es_turno_tarde = any(t in t_completo for t in ["turno de tarde", "tardes", "horario de tarde", "vespertino", "15:00 a", "16:00 a", "14:00 a 22:00", "15:00 a 23:00", "media jornada tarde"])

        if es_turno_manana and not es_turno_tarde:
            return False, "Horario presencial en turno de mañana o jornada partida (incompatible con tardes)"

        if es_turno_tarde:
            return True, "Presencial/Híbrido Albacete/Hellín en turno de tarde"

        # Si es local en Albacete/Hellín pero no especifica turno, es candidato potencial a verificar
        return True, "Presencial/Híbrido en Albacete/Hellín (turno exacto a verificar)"

    def evaluar_oferta(self, oferta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aplica filtros estrictos y categoriza en A, B o C sin porcentajes numéricos arbitrarios.
        """
        puesto = oferta.get("puesto", "")
        descripcion = oferta.get("descripcion", "")
        ubicacion = oferta.get("ubicacion", "")
        modalidad = oferta.get("modalidad", "")
        horario = oferta.get("horario", "")
        
        texto_analisis = f"{puesto} {descripcion} {ubicacion} {modalidad} {horario}".lower()

        # 1. FILTRO ESTRICTO DE MODALIDAD / UBICACIÓN Y HORARIO
        es_remoto = self._es_remoto_espana(texto_analisis, ubicacion, modalidad)
        es_local_tarde, motivo_local = self._es_local_tarde(texto_analisis, ubicacion, horario)

        if not es_remoto and not es_local_tarde:
            # Descartada directamente por geografía u horario
            return {
                "clasificacion": "C",
                "motivo": f"Descartada por restricciones de ubicación/horario: {motivo_local}",
                "requisitos_cumple": [],
                "requisitos_verificar": []
            }

        # 2. EVALUACIÓN DE COMPETENCIAS TÉCNICAS Y OPERATIVAS
        cumple = []
        puntos_fuertes = set()

        for area, kw_list in self.tech_keywords.items():
            coincidencias = [kw for kw in kw_list if re.search(r'\b' + re.escape(kw) + r'\b', texto_analisis)]
            if coincidencias:
                if area == "sistemas_redes":
                    puntos_fuertes.add("Sistemas / Redes / ASIR")
                    cumple.append(f"Administración de sistemas y redes: {', '.join(coincidencias[:4])}")
                elif area == "avionica_electronica":
                    puntos_fuertes.add("Aviónica / Electrónica / Simulación")
                    cumple.append(f"Aviónica, hardware y sistemas críticos: {', '.join(coincidencias[:4])}")
                elif area == "desarrollo_automatizacion":
                    puntos_fuertes.add("Desarrollo / Automatización")
                    cumple.append(f"Automatización y scripting: {', '.join(coincidencias[:4])}")
                elif area == "logistica_calidad":
                    puntos_fuertes.add("Logística / Calidad / Procedimientos")
                    cumple.append(f"Gestión de material, almacén y control de calidad: {', '.join(coincidencias[:4])}")
                elif area == "ciberseguridad":
                    puntos_fuertes.add("Ciberseguridad")
                    cumple.append(f"Ciberseguridad y protección de sistemas: {', '.join(coincidencias[:4])}")

        # Requisitos a verificar (certificaciones civiles o inglés)
        verificar = []
        for kw, desc in self.verificar_keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', texto_analisis):
                verificar.append(desc)

        if not es_remoto and "turno exacto a verificar" in motivo_local:
            verificar.append("Confirmar con la empresa disponibilidad de turno exclusivo de tarde")

        # 3. DETERMINACIÓN DE CLASE (A, B, C)
        # Si no encaja con ninguna competencia técnica/operativa de Pedro -> Clase C
        if not puntos_fuertes:
            return {
                "clasificacion": "C",
                "motivo": "No presenta afinidad técnica ni operativa suficiente con las áreas de especialización de Pedro.",
                "requisitos_cumple": [],
                "requisitos_verificar": []
            }

        # Motivo explicativo de valor
        mod_desc = "Teletrabajo 100% compatible" if es_remoto else "Posición local en Hellín/Albacete"
        motivo = f"{mod_desc}. Oportunidad sólida en {' + '.join(puntos_fuertes)} donde tu bagaje de 22 años en sistemas críticos y disciplina operativa aporta diferenciación inmediata."

        # Clase B si hay certificaciones civiles a validar o verificar turno local
        if len(verificar) > 0 or ("Aviónica" in puntos_fuertes and "easa" in texto_analisis):
            clasificacion = "B"
        else:
            clasificacion = "A"

        return {
            "clasificacion": clasificacion,
            "motivo": motivo,
            "requisitos_cumple": cumple,
            "requisitos_verificar": verificar
        }


# =====================================================================
# 3. CONECTORES DE INGESTA DE FUENTES DE DATOS
# =====================================================================

def generar_hash(empresa: str, puesto: str, url: str) -> str:
    """Genera un hash SHA-256 corto y unívoco."""
    semilla = f"{empresa.strip().lower()}|{puesto.strip().lower()}|{url.strip().lower()}"
    return hashlib.sha256(semilla.encode("utf-8")).hexdigest()[:12]

def limpiar_html(html_text: str) -> str:
    """Elimina etiquetas HTML y limpia espacios redundantes."""
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, "html.parser")
    texto = soup.get_text(separator=" ")
    return re.sub(r'\s+', ' ', texto).strip()


class RemotiveConnector:
    """Conector a la API abierta de Remotive."""
    URL = "https://remotive.com/api/remote-jobs"

    def fetch(self) -> List[Dict[str, Any]]:
        logger.info("Consultando API de Remotive...")
        try:
            resp = requests.get(self.URL, headers=HTTP_HEADERS, timeout=20)
            if resp.status_code != 200:
                logger.warning("Remotive respondió con status %s", resp.status_code)
                return []
            data = resp.json()
            jobs = data.get("jobs", [])
            logger.info("Remotive: %d ofertas recibidas.", len(jobs))
            
            ofertas_normalizadas = []
            for j in jobs:
                # Filtrar solo ofertas que permitan candidatos de España o Anywhere/Worldwide/Europe
                location = (j.get("candidate_required_location") or "").lower()
                permitido = any(loc in location for loc in ["spain", "españa", "worldwide", "anywhere", "europe", "emea", ""])
                if not permitido:
                    continue

                empresa = j.get("company_name", "Empresa Confidencial")
                puesto = j.get("title", "Sin título")
                url = j.get("url", "")
                if not url:
                    continue

                ofertas_normalizadas.append({
                    "id": generar_hash(empresa, puesto, url),
                    "puesto": puesto,
                    "empresa": empresa,
                    "ubicacion": j.get("candidate_required_location") or "Remoto España / Global",
                    "modalidad": "REMOTO",
                    "horario": "FLEXIBLE",
                    "salario": j.get("salary") or "No especificado",
                    "url": url,
                    "fuente": "Remotive API",
                    "descripcion": limpiar_html(j.get("description", "")),
                    "fecha_publicacion": j.get("publication_date", "")
                })
            return ofertas_normalizadas
        except Exception as e:
            logger.error("Error al conectar con Remotive: %s", e)
            return []


class TecnoempleoRSSConnector:
    """Conector para el feed RSS público de Tecnoempleo con metadatos estructurados."""
    URL = "https://www.tecnoempleo.com/alertas-empleo-rss.php"

    def fetch(self) -> List[Dict[str, Any]]:
        logger.info("Consultando RSS de Tecnoempleo...")
        try:
            resp = requests.get(self.URL, headers=HTTP_HEADERS, timeout=20)
            if resp.status_code != 200:
                logger.warning("Tecnoempleo RSS respondió con status %s", resp.status_code)
                return []

            feed = feedparser.parse(resp.content)
            logger.info("Tecnoempleo RSS: %d entradas encontradas.", len(feed.entries))

            ofertas = []
            for entry in feed.entries:
                puesto = entry.get("title", "").strip()
                url = entry.get("link", "").strip()
                raw_desc = entry.get("description", "")

                # Extraer campos estructurados del HTML del feed de Tecnoempleo
                soup = BeautifulSoup(raw_desc, "html.parser")
                
                empresa = "Empresa Confidencial"
                provincia = "España"
                salario = "No especificado"
                tecnologias = ""
                modalidad = "PRESENCIAL / NO ESPECIFICADA"

                # Analizar campos b/text
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
                    elif "tecnologías" in campo or "tecnologias" in campo and valor:
                        tecnologias = valor

                desc_text = limpiar_html(raw_desc)

                # Detección de modalidad y provincia
                if any(t in desc_text.lower() or t in provincia.lower() for t in ["100% teletrabajo", "teletrabajo", "remoto"]):
                    modalidad = "REMOTO"
                elif any(loc in provincia.lower() or loc in desc_text.lower() for loc in ["albacete", "hellin", "hellín"]):
                    modalidad = "PRESENCIAL / HÍBRIDO LOCAL"

                if not url:
                    continue

                ofertas.append({
                    "id": generar_hash(empresa, puesto, url),
                    "puesto": puesto,
                    "empresa": empresa,
                    "ubicacion": provincia,
                    "modalidad": modalidad,
                    "horario": "No especificado",
                    "salario": salario,
                    "url": url,
                    "fuente": "Tecnoempleo RSS",
                    "descripcion": f"{desc_text} Tecnologías: {tecnologias}",
                    "fecha_publicacion": entry.get("published", "")
                })
            return ofertas
        except Exception as e:
            logger.error("Error al consultar Tecnoempleo RSS: %s", e)
            return []


class WeWorkRemotelyConnector:
    """Conector a feeds RSS de WeWorkRemotely para categorías DevOps, Sysadmin y Programación."""
    FEEDS = [
        ("WWR DevOps/Sysadmin", "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss"),
        ("WWR Programming", "https://weworkremotely.com/categories/remote-programming-jobs.rss")
    ]

    def fetch(self) -> List[Dict[str, Any]]:
        todas = []
        for name, url in self.FEEDS:
            logger.info("Consultando RSS de %s...", name)
            try:
                resp = requests.get(url, headers=HTTP_HEADERS, timeout=15)
                if resp.status_code != 200:
                    continue
                feed = feedparser.parse(resp.content)
                for entry in feed.entries:
                    puesto_raw = entry.get("title", "")
                    # Generalmente viene en formato "Empresa: Puesto"
                    partes = puesto_raw.split(":", 1)
                    if len(partes) == 2:
                        empresa = partes[0].strip()
                        puesto = partes[1].strip()
                    else:
                        empresa = "Empresa WWR"
                        puesto = puesto_raw.strip()

                    url_job = entry.get("link", "")
                    if not url_job:
                        continue

                    desc = limpiar_html(entry.get("description", ""))
                    todas.append({
                        "id": generar_hash(empresa, puesto, url_job),
                        "puesto": puesto,
                        "empresa": empresa,
                        "ubicacion": "100% Remoto",
                        "modalidad": "REMOTO",
                        "horario": "FLEXIBLE",
                        "salario": "No especificado",
                        "url": url_job,
                        "fuente": name,
                        "descripcion": desc,
                        "fecha_publicacion": entry.get("published", "")
                    })
            except Exception as e:
                logger.warning("Error en feed %s: %s", name, e)
        return todas


# =====================================================================
# 4. DESPACHADOR DE NOTIFICACIONES TELEGRAM
# =====================================================================

class TelegramDispatcher:
    """Envío de alertas formateadas mediante la API REST de Telegram."""
    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        self.token = token or os.environ.get("TELEGRAM_TOKEN")
        self.chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
        self.api_url = f"https://api.telegram.org/bot{self.token}/sendMessage" if self.token else None

    def esta_configurado(self) -> bool:
        return bool(self.token and self.chat_id)

    def enviar_mensaje(self, texto_html: str) -> bool:
        if not self.esta_configurado():
            logger.warning("Telegram no está configurado (faltan TELEGRAM_TOKEN o TELEGRAM_CHAT_ID). Mensaje en log:\n%s", texto_html)
            return False

        payload = {
            "chat_id": self.chat_id,
            "text": texto_html,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        try:
            resp = requests.post(self.api_url, json=payload, timeout=20)
            if resp.status_code == 200:
                logger.info("Mensaje enviado con éxito a Telegram.")
                return True
            else:
                logger.error("Error al enviar a Telegram (status %d): %s", resp.status_code, resp.text)
                return False
        except Exception as e:
            logger.error("Excepción de conexión con Telegram: %s", e)
            return False

    def enviar_bloques(self, bloques: List[str]):
        """Envía una lista de bloques HTML asegurando el límite de 4096 caracteres de Telegram."""
        if not bloques:
            return

        mensaje_actual = ""
        for bloque in bloques:
            if len(mensaje_actual) + len(bloque) + 2 > 4000:
                self.enviar_mensaje(mensaje_actual.strip())
                mensaje_actual = bloque + "\n\n"
            else:
                mensaje_actual += bloque + "\n\n"

        if mensaje_actual.strip():
            self.enviar_mensaje(mensaje_actual.strip())

    def formatear_oferta_html(self, oferta: Dict[str, Any]) -> str:
        """Formatea una vacante individual con la estructura exigida."""
        clase = oferta.get("clasificacion", "A")
        badge = "🟢 <b>CLASE A (Encaje Directo)</b>" if clase == "A" else "🟡 <b>CLASE B (Encaje Potencial)</b>"
        
        req_cumple = oferta.get("requisitos_cumple", [])
        req_verificar = oferta.get("requisitos_verificar", [])

        cumple_html = ""
        if req_cumple:
            items = "".join([f"  • {c}\n" for c in req_cumple])
            cumple_html = f"\n<b>✅ Requisitos que cumplo:</b>\n{items}"

        verificar_html = ""
        if req_verificar:
            items = "".join([f"  • {v}\n" for v in req_verificar])
            verificar_html = f"\n<b>🔍 Requisitos a verificar:</b>\n{items}"
        elif clase == "B":
            verificar_html = "\n<b>🔍 Requisitos a verificar:</b>\n  • Validar horario presencial o acreditación civil específica.\n"

        motivo = oferta.get("motivo", "")
        motivo_html = f"\n<b>💡 Por qué merece atención:</b>\n<i>{motivo}</i>\n" if motivo else ""

        bloque = (
            f"💼 <b>{oferta.get('puesto', 'Puesto')}</b>\n"
            f"🏢 <b>Empresa:</b> {oferta.get('empresa', 'No indicada')}\n"
            f"🏷️ <b>Evaluación:</b> {badge}\n"
            f"📍 <b>Ubicación/Modalidad:</b> {oferta.get('ubicacion', '')} ({oferta.get('modalidad', '')})\n"
            f"💰 <b>Salario:</b> {oferta.get('salario', 'No especificado')}\n"
            f"{cumple_html}"
            f"{verificar_html}"
            f"{motivo_html}"
            f"🔗 <a href='{oferta.get('url', '#')}'>Ver oferta original en {oferta.get('fuente', 'Portal')}</a>\n"
            f"🆔 <code>Hash: {oferta.get('id', '')}</code>"
        )
        return bloque


# =====================================================================
# 5. PIPELINE PRINCIPAL DE EJECUCIÓN
# =====================================================================

class JobAgent:
    def __init__(self):
        self.db = DatabaseManager()
        self.matcher = ProfileMatcher()
        self.telegram = TelegramDispatcher()
        
        # Conectores desacoplados
        self.connectors = [
            RemotiveConnector(),
            TecnoempleoRSSConnector(),
            WeWorkRemotelyConnector()
        ]

    def ejecutar(self):
        logger.info("=== INICIANDO AGENTE DE BÚSQUEDA DE EMPLEO ===")
        ahora_str = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

        # 1. Ingesta de todas las fuentes
        todas_ofertas = []
        for conn in self.connectors:
            try:
                items = conn.fetch()
                todas_ofertas.extend(items)
            except Exception as e:
                logger.error("Error en conector %s: %s", conn.__class__.__name__, e)

        logger.info("Total de ofertas crudas recopiladas: %d", len(todas_ofertas))

        # 2. Deduplicación y Evaluación
        nuevas_procesadas = 0
        ofertas_notificar = []

        for raw_job in todas_ofertas:
            job_id = raw_job["id"]
            
            # Comprobar si ya existe en la base de datos
            if self.db.existe_oferta(job_id):
                continue

            # Evaluar con el motor léxico y de restricciones
            evaluacion = self.matcher.evaluar_oferta(raw_job)
            
            raw_job["clasificacion"] = evaluacion["clasificacion"]
            raw_job["motivo"] = evaluacion["motivo"]
            raw_job["requisitos_cumple"] = evaluacion["requisitos_cumple"]
            raw_job["requisitos_verificar"] = evaluacion["requisitos_verificar"]
            raw_job["fecha_procesada"] = datetime.now(timezone.utc).isoformat()

            # Guardar en SQLite (todas se persisten, incluidas las descartadas C para no reprocesar)
            self.db.guardar_oferta(raw_job)
            nuevas_procesadas += 1

            if raw_job["clasificacion"] in ("A", "B"):
                ofertas_notificar.append(raw_job)

        logger.info("Nuevas ofertas insertadas en BD: %d. Relevantes (A/B): %d.", nuevas_procesadas, len(ofertas_notificar))

        # 3. Despacho a Telegram
        if ofertas_notificar:
            cabecera = (
                f"🎯 <b>REPORTE DIARIO DE EMPLEO PERSONALIZADO</b>\n"
                f"📅 <i>{ahora_str}</i>\n"
                f"👤 <b>Candidato:</b> Pedro Úbeda Sánchez\n"
                f"Se han detectado <b>{len(ofertas_notificar)} ofertas</b> con encaje directo o potencial cumpliendo las restricciones horarias y de teletrabajo/Albacete:\n"
                f"────────────────────────"
            )
            bloques = [cabecera]
            for of in ofertas_notificar:
                bloques.append(self.telegram.formatear_oferta_html(of))

            pie = (
                "💡 <i>Usa el comando CLI para gestionar el estado:</i>\n"
                "<code>python src/gestionar.py &lt;hash&gt; &lt;ESTADO&gt;</code>"
            )
            bloques.append(pie)
            self.telegram.enviar_bloques(bloques)
        else:
            # Mensaje conciso notificando que no hubo novedades
            msg_tranquilidad = (
                f"✅ <b>Agente de Empleo: Búsqueda Diaria Finalizada</b>\n"
                f"📅 <i>{ahora_str}</i>\n\n"
                f"No se han detectado nuevas ofertas con encaje <b>Clase A</b> o <b>Clase B</b> en las últimas 24 horas "
                f"que cumplan las restricciones horarias y geográficas (Remoto 100% España o Presencial Tarde Hellín/Albacete).\n\n"
                f"Base de datos SQLite actualizada correctamente."
            )
            self.telegram.enviar_mensaje(msg_tranquilidad)

        logger.info("=== EJECUCIÓN FINALIZADA SATISFACTORIAMENTE ===")


if __name__ == "__main__":
    agent = JobAgent()
    agent.ejecutar()
