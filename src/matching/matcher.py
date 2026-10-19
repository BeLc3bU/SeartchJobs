import re
from typing import Dict, Any, Tuple
from .profile import (
    LOCALIDADES_LOCALES, TECH_KEYWORDS, EXCLUDED_PROFESSIONS,
    EXCLUDED_DEGREE_TITLES, FP_ACCEPTED_KEYWORDS, MANDATORY_DEGREE_KEYWORDS,
    TARGET_TITLE_KEYWORDS, VERIFICAR_KEYWORDS
)

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

    LOCALIDADES_LOCALES = LOCALIDADES_LOCALES

    def __init__(self):
        self.tech_keywords = TECH_KEYWORDS
        self.EXCLUDED_PROFESSIONS = EXCLUDED_PROFESSIONS
        self.EXCLUDED_DEGREE_TITLES = EXCLUDED_DEGREE_TITLES
        self.FP_ACCEPTED_KEYWORDS = FP_ACCEPTED_KEYWORDS
        self.MANDATORY_DEGREE_KEYWORDS = MANDATORY_DEGREE_KEYWORDS
        self.TARGET_TITLE_KEYWORDS = TARGET_TITLE_KEYWORDS
        self.verificar_keywords = VERIFICAR_KEYWORDS

    def _es_titulacion_compatible(self, puesto: str, descripcion: str) -> Tuple[bool, str]:
        p_lower = puesto.lower()
        d_lower = descripcion.lower()
        texto_completo = f"{p_lower} {d_lower}"

        for pat in self.EXCLUDED_PROFESSIONS:
            if re.search(pat, p_lower):
                return False, f"Profesión no afín al perfil técnico/ASIR de Pedro ({pat})"

        admite_fp = any(kw in texto_completo for kw in self.FP_ACCEPTED_KEYWORDS)

        for pat in self.EXCLUDED_DEGREE_TITLES:
            if re.search(pat, p_lower) and not admite_fp:
                return False, "Puesto de ingeniería/carrera universitaria superior (no especifica FP Grado Superior)"

        if not admite_fp:
            for pat in self.MANDATORY_DEGREE_KEYWORDS:
                if re.search(pat, d_lower):
                    return False, "Exige titulación universitaria / carrera sin contemplar FP Grado Superior"

        tiene_ocupacion_diana = any(re.search(pat, p_lower) for pat in self.TARGET_TITLE_KEYWORDS) or admite_fp
        if not tiene_ocupacion_diana:
            return False, "Puesto no alineado con las áreas técnicas/operativas de FP Grado Superior de Pedro"

        return True, "Compatible con FP Grado Superior"

    def _es_remoto_espana(self, texto: str, ubicacion: str, modalidad: str) -> bool:
        t_completo = f"{texto} {ubicacion} {modalidad}".lower()
        
        if "100% presencial" in t_completo or "presencial en madrid" in t_completo or "presencial en barcelona" in t_completo:
            return False

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

    def _es_tiempo_completo(self, texto: str, horario: str) -> Tuple[bool, str]:
        t_completo = f"{texto} {horario}".lower()
        h_lower = (horario or "").lower()

        if any(c in h_lower for c in ["completa", "completo", "full-time", "full time", "40h", "40 horas"]):
            return True, "Horario explícito de tiempo completo / jornada completa (40h)"

        patrones_completo = [
            r'\bjornada completa\b',
            r'\btiempo completo\b',
            r'\bfull[- ]?time\b',
            r'\b40\s*h(?:oras)?(?:/(?:sem|semana))?\b',
            r'\b40\s*horas\s*semanales\b',
            r'\bdedicaci[oó]n exclusiva\b',
            r'\bturno partido\b',
            r'\bjornada partida\b',
            r'\b8\s*horas diarios?\b',
            r'\b8\s*horas al d[íi]a\b'
        ]
        for pat in patrones_completo:
            if re.search(pat, t_completo):
                return True, f"Oferta a tiempo completo / jornada completa detectada ({pat})"

        return False, ""

    def _evaluar_compatibilidad_horaria(self, texto: str, ubicacion: str, modalidad: str, horario: str) -> Tuple[bool, str, bool]:
        t_completo = f"{texto} {ubicacion} {modalidad} {horario}".lower()
        h_lower = (horario or "").lower()

        es_tc, motivo_tc = self._es_tiempo_completo(texto, horario)
        if es_tc:
            return False, motivo_tc, False

        patrones_manana = [
            r'\bturno\s+de\s+mañana\b',
            r'\bturno\s+mañana\b',
            r'\bhorario\s+de\s+mañana\b',
            r'\bsolo\s+mañanas?\b',
            r'\bpor\s+la\s+mañana\b',
            r'\ben\s+las?\s+mañanas?\b',
            r'\bde\s+mañanas?\b',
            r'\bmatinal\b',
            r'\bparcial\s*-\s*mañana\b',
            r'\bintensiva\s*-\s*mañana\b',
            r'\bjornada\s+de\s+mañana\b',
            r'\b0[789]:00\s*(?:a|-)\s*1[345]:00\b'
        ]
        es_manana = any(re.search(pat, t_completo) for pat in patrones_manana) or any(m in h_lower for m in ["mañana", "matinal"])

        patrones_tarde = [
            r'\bturno\s+de\s+tarde\b',
            r'\bturno\s+tarde\b',
            r'\bhorario\s+de\s+tarde\b',
            r'\bpor\s+la\s+tarde\b',
            r'\ben\s+las?\s+tardes?\b',
            r'\bde\s+tardes?\b',
            r'\bvespertino\b',
            r'\bparcial\s*-\s*tarde\b',
            r'\bintensiva\s*-\s*tarde\b',
            r'\bjornada\s+de\s+tarde\b',
            r'\b1[4567]:00\s*(?:a|-)\s*2[0123]:00\b',
            r'\b1[4567]:00\s*a\b'
        ]
        es_turno_tarde = any(re.search(pat, t_completo) for pat in patrones_tarde) or any(t in h_lower for t in ["tarde", "vespertino"])

        patrones_fds = [
            r'\bfin\s+de\s+semana\b',
            r'\bfines\s+de\s+semana\b',
            r'\bs[aá]bados?\s+y\s+domingos?\b',
            r'\bs[aá]bados?\b',
            r'\bdomingos?\b',
            r'\bguardias?\s+de\s+fin\s+de\s+semana\b',
            r'\bweekend\b'
        ]
        es_fin_de_semana = any(re.search(pat, t_completo) for pat in patrones_fds) or "fin de semana" in h_lower

        patrones_parcial = [
            r'\btiempo\s+parcial\b',
            r'\bmedia\s+jornada\b',
            r'\bjornada\s+parcial\b',
            r'\bpart[- ]?time\b',
            r'\bpor\s+horas\b',
            r'\bhoras\s+semanales\b',
            r'\b(?:10|12|15|18|20|24|25|30)\s*h(?:oras)?(?:/(?:sem|semana))?\b',
            r'\bparcial\s*-\s*indiferente\b'
        ]
        es_tiempo_parcial = any(re.search(pat, t_completo) for pat in patrones_parcial) or any(p in h_lower for p in ["parcial", "media jornada", "part-time", "part time", "horas"])

        if es_manana and not (es_turno_tarde or es_fin_de_semana):
            return False, "Turno de mañana incompatible (se exige exclusivamente tardes o fines de semana)", False

        if not (es_turno_tarde or es_fin_de_semana or es_tiempo_parcial):
            return False, "No especifica turno de tarde, fin de semana ni tiempo parcial (descartada para evitar jornada completa ordinaria)", False

        detalles = []
        if es_turno_tarde:
            detalles.append("Turno de tarde")
        if es_fin_de_semana:
            detalles.append("Fin de semana")
        if es_tiempo_parcial:
            detalles.append("Tiempo parcial / media jornada")

        motivo = " + ".join(detalles)
        requiere_verificar = es_tiempo_parcial and not (es_turno_tarde or es_fin_de_semana)
        return True, motivo, requiere_verificar

    def _es_local_tarde(self, texto: str, ubicacion: str, horario: str) -> Tuple[bool, str]:
        t_completo = f"{texto} {ubicacion} {horario}".lower()
        es_local = any(loc in t_completo for loc in self.LOCALIDADES_LOCALES)
        if not es_local:
            return False, "Ubicación presencial fuera de Hellín o Albacete"
        return True, "Presencial/Híbrido en Albacete/Hellín"

    def _es_idioma_espanol(self, texto: str) -> bool:
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

        if coincidencias_en >= 3 and coincidencias_en > coincidencias_es:
            return False

        if coincidencias_es >= 1 and coincidencias_en <= 1:
            return True

        return coincidencias_es >= 2

    def evaluar_oferta(self, oferta: Dict[str, Any]) -> Dict[str, Any]:
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

        # 2. FILTRO ESTRICTO DE MODALIDAD / UBICACIÓN GEOGRÁFICA
        es_remoto = self._es_remoto_espana(texto_analisis, ubicacion, modalidad)
        es_local, motivo_local = self._es_local_tarde(texto_analisis, ubicacion, horario)

        if not es_remoto and not es_local:
            return {
                "clasificacion": "C",
                "motivo": f"Descartada por restricciones de ubicación: {motivo_local}",
                "requisitos_cumple": [],
                "requisitos_verificar": []
            }

        # 3. FILTRO ESTRICTO DE HORARIO (TIEMPO PARCIAL, TARDE Y/O FIN DE SEMANA)
        horario_ok, motivo_horario, verificar_horario = self._evaluar_compatibilidad_horaria(
            texto_analisis, ubicacion, modalidad, horario
        )
        if not horario_ok:
            return {
                "clasificacion": "C",
                "motivo": f"Descartada por restricciones de horario: {motivo_horario}",
                "requisitos_cumple": [],
                "requisitos_verificar": []
            }

        # 4. EVALUACIÓN DE COMPETENCIAS TÉCNICAS Y OPERATIVAS
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

        verificar = []
        for kw, desc in self.verificar_keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', texto_analisis):
                verificar.append(desc)

        if verificar_horario:
            verificar.append("Confirmar con la empresa compatibilidad con tiempo parcial por la tarde o fin de semana")

        if not puntos_fuertes:
            return {
                "clasificacion": "C",
                "motivo": "No presenta afinidad técnica ni operativa suficiente con las áreas de especialización de Pedro.",
                "requisitos_cumple": [],
                "requisitos_verificar": []
            }

        mod_desc = "Teletrabajo 100% compatible" if es_remoto else "Posición local en Hellín/Albacete"
        det_horario = f" Horario: {motivo_horario}." if motivo_horario else ""
        motivo = f"{mod_desc}.{det_horario} Oportunidad sólida en {' + '.join(puntos_fuertes)} donde tu bagaje de 22 años en sistemas críticos y disciplina operativa aporta diferenciación inmediata."

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
