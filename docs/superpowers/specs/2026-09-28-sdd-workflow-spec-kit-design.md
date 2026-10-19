# Especificación de Arquitectura: Flujo de Trabajo SDD (Spec-Driven Development) con GitHub Spec Kit y Kev

- **Fecha:** 2026-09-28
- **Estado:** Propuesto (Aprobado en Brainstorming)
- **Ámbito:** Global (Antigravity IDE) y Local (`SeartchJobs`)
- **Estándar de referencia:** [github/spec-kit](https://github.com/github/spec-kit) & [jaredpalmer/kev](https://github.com/jaredpalmer/kev)

---

## 1. Resumen Ejecutivo y Objetivos

Este documento formaliza la arquitectura del flujo de desarrollo basado en especificaciones (**Spec-Driven Development - SDD**) para el proyecto `SeartchJobs` y como estándar corporativo para cualquier proyecto futuro administrado en Antigravity.

### Metas:
1. **Eliminar el *Vibe Coding*:** Garantizar que ninguna línea de código se escriba o modifique sin una especificación (`spec.md`), un plan técnico (`plan.md`) y una lista de tareas atómicas (`tasks.md`) aprobadas.
2. **Gobernanza Constitucional:** Fijar las reglas y principios innegociables del proyecto en `.specify/memory/constitution.md`.
3. **Estandarización Multi-Proyecto:** Crear una Skill global (`speckit-sdd`), plantillas maestras universales y reglas de comportamiento en `~/.gemini/config/` para inicializar y gobernar cualquier repositorio en segundos.
4. **Integración con Modelos de Decisión (Kev):** Incorporar la arquitectura de decisiones tipadas de Jared Palmer (`jaredpalmer/kev` / System 1 / Jev MCP `/v1/systemone`) para enrutamiento y clasificación ultrarrápida de ofertas de empleo sin incurrir en costes de LLM.

---

## 2. Arquitectura General del Sistema

```
===================================================================================
NIVEL GLOBAL (~/.gemini/config/)
├── skills/
│   └── speckit-sdd/
│       └── SKILL.md                 <- Skill que orquesta las 5 fases de Spec Kit
├── templates/
│   └── sdd-starter/                 <- Paquete universal para nuevos proyectos
│       ├── .specify/
│       │   ├── memory/constitution-template.md
│       │   └── templates/ (spec.md, plan.md, tasks.md)
│       ├── AGENTS.md
│       └── init-sdd.bat             <- Script rápido de inicialización
└── GEMINI.md                        <- Regla global: Forzar SDD si existe .specify/
===================================================================================
CAPA DE DECISIÓN Y CLASIFICACIÓN (Kev / Jev)
├── MCP Server: jev-classifier       <- Integrado en mcp_config.json
└── API Contract: /v1/systemone      <- Clasificación tipada A/B/C y turnos
===================================================================================
NIVEL LOCAL (c:\Users\pubes\Desktop\Proyectos\SeartchJobs-main)
├── .specify/
│   ├── memory/
│   │   └── constitution.md          <- Leyes innegociables de SeartchJobs
│   └── templates/
│       ├── spec.md
│       ├── plan.md
│       └── tasks.md
├── specs/
│   └── 001-sdd-baseline/            <- Especificación de la línea base del repo
│       ├── spec.md
│       ├── plan.md
│       └── tasks.md
├── AGENTS.md                        <- Instrucciones específicas para el agente
└── GEMINI.md                        <- Regla de contexto local
===================================================================================
```

---

## 3. Especificación Detallada de Componentes

### 3.1. Constitución de SeartchJobs (`.specify/memory/constitution.md`)
La Constitución contiene los principios que ninguna modificación de código puede violar:

1. **Principio de Coste Cero y Autonomía:**
   - La orquestación corre exclusivamente en GitHub Actions (`.github/workflows/empleo.yml`) a las 06:00 UTC.
   - Base de datos relacional SQLite ligera persistida en `data/empleo.db` sincronizada mediante `git commit/push`.
   - Canal de Telegram unidireccional pasivo: el bot nunca levanta un servidor webhook continuo; solo emite alertas durante el pipeline.
2. **Principio de Filtros Estrictos de Ubicación y Horario:**
   - **Modalidad 1:** Remoto 100% en territorio español con horario compatible.
   - **Modalidad 2:** Presencial o híbrido restringido a **Hellín** o **Albacete capital**, **exclusivamente en turno de tarde** (descartar mañana o jornada partida).
   - Cualquier oferta fuera de estas condiciones se cataloga como Clase C o se descarta.
3. **Principio de Clasificación Determinista (Kev Integration):**
   - **Clase A:** Encaje directo (perfil técnico + filtros estrictos). Notificación inmediata a Telegram.
   - **Clase B:** Encaje potencial (requiere validar certificaciones o confirmar turno en Albacete/Hellín). Notificación con advertencia.
   - **Clase C:** Encaje limitado. Persistencia obligatoria en SQLite para evitar re-procesamiento, pero **prohibida** su notificación a Telegram.
   - Toda lógica de decisión debe estructurarse para admitir clasificación tipada mediante modelos tipo Kev (`noul` sí/no, `choice` A/B/C, `score`).
4. **Principio de Calidad y Pruebas Obligatorias:**
   - Todo módulo nuevo en `src/` debe contar con cobertura de pruebas unitarias en `tests/`.
   - Compatibilidad estricta con Python 3.13+.

---

### 3.2. Plantillas Oficiales de Spec Kit (`.specify/templates/`)

#### A. `spec.md` (Plantilla de Especificación de Característica)
- **Título & Metadatos:** Identificador único (`NNN-<feature>`), fecha, autor y estado (`DRAFT`, `APPROVED`, `IMPLEMENTED`).
- **Problema & Justificación:** Qué necesidad cubre y qué valor aporta a Pedro Úbeda Sánchez o al sistema.
- **Requerimientos Funcionales (FR):** Lista numerada y detallada de capacidades esperadas.
- **Requerimientos No Funcionales (NFR):** Impacto en rendimiento, memoria, cuotas de API de Telegram, límites de GitHub Actions.
- **Criterios de Aceptación:** Condiciones objetivas y medibles para considerar la especificación completada.

#### B. `plan.md` (Plantilla de Plan Técnico)
- **Visión Arquitectónica:** Diagrama de componentes y flujo de datos.
- **Esquema de Datos:** Alteraciones o nuevas tablas en SQLite (`empleo.db`).
- **Archivos Impactados:** Lista exacta de archivos a crear, editar o eliminar.
- **Integraciones:** Interacción con Kev, Telegram API o parsers RSS/scraping.
- **Riesgos y Estrategia de Rollback:** Qué hacer si falla la ejecución diaria.

#### C. `tasks.md` (Plantilla de Tareas Atómicas)
- **Estructura de Tareas:** Tareas atómicas numeradas (`- [ ] Tarea 1: ...`).
- **Criterio de Terminación:** Qué archivos cambian en cada tarea.
- **Comando de Verificación Obligatorio:** Comando exacto de terminal (`pytest`, script de verificación) que debe ejecutarse y pasar antes de marcar la tarea como completada.

---

### 3.3. Skill Global de Antigravity (`speckit-sdd`)
Ubicación: `C:\Users\pubes\.gemini\config\skills\speckit-sdd\SKILL.md`

Define el protocolo de activación y ejecución de los comandos SDD:
* `/speckit.specify <nombre>`: Valida la idea contra la constitución, crea la carpeta en `specs/` y redacta el `spec.md`.
* `/speckit.plan`: Lee el `spec.md` aprobado y elabora el plan técnico `plan.md`.
* `/speckit.tasks`: Desglosa el plan en tareas atómicas con comandos de prueba en `tasks.md`.
* `/speckit.implement`: Ejecuta las tareas paso a paso, aplicando TDD y verificando cada paso.
* `/speckit.converge`: Ejecuta la suite de verificación completa, linters y prepara la documentación final.

---

### 3.4. Inicializador Universal para Otros Proyectos (`sdd-starter`)
Ubicación: `C:\Users\pubes\.gemini\config\templates\sdd-starter\`

Permite que cualquier otro proyecto adopte SDD en un solo paso:
- Contiene una estructura `.specify/` preconfigurada con plantillas universales y un script PowerShell/Batch `init-sdd.bat`.
- Al ejecutarse en un repositorio nuevo, crea `.specify/`, `specs/`, y genera un borrador de `constitution.md` entrevistando al usuario.

---

## 4. Estrategia de Verificación y Testing

1. **Verificación de Estructura:** Confirmar la existencia y formato válido de todos los directorios (`.specify`, `specs`) y archivos Markdown.
2. **Validación de la Skill Global:** Verificar que Antigravity detecte y registre la skill `speckit-sdd` en su catálogo.
3. **Validación del MCP Kev/Jev:** Verificar que las directrices en la constitución y especificaciones se acoplen a las herramientas MCP existentes (`jev_status`, `jev_choose_next_tool`).
4. **Verificación del Baseline:** Asegurar que `specs/001-sdd-baseline/` describa con total exactitud la funcionalidad actual de `SeartchJobs` y pase los tests existentes con `pytest`.

---

## 5. Matriz de Entregables

| Ámbito | Ruta | Descripción |
| :--- | :--- | :--- |
| **Global** | `C:\Users\pubes\.gemini\config\skills\speckit-sdd\SKILL.md` | Skill nativa SDD |
| **Global** | `C:\Users\pubes\.gemini\config\templates\sdd-starter\` | Plantilla y script de inicialización universal |
| **Global** | `C:\Users\pubes\.gemini\config\GEMINI.md` | Regla global para agentes |
| **Local** | `c:\Users\pubes\Desktop\Proyectos\SeartchJobs-main\.specify\memory\constitution.md` | Constitución de SeartchJobs |
| **Local** | `c:\Users\pubes\Desktop\Proyectos\SeartchJobs-main\.specify\templates\` | Plantillas `spec.md`, `plan.md`, `tasks.md` |
| **Local** | `c:\Users\pubes\Desktop\Proyectos\SeartchJobs-main\specs\001-sdd-baseline\` | Línea base documentada del proyecto |
| **Local** | `c:\Users\pubes\Desktop\Proyectos\SeartchJobs-main\AGENTS.md` | Guía de agentes en el repositorio |
