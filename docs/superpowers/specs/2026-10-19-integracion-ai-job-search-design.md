# 📐 Especificación de Diseño: Refactorización Modular e Integración de AI Job Search en AlertasEmpleo

**Fecha:** 2026-10-19  
**Estado:** Aprobado en diseño colaborativo  
**Autor:** Antigravity & Pedro Úbeda Sánchez  
**Proyecto:** AlertasEmpleo (`c:\Proyectos\AlertasEmpleo`)  
**Repositorio de Referencia:** [MadsLorentzen/ai-job-search](https://github.com/MadsLorentzen/ai-job-search)

---

## 1. Resumen Ejecutivo y Objetivos

El objetivo de esta especificación es transformar **AlertasEmpleo** (actualmente un buscador y clasificador diario de empleo monolítico en Python) en una **suite integral de postulación inteligente y autónoma**, adoptando la arquitectura, metodologías y flujos del framework [MadsLorentzen/ai-job-search](https://github.com/MadsLorentzen/ai-job-search), adaptados específicamente al perfil profesional de **Pedro Úbeda Sánchez**.

### Objetivos Clave:
1. **Refactorización Limpia:** Descomponer el monolito `src/job_agent.py` (1.775 líneas, ~87 KB) en una arquitectura modular desacoplada (`src/core/`, `src/db/`, `src/matching/`, `src/connectors/`, `src/notifiers/`), manteniendo un wrapper de retrocompatibilidad y asegurando que el 100% de los tests unitarios existentes continúen pasando.
2. **Base de Conocimiento de Candidato:** Crear el perfil estructurado de Pedro en `.agents/skills/job-application-assistant/` y `AGENTS.md` (perfil profesional, perfil conductual, directrices de redacción anti-clichés de IA y matriz de evaluación con filtros estrictos de ubicación y turno).
3. **Pipeline de Postulación Drafter-Reviewer (`/apply`):** Implementar la generación de CV a medida y Carta de Presentación personalizada con gate de seguridad determinista contra *prompt injection*, revisión crítica y plantillas en Markdown/HTML y LaTeX.
4. **Ciclo de Vida de Postulaciones:** Integrar herramientas para preparación de entrevistas (`/interview`), registro de estados y archivo (`/outcome`), análisis de brechas formativas (`/upskill`) y cuadro de mando visual (`/html-report`).
5. **Puente Operativo:** Conectar la base de datos `data/empleo.db` y el CLI `src/gestionar.py` para permitir la postulación inmediata a partir de cualquier oferta de Clase A o B guardada por el agente diario.

---

## 2. Arquitectura del Sistema Refactorizado

```mermaid
flowchart TD
    subgraph Ingestion["Capa de Ingesta (src/connectors/)"]
        C1[TecnoempleoConnector]
        C2[InfoJobsConnector]
        C3[LinkedInConnector]
        C4[IndeedConnector]
        C5[JobTodayConnector]
    end

    subgraph CoreEngine["Motor de Clasificación y Estado (src/)"]
        M[ProfileMatcher<br/>src/matching/]
        DB[(SQLite data/empleo.db<br/>src/db/)]
        Agent[JobAgent<br/>src/core/]
    end

    subgraph Distribution["Notificación y Gestión"]
        TG[TelegramDispatcher<br/>src/notifiers/]
        CLI[gestionar.py CLI]
    end

    subgraph AIAssistant["Suite de Postulación (tools/ & .agents/)"]
        Apply[Pipeline /apply<br/>Drafter + Reviewer]
        Interview[/interview Prep Pack]
        Outcome[/outcome Tracker & Archive]
        Upskill[/upskill Gap Analysis]
        Report[/html-report Dashboard]
    end

    C1 & C2 & C3 & C4 & C5 --> Agent
    Agent --> M
    M --> DB
    Agent --> TG
    DB --> CLI
    CLI --> Apply
    DB --> Apply
    Apply --> Outcome
    Outcome --> Report
    DB --> Upskill
```

### Estructura de Directorios Resultante

```text
AlertasEmpleo/
├── .agents/
│   ├── AGENTS.md                                   # Puntero único y reglas generales de agentes
│   └── skills/
│       ├── job-application-assistant/              # Metodología y perfil de Pedro Úbeda
│       │   ├── SKILL.md
│       │   ├── 01-candidate-profile.md             # Perfil técnico detallado
│       │   ├── 02-behavioral-profile.md            # Perfil conductual y resiliencia
│       │   ├── 03-writing-style.md                 # Tono sobrio, métricas STAR
│       │   ├── 04-job-evaluation.md                # Criterios de evaluación y veto
│       │   ├── 05-cv-templates.md                  # Reglas de tailoring para CV
│       │   ├── 06-cover-letter-templates.md        # Estructura de cartas de presentación
│       │   └── 07-interview-prep.md                # Dossier y simulación de entrevista
│       ├── job-pipeline/                           # Orquestación de postulación (/apply, /outcome, /interview)
│       │   └── SKILL.md
│       └── upskill/                                # Análisis de brechas formativas
│           └── SKILL.md
├── src/
│   ├── __init__.py
│   ├── job_agent.py                                # Wrapper para retrocompatibilidad total
│   ├── gestionar.py                                # CLI enriquecido con comandos apply y report
│   ├── bot_listener.py                             # Listener interactivo de Telegram
│   ├── test_telegram.py                            # Verificación de conexión
│   ├── core/
│   │   ├── __init__.py
│   │   └── agent.py                                # Pipeline principal JobAgent
│   ├── db/
│   │   ├── __init__.py
│   │   └── manager.py                              # DatabaseManager (SQLite, consultas, purgas)
│   ├── matching/
│   │   ├── __init__.py
│   │   ├── normalizer.py                           # Limpieza de HTML, hashes y salarios
│   │   ├── profile.py                              # Perfil de búsqueda, palabras clave, dealbreakers
│   │   └── matcher.py                              # ProfileMatcher (evaluación Clase A, B, C)
│   ├── connectors/
│   │   ├── __init__.py
│   │   ├── base.py                                 # BaseConnector, proxies y requests seguros
│   │   ├── tecnoempleo.py                          # TecnoempleoConnector
│   │   ├── infojobs.py                             # InfoJobsConnector
│   │   ├── linkedin.py                             # LinkedInConnector
│   │   ├── indeed.py                               # IndeedConnector
│   │   └── jobtoday.py                             # JobTodayConnector
│   └── notifiers/
│       ├── __init__.py
│       └── telegram.py                             # TelegramDispatcher (HTML y teclados)
├── tools/                                          # Herramientas del pipeline de IA
│   ├── security.py                                 # Sanitización determinista anti-injection
│   ├── apply_pipeline.py                           # Generador de CV y Carta de Presentación
│   ├── interview_prep.py                           # Generador de dossier de entrevista
│   ├── upskill_analyzer.py                         # Analizador de brechas en ofertas
│   └── html_reporter.py                            # Generador del dashboard HTML offline
├── cv/                                             # Plantillas y CV maestro
│   ├── cv_pedro_template.md                        # Plantilla base editable en Markdown
│   └── cv_modern.tex                               # Plantilla LaTeX opcional
├── cover_letters/                                  # Plantillas de carta de presentación
│   ├── cover_template.md                           # Plantilla base en Markdown
│   └── cover.cls                                   # Clase LaTeX opcional
├── documents/                                      # Archivo de aplicaciones y evidencias
│   └── applications/                               # Histórico por empresa_puesto/
├── data/
│   └── empleo.db                                   # SQLite persistida
├── tests/
│   ├── test_agent.py                               # Tests originales de regresión (23 tests)
│   ├── test_db.py                                  # Tests unitarios de base de datos
│   ├── test_matcher.py                             # Tests unitarios de lógica de filtrado
│   └── test_tools.py                               # Tests unitarios de herramientas de postulación
└── docs/
    └── superpowers/specs/                          # Especificaciones y planes
```

---

## 3. Especificación Detallada de Componentes

### 3.1 Refactorización de Código Python (`src/`)

- **Contrato Inmutable:** La firma de `JobAgent`, `DatabaseManager`, `ProfileMatcher` y `TelegramDispatcher` se mantiene exactamente igual para que los tests en `tests/test_agent.py` sigan pasando sin modificaciones o mediante imports limpios en `src/job_agent.py`.
- **`src/connectors/base.py`:**
  - Encapsula el User-Agent estándar, la integración con Cloudflare Worker proxy (`CF_WORKER_PROXY`) y el fallback opcional a `curl_cffi` para evadir bloqueos antibot.
  - Métodos abstractos `obtener_ofertas()` y control de errores por portal para que el fallo de una fuente no detenga el pipeline global.
- **`src/db/manager.py`:**
  - Extrae la conexión y migraciones de SQLite.
  - Asegura la columna `descripcion` y añade campos opcionales para seguimiento (`cv_generado`, `carta_generada`).

### 3.2 Base de Conocimiento de Pedro Úbeda Sánchez

En `.agents/skills/job-application-assistant/`:
- **`01-candidate-profile.md`**:
  - Trayectoria: Cabo Primero del Ejército del Aire y del Espacio (22 años de servicio en aviónica y simuladores C-101 y Pilatus).
  - Titulación: Grado Superior ASIR (Administración de Sistemas Informáticos en Red), Técnico Especialista en Informática de Gestión.
  - Certificaciones: Ciberseguridad (INCIBE), NATO HPS CRYPTO, condecoraciones al mérito y constancia.
  - Habilidades técnicas: Linux, Windows Server, Active Directory, Redes LAN/WAN, routing/switching, virtualización (VMware, Proxmox), soporte L2/L3, Python, JavaScript, TypeScript, SQLite, Bash, Git.
  - Logística y calidad: Almacén técnico aeronáutico, control de repuestos, gestión procedimental rigurosa.
- **`02-behavioral-profile.md`**:
  - Orientación a la misión, resiliencia bajo presión en entornos de seguridad crítica, alta disciplina procedimental y ética de trabajo.
- **`03-writing-style.md`**:
  - Redacción profesional, concisa, sin adjetivos grandilocuentes ni clichés de IA ("apasionado por...", "proactivo y dinámico"). Enfoque centrado en hechos demostrables y métricas de impacto (método STAR).
- **`04-job-evaluation.md`**:
  - **Filtros Innegociables (Dealbreakers):**
    1. Remoto 100% España (con horario flexible o compatible).
    2. Presencial o híbrido: Exclusivamente en **Hellín** o **Albacete capital** en **turno de tarde** o compatible.
    3. Exclusión terminante: Jornada partida clásica o turnos de mañana fijos en modalidad presencial.

### 3.3 Pipeline de Postulación Inteligente (`tools/`)

1. **`tools/security.py`**:
   - Escaneo de la descripción del puesto en busca de caracteres invisibles, directivas de inyección (`ignore previous instructions`, `system prompt`, `DAN`, etc.) y bloques sospechosos.
   - Emite dictamen de seguridad antes de permitir el procesamiento por el modelo.
2. **`tools/apply_pipeline.py`**:
   - Recibe una oferta (por URL o por ID de SQLite).
   - Extrae el texto y requisitos clave.
   - Genera el borrador del **CV adaptado** (seleccionando las viñetas y tecnologías del perfil de Pedro más afines al puesto sin alterar fechas ni inventar datos).
   - Genera la **Carta de Presentación** personalizada (máximo 1 página, explicando el valor diferencial que aporta la experiencia militar-técnica para el puesto civil/remoto).
   - Agente Revisor interno: valida que el texto no contenga alucinaciones, respete el formato ATS y cumpla el estilo de Pedro.
   - Exporta los archivos a `documents/applications/<empresa>_<puesto>/` en formatos Markdown y HTML listos para imprimir a PDF.
3. **`tools/interview_prep.py`**:
   - Genera un documento con las 10 preguntas técnicas y situacionales más probables para esa oferta.
   - Vincula cada pregunta a una experiencia real de Pedro explicada en formato STAR (Situación, Tarea, Acción, Resultado).
   - Incluye preguntas estratégicas que Pedro puede formular al entrevistador al final de la reunión.
4. **`tools/upskill_analyzer.py`**:
   - Consulta las ofertas registradas en `data/empleo.db` (especialmente Clase B o descartadas).
   - Extrae las palabras clave tecnológicas más demandadas que Pedro aún no domina en profundidad (ej. certificaciones cloud AWS/Azure, Kubernetes, etc.) y genera un plan de estudio sugerido.
5. **`tools/html_reporter.py`**:
   - Lee `data/empleo.db` y genera `documents/reporte_empleo.html`.
   - Incluye tarjetas con el total de ofertas procesadas, activas, solicitadas y descartadas, gráficos SVG de desglose por fuente/portal y distribución por clases (A, B, C).

---

## 4. Estrategia de Pruebas y Validación

1. **Pruebas de Regresión:**
   - Ejecución de `python -m pytest tests/test_agent.py` para asegurar que las 23 pruebas actuales sigan pasando al 100%.
2. **Nuevas Pruebas Unitarias:**
   - `tests/test_db.py`: Verificación de aislamiento en base de datos SQLite y purgas.
   - `tests/test_matcher.py`: Comprobación de que la lógica de filtrado de ubicación y turnos no sufra ninguna alteración.
   - `tests/test_tools.py`: Verificación del sanitizer de seguridad y de los generadores de CV y carta.
3. **Prueba End-to-End:**
   - Ejecución simulada de ingesta y generación de un paquete de postulación de prueba en `documents/applications/test_empresa_puesto/`.

---

## 5. Criterios de Aprobación y Traspaso a Implementación

Una vez aprobado este documento:
1. Se invocará la habilidad **writing-plans** para generar el plan de tareas paso a paso (`plan.md`).
2. Se procederá a la implementación por fases guiadas por pruebas (TDD) sin romper la estabilidad del repositorio.
