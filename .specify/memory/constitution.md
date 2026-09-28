# Constitución del Proyecto: SeartchJobs (Agente Autónomo de Empleo)

> **Candidato:** Pedro Úbeda Sánchez  
> **Estándar:** GitHub Spec Kit (SDD) & Kev Decision Architecture  
> **Estado:** Vigente y de Obligado Cumplimiento  
> **Versión:** 1.0.0  

---

## 🏛️ 1. Misión y Propósito Central
`SeartchJobs` es un sistema autónomo, de coste cero y alta precisión, diseñado para rastrear, filtrar, clasificar y notificar diariamente oportunidades de empleo adaptadas al perfil técnico, operativo y administrativo multidisciplinar de **Pedro Úbeda Sánchez** (Sistemas/Redes, Aviónica, Telecomunicaciones, Ciberseguridad, Automatización y Logística).

---

## 📜 2. Principios Innegociables (Reglas de Oro)

### 2.1. Arquitectura de Coste Cero y Autonomía
1. **GitHub Actions como Orquestador:** La ejecución se realiza mediante cron automático diario (06:00 UTC) en `.github/workflows/empleo.yml`. No se permite añadir infraestructura que requiera servidores 24/7 de pago.
2. **Persistencia Ligera en SQLite:** Los datos se almacenan en `data/empleo.db` y se versionan vía `git commit` y `git push` desde el flujo de Actions.
3. **Telegram como Emisor Unidireccional Pasivo:** El bot no opera servidores HTTP continuos; solo emite el resumen de alertas al chat configurado (`TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`).

### 2.2. Filtros Estrictos de Ubicación y Horario (Inviolables)
El motor de filtrado debe descartar de inmediato cualquier oferta que no cumpla una de estas dos condiciones:
1. **Modalidad 1 (Prioridad Máxima):** **Teletrabajo / Remoto 100%** desde España con flexibilidad horaria.
2. **Modalidad 2 (Presencial o Híbrido Local):** Exclusivamente en **Hellín** o **Albacete capital**, y **OBLIGATORIAMENTE en turno de tarde** o compatible (descartando turnos de mañana o jornada partida presencial clásica).
3. **Descarte Automático:** Cualquier oferta presencial fuera de Albacete/Hellín o con jornada de mañana/partida incompatible debe catalogarse como Clase C o descartarse.

### 2.3. Clasificación de Ofertas y Capa de Decisión (Kev / Jev)
* **🟢 Clase A (Encaje directo):** Requisitos técnicos y operativos alineados con el perfil + cumplimiento estricto de ubicación/horario. **Se notifica a Telegram**.
* **🟡 Clase B (Encaje potencial):** Alta compatibilidad técnica pero con algún requisito civil o turno a validar. **Se notifica con aviso de validación**.
* **⚪ Clase C (Encaje limitado):** Tecnologías excluyentes o desajuste geográfico/horario. **Se almacena en SQLite para evitar duplicados pero NUNCA se envía a Telegram**.
* **Integración Kev:** Las evaluaciones de encaje y turnos deben basarse en decisiones tipadas (`noul` sí/no, `choice` A/B/C) evaluables mediante el motor de decisión Kev (`jaredpalmer/kev` / `/v1/systemone` o MCP `jev-classifier`).

### 2.4. Prohibición Absoluta de "Vibe Coding"
1. **Ningún cambio en `src/` o `tests/` sin especificación:** Todo desarrollo debe contar con una carpeta `specs/NNN-<feature>/` aprobada que contenga:
   - `spec.md` (Requisitos y Criterios de Aceptación).
   - `plan.md` (Diseño técnico, dependencias y riesgos).
   - `tasks.md` (Tareas atómicas con comandos de prueba).
2. **Ciclo TDD:** Cada nueva funcionalidad o corrección debe acompañarse de su test unitario en `tests/`. La suite completa de tests (actualmente 23 tests en `tests/test_agent.py`) debe pasar al 100% en verde antes de cualquier merge o commit de cierre.

### 2.5. Idioma y Formato Oficial
* Todas las respuestas del agente, comentarios en el código, documentación, mensajes de commit y especificaciones deben redactarse obligatoriamente en **Español**.

---

## 🛠️ 3. Stack Tecnológico
- **Lenguaje:** Python 3.13+
- **Base de Datos:** SQLite 3 (`data/empleo.db`)
- **Dependencias Principales:** `requests`, `feedparser`, `beautifulsoup4`
- **Testing:** `unittest` / `pytest`
- **Integraciones:** Telegram Bot API, GitHub Actions, Context7 MCP, jev-classifier MCP
