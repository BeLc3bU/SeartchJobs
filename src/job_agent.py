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

try:
    from curl_cffi import requests as cffi_requests
except ImportError:
    cffi_requests = None

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

            # Migración: asegurar que la columna descripcion existe
            cursor.execute("PRAGMA table_info(ofertas)")
            cols = [col[1] for col in cursor.fetchall()]
            if "descripcion" not in cols:
                cursor.execute("ALTER TABLE ofertas ADD COLUMN descripcion TEXT DEFAULT ''")

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
                    requisitos_verificar, motivo, fecha_publicacion, fecha_procesada, descripcion
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                oferta.get("fecha_procesada", datetime.now(timezone.utc).isoformat()),
                oferta.get("descripcion", "")
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

    def obtener_resumen(self) -> Dict[str, int]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT estado, COUNT(*) FROM ofertas GROUP BY estado")
            estados = dict(cursor.fetchall())
            cursor.execute("SELECT clasificacion, COUNT(*) FROM ofertas GROUP BY clasificacion")
            clases = dict(cursor.fetchall())
            return {"estados": estados, "clases": clases}

    def obtener_interesantes(self, limite: int = 10) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM ofertas 
                WHERE estado = 'INTERESANTE' 
                ORDER BY fecha_procesada DESC LIMIT ?
            """, (limite,))
            filas = cursor.fetchall()
            res = []
            for f in filas:
                d = dict(f)
                d["requisitos_cumple"] = json.loads(d["requisitos_cumple"] or "[]")
                d["requisitos_verificar"] = json.loads(d["requisitos_verificar"] or "[]")
    def obtener_ultimas_activas(self, limite: int = 5, clasificacion: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if clasificacion:
                cursor.execute("""
                    SELECT * FROM ofertas 
                    WHERE clasificacion = ? AND estado != 'DESCARTADA'
                    ORDER BY fecha_procesada DESC LIMIT ?
                """, (clasificacion, limite))
            else:
                cursor.execute("""
                    SELECT * FROM ofertas 
                    WHERE clasificacion IN ('A', 'B') AND estado != 'DESCARTADA'
                    ORDER BY clasificacion ASC, fecha_procesada DESC LIMIT ?
                """, (limite,))
            filas = cursor.fetchall()
            res = []
            for f in filas:
                d = dict(f)
                d["requisitos_cumple"] = json.loads(d["requisitos_cumple"] or "[]")
                d["requisitos_verificar"] = json.loads(d["requisitos_verificar"] or "[]")
                res.append(d)
            return res

    def actualizar_estado_oferta(self, hash_prefix: str, nuevo_estado: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, puesto, empresa, estado FROM ofertas WHERE id LIKE ?", (f"{hash_prefix}%",))
            filas = cursor.fetchall()
            if not filas or len(filas) > 1:
                return None
            of = filas[0]
            cursor.execute("UPDATE ofertas SET estado = ? WHERE id = ?", (nuevo_estado, of["id"]))
            conn.commit()
            return dict(of)

    def exportar_json(self, output_path: Optional[str] = None):
        """Exporta las ofertas de Clase A y B a un archivo JSON para consumo por el Webhook de Cloudflare."""
        if not output_path:
            output_path = os.path.join(os.path.dirname(self.db_path), "ofertas.json")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, puesto, empresa, ubicacion, modalidad, horario, salario,
                       url, fuente, clasificacion, estado, requisitos_cumple,
                       requisitos_verificar, motivo, fecha_publicacion, fecha_procesada
                FROM ofertas
                WHERE clasificacion IN ('A', 'B')
                ORDER BY clasificacion ASC, fecha_procesada DESC
            """)
            filas = cursor.fetchall()
            datos = []
            for f in filas:
                d = dict(f)
                d["requisitos_cumple"] = json.loads(d["requisitos_cumple"] or "[]")
                d["requisitos_verificar"] = json.loads(d["requisitos_verificar"] or "[]")
                datos.append(d)
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)
            logger.info("Exportado archivo JSON con %d ofertas en %s", len(datos), output_path)

    def reclasificar_bd(self, matcher: 'ProfileMatcher') -> int:
        """Re-evalúa todas las ofertas de la BD con el matcher actual (filtro idioma español + restricciones)."""
        actualizadas = 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ofertas")
            filas = cursor.fetchall()
            for f in filas:
                of_dict = dict(f)
                res = matcher.evaluar_oferta(of_dict)
                nueva_clase = res["clasificacion"]
                nuevo_motivo = res["motivo"]
                nuevo_cumple = json.dumps(res.get("requisitos_cumple", []), ensure_ascii=False)
                nuevo_verif = json.dumps(res.get("requisitos_verificar", []), ensure_ascii=False)
                
                nuevo_estado = of_dict["estado"]
                if nueva_clase == "C" and of_dict["estado"] != "DESCARTADA":
                    nuevo_estado = "DESCARTADA"

                if (nueva_clase != of_dict["clasificacion"] or 
                    nuevo_motivo != of_dict["motivo"] or 
                    nuevo_estado != of_dict["estado"]):
                    cursor.execute("""
                        UPDATE ofertas
                        SET clasificacion = ?, motivo = ?, requisitos_cumple = ?, 
                            requisitos_verificar = ?, estado = ?
                        WHERE id = ?
                    """, (nueva_clase, nuevo_motivo, nuevo_cumple, nuevo_verif, nuevo_estado, of_dict["id"]))
                    actualizadas += 1
            conn.commit()
        logger.info("Reclasificación de BD completada: %d ofertas actualizadas.", actualizadas)
        return actualizadas



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
        # Mapeo léxico de competencias de Pedro
        self.tech_keywords = {
            "sistemas_redes": [
                "linux", "debian", "ubuntu", "redhat", "centos", "rocky", "windows server",
                "active directory", "ldap", "redes", "lan", "wan", "routing", "switching",
                "vlan", "firewall", "vpn", "tcp/ip", "dns", "dhcp", "cisco", "mikrotik",
                "soporte tecnico", "soporte técnico", "soporte informatico", "soporte informático",
                "helpdesk", "soporte l2", "soporte l3", "soporte a usuarios", "soporte it",
                "it support", "sysadmin", "administrador de sistemas", "asir", "virtualizacion",
                "vmware", "vsphere", "proxmox", "hyper-v", "microinformatica", "microinformática"
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
                "inventario", "compras tecnicas", "compras técnicas", "control de calidad",
                "gestion de calidad", "calidad iso", "iso 9001", "normativa aeronautica",
                "normativa militar", "gestion de material", "gestión de material"
            ],
            "administracion_contabilidad": [
                "administrativo", "administrativa", "administracion", "administración",
                "contable", "contabilidad", "facturacion", "facturación", "asientos contables",
                "conciliacion bancaria", "conciliación bancaria", "gestion de albaranes",
                "gestion documental", "gestión documental", "archivo", "erp", "sap",
                "excel", "backoffice", "back office", "auxiliar administrativo",
                "auxiliar administrativa", "gestion de cobros", "tramitacion", "tramitación"
            ],
            "ciberseguridad": [
                "ciberseguridad", "seguridad informatica", "seguridad de la informacion",
                "incibe", "soc", "siem", "criptografia", "hardening", "iso 27001", "ens"
            ]
        }

        # Profesiones tajantemente excluidas (salud, legal, obra civil, comercial puro, hostelería)
        self.EXCLUDED_PROFESSIONS = [
            r'\bortodonc\w*', r'\bdent\w*', r'\bodont[oó]log\w*', r'\bm[eé]dic\w*', r'\benferm\w*',
            r'\bveterinar\w*', r'\bfarmac[eé]ut\w*', r'\bfisioterap\w*', r'\bpsic[oó]log\w*',
            r'\babogad\w*', r'\bletrad\w*', r'\bjur[ií]dic\w*',
            r'\bviajes?\b', r'\bhotel\w*', r'\bhosteler\w*', r'\bcamarer\w*', r'\bcocin\w*',
            r'\bcrupier\b', r'\bcasino\b', r'\binmobiliar\w*',
            r'\bobra civil\b', r'\bjefe de obra\b', r'\bjefa de obra\b',
            r'\bcomercial\b', r'\bventas?\b', r'\baccount manager\b', r'\bvendedor\w*', r'\bteleoperador\w*'
        ]

        # Titulaciones universitarias e ingenierías excluidas salvo que explícitamente admitan FP / Grado Superior
        self.EXCLUDED_DEGREE_TITLES = [
            r'\bingeniero\b', r'\bingeniera\b', r'\bingenier[íi]a\b',
            r'\barquitecto\b', r'\barquitecta\b',
            r'\bcivil\b', r'\bclimat\w*', r'\bambiental\b', r'\bqu[íi]mic\w*',
            r'\bagr[oó]nom\w*', r'\bagr[ií]col\w*', r'\bge[oó]log\w*'
        ]

        self.FP_ACCEPTED_KEYWORDS = [
            'grado superior', 'ciclo formativo', 'fp ii', 'fp 2', 'fp',
            'formación profesional', 'formacion profesional', 'técnico superior', 'tecnico superior',
            'cfgs', 'asir', 'dam', 'daw', 'o experiencia equivalente'
        ]

        self.MANDATORY_DEGREE_KEYWORDS = [
            r'titulaci[oó]n universitaria\b',
            r'grado universitario\b',
            r'carrera universitaria\b',
            r'licenciatura\b',
            r'estudios universitarios imprescindibles\b',
            r'm[aá]ster universitario\b',
            r'imprescindible grado\b',
            r'imprescindible ingenier[íi]a\b',
            r'imprescindible carrera\b'
        ]

        # Palabras clave en el título que definen los puestos técnicos y operativos de FP Grado Superior
        self.TARGET_TITLE_KEYWORDS = [
            # Sistemas / Redes / Informática
            r'sistemas?', r'redes?', r'sysadmin', r'linux', r'windows', r'soporte', r'helpdesk',
            r'inform[aá]tic\w*', r'asir', r'ciberseguridad', r'seguridad', r'devops', r'cloud',
            r'virtualizaci[oó]n', r'microinform[aá]tic\w*', r'operador', r't[eé]cnic\w*',
            # Aviónica / Electrónica / Hardware / Simulación
            r'avi[oó]nic\w*', r'electr[oó]nic\w*', r'hardware', r'simulador\w*', r'calibraci[oó]n',
            r'instrumentaci[oó]n', r'aeron[aá]utic\w*', r'mantenimiento', r'soldadura', r'defensa',
            # Automatización / Scripting
            r'python', r'automatizaci[oó]n', r'scripting', r'programador\w*', r'desarrollador\w*',
            # Logística técnica / Almacén / Calidad
            r'almac[eé]n', r'log[ií]stic\w*', r'repuestos?', r'stock', r'inventario', r'material',
            # Administración / Gestión documental
            r'administrativ\w*', r'facturaci[oó]n', r'gesti[oó]n documental', r'backoffice', r'archivo', r'tramitaci[oó]n'
        ]

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

    def _es_titulacion_compatible(self, puesto: str, descripcion: str) -> Tuple[bool, str]:
        """
        Garantiza que la oferta sea acorde al nivel de estudios de Pedro (FP Grado Superior).
        Descarta puestos que requieran titulación universitaria/ingeniería superior o profesiones no afines.
        """
        p_lower = puesto.lower()
        d_lower = descripcion.lower()
        texto_completo = f"{p_lower} {d_lower}"

        # 1. Comprobar profesiones completamente ajenas (salud, legal, comercial puro, obra civil)
        for pat in self.EXCLUDED_PROFESSIONS:
            if re.search(pat, p_lower):
                return False, f"Profesión no afín al perfil técnico/ASIR de Pedro ({pat})"

        # 2. Comprobar si explícitamente se acepta o valora FP / Grado Superior
        admite_fp = any(kw in texto_completo for kw in self.FP_ACCEPTED_KEYWORDS)

        # 3. Comprobar titulaciones universitarias / ingenierías en el título
        for pat in self.EXCLUDED_DEGREE_TITLES:
            if re.search(pat, p_lower) and not admite_fp:
                return False, "Puesto de ingeniería/carrera universitaria superior (no especifica FP Grado Superior)"

        # 4. Comprobar requisitos de titulación universitaria obligatoria en la descripción
        if not admite_fp:
            for pat in self.MANDATORY_DEGREE_KEYWORDS:
                if re.search(pat, d_lower):
                    return False, "Exige titulación universitaria / carrera sin contemplar FP Grado Superior"

        # 5. Comprobar coherencia ocupacional en el título del puesto
        tiene_ocupacion_diana = any(re.search(pat, p_lower) for pat in self.TARGET_TITLE_KEYWORDS) or admite_fp
        if not tiene_ocupacion_diana:
            return False, "Puesto no alineado con las áreas técnicas/operativas de FP Grado Superior de Pedro"

        return True, "Compatible con FP Grado Superior"

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

    def _es_idioma_espanol(self, texto: str) -> bool:
        """
        Verifica si la oferta está redactada en español.
        Descarta ofertas redactadas en inglés u otros idiomas extranjeros.
        """
        if not texto:
            return False

        palabras_es = {
            "de", "en", "y", "la", "el", "los", "las", "para", "con", "del", "por",
            "un", "una", "requisitos", "experiencia", "puesto", "empresa", "funciones",
            "conocimientos", "trabajo", "incorporación", "jornada", "contrato",
            "equipo", "nuestro", "nuestra", "buscamos", "ofrecemos", "desarrollo",
            "proyecto", "años", "año", "salario", "soporte", "sistemas", "horario",
            "titulación", "sector", "perfil", "remoto", "teletrabajo", "gestión",
            "técnico", "tecnico", "administrador", "mantenimiento"
        }
        palabras_en = {
            "the", "and", "with", "for", "our", "you", "your", "we", "looking",
            "responsibilities", "requirements", "team", "join", "working", "about",
            "skills", "experience", "building", "role", "help", "opportunity",
            "applicant", "apply", "who", "will", "what", "must", "have", "company"
        }

        tokens = set(re.findall(r'\b[a-záéíóúñ]{2,}\b', texto.lower()))
        coincidencias_es = len(tokens.intersection(palabras_es))
        coincidencias_en = len(tokens.intersection(palabras_en))

        # Si las palabras en inglés superan notablemente a las de español
        if coincidencias_en >= 3 and coincidencias_en > coincidencias_es:
            return False

        # Si hay palabras en español y mínima o ninguna presencia en inglés, es español
        if coincidencias_es >= 1 and coincidencias_en <= 1:
            return True

        return coincidencias_es >= 2

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

        # 0. FILTRO ESTRICTO DE IDIOMA (SOLO OFERTAS EN ESPAÑOL)
        if not self._es_idioma_espanol(f"{puesto} {descripcion}"):
            return {
                "clasificacion": "C",
                "motivo": "Descartada: Oferta redactada en inglés u otro idioma extranjero (filtro: solo ofertas en español).",
                "requisitos_cumple": [],
                "requisitos_verificar": []
            }

        # 1. FILTRO DE TITULACIÓN Y PUESTO ACORDE A GRADO SUPERIOR
        es_titulacion_ok, motivo_titulacion = self._es_titulacion_compatible(puesto, descripcion)
        if not es_titulacion_ok:
            return {
                "clasificacion": "C",
                "motivo": f"Descartada: {motivo_titulacion} (filtro: acorde a FP Grado Superior).",
                "requisitos_cumple": [],
                "requisitos_verificar": []
            }

        # 2. FILTRO ESTRICTO DE MODALIDAD / UBICACIÓN Y HORARIO
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
                elif area == "administracion_contabilidad":
                    puntos_fuertes.add("Administración / Gestión / Contabilidad")
                    cumple.append(f"Gestión administrativa, contable y documental: {', '.join(coincidencias[:4])}")
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


class TecnoempleoConnector:
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


class InfoJobsConnector:
    """Conector para InfoJobs (Albacete, Teletrabajo y RSS de respaldo)."""
    URLS = [
        ("InfoJobs Albacete Sistemas", "https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword=sistemas&provinceIds=3"),
        ("InfoJobs Albacete General", "https://www.infojobs.net/jobsearch/search-results/list.xhtml?provinceIds=3"),
        ("InfoJobs Teletrabajo Sistemas", "https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword=sistemas&teleworkingIds=2"),
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


class LinkedInConnector:
    """Conector para LinkedIn Jobs mediante la API pública guest search."""
    URLS = [
        ("LinkedIn Albacete Sistemas", "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=sistemas&location=Albacete%2C%20Castile-La%20Mancha%2C%20Spain"),
        ("LinkedIn Albacete Soporte", "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=soporte&location=Albacete"),
        ("LinkedIn Albacete Mantenimiento", "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=mantenimiento%20electronico&location=Albacete"),
        ("LinkedIn Teletrabajo Sistemas", "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=administrador%20sistemas&location=Spain&f_WT=2"),
        ("LinkedIn Teletrabajo Sysadmin", "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=sysadmin&location=Spain&f_WT=2"),
        ("LinkedIn España Aviónica", "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=avionica&location=Spain")
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


class IndeedConnector:
    """Conector para Indeed España mediante emulación TLS de navegador (curl_cffi)."""
    URLS = [
        ("Indeed Albacete Sistemas", "https://es.indeed.com/jobs?q=sistemas&l=Albacete"),
        ("Indeed Albacete Soporte", "https://es.indeed.com/jobs?q=soporte+or+redes&l=Albacete"),
        ("Indeed Remoto Sistemas", "https://es.indeed.com/jobs?q=administrador+sistemas&l=remoto"),
        ("Indeed España Aviónica", "https://es.indeed.com/jobs?q=avionica+or+electronica&l=España")
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


class JobTodayConnector:
    """Conector para Job Today (Albacete, Teletrabajo y puestos operativos)."""
    URLS = [
        ("Job Today Albacete", "https://jobtoday.com/es/trabajos-albacete"),
        ("Job Today Teletrabajo", "https://jobtoday.com/es/trabajos-teletrabajo"),
        ("Job Today Sistemas", "https://jobtoday.com/es/trabajos?q=sistemas"),
        ("Job Today Soporte", "https://jobtoday.com/es/trabajos?q=soporte")
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
                        salario = p.get("salary") or "No especificado"

                        ofertas.append({
                            "id": generar_hash(empresa, role, job_url),
                            "puesto": role.strip(),
                            "empresa": empresa.strip(),
                            "ubicacion": ciudad,
                            "modalidad": modalidad,
                            "horario": "No especificado",
                            "salario": str(salario) if salario else "No especificado",
                            "url": job_url,
                            "fuente": "Job Today",
                            "descripcion": limpiar_html(desc),
                            "fecha_publicacion": p.get("createDate", "") or p.get("updateDate", "")
                        })
            except Exception as e:
                logger.warning("Error en %s: %s", nombre, e)

        logger.info("Job Today: %d ofertas recopiladas.", len(ofertas))
        return ofertas


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

    def enviar_mensaje(self, texto_html: str, inline_keyboard: Optional[List[List[Dict[str, str]]]] = None) -> bool:
        if not self.esta_configurado():
            logger.warning("Telegram no está configurado (faltan TELEGRAM_TOKEN o TELEGRAM_CHAT_ID). Mensaje en log:\n%s", texto_html)
            return False

        payload = {
            "chat_id": self.chat_id,
            "text": texto_html,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        if inline_keyboard:
            payload["reply_markup"] = {"inline_keyboard": inline_keyboard}

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
        h = oferta.get('id', '')

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
            f"🆔 <code>Hash: {h}</code>\n"
            f"⚡ <b>Acciones:</b> /interesante_{h[:8]} | /solicitada_{h[:8]} | /descartar_{h[:8]}"
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
        
        # Conectores desacoplados: 5 portales solicitados por Pedro
        self.connectors = [
            TecnoempleoConnector(),
            InfoJobsConnector(),
            LinkedInConnector(),
            IndeedConnector(),
            JobTodayConnector()
        ]

    def ejecutar(self):
        logger.info("=== INICIANDO AGENTE DE BÚSQUEDA DE EMPLEO ===")
        ahora_str = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

        # 0. Asegurar coherencia histórica de la base de datos con los filtros actuales
        self.db.reclasificar_bd(self.matcher)

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

        # 4. Procesar comandos pendientes enviados por el usuario en Telegram
        self.procesar_comandos_telegram()

        # 5. Exportar JSON de ofertas sincronizado para Cloudflare Worker
        self.db.exportar_json()

        logger.info("=== EJECUCIÓN FINALIZADA SATISFACTORIAMENTE ===")

    def procesar_comandos_telegram(self):
        """Lee y responde a los mensajes y comandos enviados al bot en Telegram."""
        if not self.telegram.esta_configurado():
            return

        try:
            url = f"https://api.telegram.org/bot{self.telegram.token}/getUpdates"
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                return

            updates = resp.json().get("result", [])
            if not updates:
                return

            max_update_id = 0
            for u in updates:
                up_id = u.get("update_id", 0)
                if up_id > max_update_id:
                    max_update_id = up_id

                msg = u.get("message", {})
                texto = (msg.get("text") or "").strip().lower()
                chat_id = str(msg.get("chat", {}).get("id", ""))

                if not texto or chat_id != str(self.telegram.chat_id):
                    continue

                logger.info("Comando recibido en Telegram: %s", texto)

                if texto.startswith("/start") or texto.startswith("/ayuda"):
                    respuesta = (
                        "👋 <b>Hola Pedro. Soy tu Agente de Búsqueda de Empleo.</b>\n\n"
                        "Comandos disponibles:\n"
                        "• /ofertas - Explorar todas las ofertas interactivamente (Anterior/Siguiente)\n"
                        "• /resumen - Conteo de ofertas por estado y clase\n"
                        "• /interesantes - Ver tus ofertas guardadas\n"
                        "• /interesante_&lt;hash&gt; - Marcar oferta como interesante\n"
                        "• /solicitada_&lt;hash&gt; - Marcar oferta como solicitada/enviada\n"
                        "• /descartar_&lt;hash&gt; - Descartar oferta\n"
                        "• /buscar - Ejecutar búsqueda inmediata de ofertas"
                    )
                    self.telegram.enviar_mensaje(respuesta)

                elif texto.startswith("/ofertas"):
                    ofertas = self.db.obtener_nuevas_relevantes(horas=720)
                    if not ofertas:
                        self.telegram.enviar_mensaje("⚠️ No se encontraron ofertas activas en la base de datos.")
                    else:
                        of = ofertas[0]
                        total = len(ofertas)
                        h = of['id'][:8]
                        card = self.telegram.formatear_oferta_html(of)
                        keyboard = [
                            [
                                {"text": "⏮️ Inicio", "callback_data": "of_noop"},
                                {"text": f"📄 1 / {total}", "callback_data": "of_noop"},
                                {"text": "Siguiente ➡️" if total > 1 else "Fin ⏭️", "callback_data": "of_1" if total > 1 else "of_noop"}
                            ],
                            [
                                {"text": "🔗 Ver Oferta", "url": of['url']},
                                {"text": "⭐ Interesante", "callback_data": f"fav_{h}"}
                            ]
                        ]
                        self.telegram.enviar_mensaje(card, inline_keyboard=keyboard)

                elif texto.startswith("/resumen"):
                    res = self.db.obtener_resumen()
                    estados = res.get("estados", {})
                    clases = res.get("clases", {})
                    lineas_est = "\n".join([f"  • <b>{k}:</b> {v}" for k, v in estados.items()])
                    lineas_cl = "\n".join([f"  • <b>Clase {k}:</b> {v}" for k, v in clases.items()])
                    respuesta = (
                        f"📊 <b>RESUMEN DE LA BASE DE DATOS</b>\n\n"
                        f"<b>Por Estado:</b>\n{lineas_est}\n\n"
                        f"<b>Por Clasificación:</b>\n{lineas_cl}"
                    )
                    self.telegram.enviar_mensaje(respuesta)

                elif texto.startswith("/interesantes"):
                    lista = self.db.obtener_interesantes(limite=5)
                    if not lista:
                        self.telegram.enviar_mensaje("⭐ No tienes ninguna oferta marcada como <b>INTERESANTE</b> actualmente.")
                    else:
                        bloques = ["⭐ <b>TUS OFERTAS INTERESANTES GUARDADAS:</b>\n"]
                        for of in lista:
                            bloques.append(
                                f"💼 <b>{of['puesto']}</b> ({of['empresa']})\n"
                                f"📍 {of['ubicacion']} | 💰 {of['salario']}\n"
                                f"🔗 <a href='{of['url']}'>Ver Oferta</a>\n"
                                f"🆔 <code>{of['id'][:8]}</code> | /solicitada_{of['id'][:8]} | /descartar_{of['id'][:8]}"
                            )
                        self.telegram.enviar_mensaje("\n\n".join(bloques))

                elif texto.startswith("/interesante_"):
                    h = texto.replace("/interesante_", "").strip()
                    of = self.db.actualizar_estado_oferta(h, "INTERESANTE")
                    if of:
                        self.telegram.enviar_mensaje(f"⭐ Oferta <b>{of['puesto']}</b> ({of['empresa']}) marcada como <b>INTERESANTE</b>.")
                    else:
                        self.telegram.enviar_mensaje(f"⚠️ No se encontró la oferta con hash '{h}'.")

                elif texto.startswith("/solicitada_"):
                    h = texto.replace("/solicitada_", "").strip()
                    of = self.db.actualizar_estado_oferta(h, "SOLICITADA")
                    if of:
                        self.telegram.enviar_mensaje(f"📨 Oferta <b>{of['puesto']}</b> ({of['empresa']}) marcada como <b>SOLICITADA / CV ENVIADO</b>.")
                    else:
                        self.telegram.enviar_mensaje(f"⚠️ No se encontró la oferta con hash '{h}'.")

                elif texto.startswith("/descartar_"):
                    h = texto.replace("/descartar_", "").strip()
                    of = self.db.actualizar_estado_oferta(h, "DESCARTADA")
                    if of:
                        self.telegram.enviar_mensaje(f"🗑️ Oferta <b>{of['puesto']}</b> ({of['empresa']}) <b>DESCARTADA</b>.")
                    else:
                        self.telegram.enviar_mensaje(f"⚠️ No se encontró la oferta con hash '{h}'.")

            # Confirmar lectura a Telegram mediante offset para no reprocesar los mismos mensajes
            if max_update_id > 0:
                requests.get(f"{url}?offset={max_update_id + 1}", timeout=10)

        except Exception as e:
            logger.error("Error al procesar comandos de Telegram: %s", e)


if __name__ == "__main__":
    agent = JobAgent()
    if "--reclasificar" in sys.argv:
        count = agent.db.reclasificar_bd(agent.matcher)
        agent.db.exportar_json()
        print(f"Reclasificación completada: {count} ofertas actualizadas. Archivo ofertas.json sincronizado.")
    else:
        agent.ejecutar()
