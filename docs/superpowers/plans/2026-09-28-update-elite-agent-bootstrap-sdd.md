# Plan de Implementación: Actualización de Elite Agent Bootstrap al Estándar SDD (Spec Kit + Kev)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Actualizar el repositorio `elite-agent-bootstrap-main` al estándar oficial de Spec-Driven Development ([github/spec-kit](https://github.com/github/spec-kit)), integrando soporte para modelos de decisión tipada ([jaredpalmer/kev](https://github.com/jaredpalmer/kev)), la skill nativa `speckit-sdd` para Antigravity y scripts de portabilidad e instalación universal para cualquier ordenador.

**Architecture:** Reestructurar `elite-agent-bootstrap-main` eliminando el esquema legacy `spec_template/` para adoptar la estructura estándar `.specify/` (`memory/constitution-template.md`, `templates/`) y `specs/`. Incorporar la skill global `speckit-sdd`, scripts de instalación desatendida (`install-sdd.bat`, `install-sdd.ps1`) y actualizar el Mega-Prompt `AGENT_BOOTSTRAP.md` y `README.md`. Finalmente, inicializar el entorno en el proyecto actual `SeartchJobs`.

**Tech Stack:** Markdown, Git, PowerShell, Batch Scripting, Antigravity Customization System (Skills/Rules), GitHub Spec Kit standard, Kev/Jev decision model specifications.

**Spec:** [`docs/superpowers/specs/2026-09-28-sdd-workflow-spec-kit-design.md`](file:///c:/Users/pubes/Desktop/Proyectos/SeartchJobs-main/docs/superpowers/specs/2026-09-28-sdd-workflow-spec-kit-design.md)

## Global Constraints
- Todo el contenido generado, documentación, plantillas y comentarios deben ser en **Español**.
- Cumplimiento estricto del estándar de nomenclatura y convenciones de GitHub Spec Kit (`.specify/` y `specs/`).
- Compatibilidad multiplataforma en scripts (Windows nativo con PowerShell y Batch).
- Límite de arnés: `AGENTS.md` no debe exceder las 500 líneas.

## Review Focus
1. **Rutas relativas en Windows:** Asegurar que los scripts de instalación usen variables de entorno dinámicas (`%USERPROFILE%` y `$HOME`) sin rutas absolutas fijas.
2. **Sintaxis de Skill YAML:** Validar el frontmatter YAML de la skill `speckit-sdd` para que Antigravity la cargue sin errores de parsing.
3. **Persistencia de plantillas:** Asegurar que las plantillas en `.specify/templates/` contengan placeholders claros y no rompan la sintaxis Markdown.
4. **Acoplamiento con Kev/Jev:** Verificar que las directrices de clasificación expliquen claramente el uso de la API `/v1/systemone` y el MCP `jev-classifier`.
5. **No rotura de proyectos existentes:** Garantizar que la migración mantenga compatibilidad con proyectos que ya contaban con un `AGENTS.md`.

---

### Task 1: Reestructuración de Plantillas en `elite-agent-bootstrap-main` (`.specify/` y `specs/`)

**Files:**
- Create: `c:/Users/pubes/Desktop/Proyectos/elite-agent-bootstrap-main/.specify/memory/constitution-template.md`
- Create: `c:/Users/pubes/Desktop/Proyectos/elite-agent-bootstrap-main/.specify/templates/spec.md`
- Create: `c:/Users/pubes/Desktop/Proyectos/elite-agent-bootstrap-main/.specify/templates/plan.md`
- Create: `c:/Users/pubes/Desktop/Proyectos/elite-agent-bootstrap-main/.specify/templates/tasks.md`
- Create: `c:/Users/pubes/Desktop/Proyectos/elite-agent-bootstrap-main/specs/001-template-baseline/spec.md`
- Delete: `c:/Users/pubes/Desktop/Proyectos/elite-agent-bootstrap-main/spec_template/`

**Interfaces:**
- Consumes: Convenciones oficiales de `github/spec-kit`.
- Produces: Estructura `.specify/` estándar consumible por cualquier agente o script de copia.

- [ ] **Paso 1.1:** Crear la carpeta `.specify/memory/` y redactar `constitution-template.md` con los 5 principios innegociables (Gobernanza, No Vibe Coding, Calidad/Testing, Decisiones con Kev, Estilo).
- [ ] **Paso 1.2:** Crear la carpeta `.specify/templates/` y redactar las plantillas oficiales `spec.md`, `plan.md` y `tasks.md`.
- [ ] **Paso 1.3:** Crear `specs/001-template-baseline/spec.md` como ejemplo funcional documentado de una característica.
- [ ] **Paso 1.4:** Eliminar el directorio legacy `spec_template/` para evitar duplicidad de estándares.
- [ ] **Paso 1.5:** Verificar la existencia de todos los archivos creados mediante PowerShell.

---

### Task 2: Creación de la Skill Global `speckit-sdd` y Exportable

**Files:**
- Create: `c:/Users/pubes/Desktop/Proyectos/elite-agent-bootstrap-main/skills/speckit-sdd/SKILL.md`
- Create: `C:/Users/pubes/.gemini/config/skills/speckit-sdd/SKILL.md`
- Modify: `C:/Users/pubes/.gemini/config/GEMINI.md`

**Interfaces:**
- Consumes: Antigravity Customization System (frontmatter YAML).
- Produces: Comandos `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, `/speckit.implement`, `/speckit.converge`.

- [ ] **Paso 2.1:** Redactar `SKILL.md` con frontmatter válido (`name: speckit-sdd`, `description`) y el protocolo completo de las 5 fases en `elite-agent-bootstrap-main/skills/speckit-sdd/SKILL.md`.
- [ ] **Paso 2.2:** Instalar la skill en el directorio global de Antigravity `C:\Users\pubes\.gemini\config\skills\speckit-sdd\SKILL.md`.
- [ ] **Paso 2.3:** Configurar la regla global en `C:\Users\pubes\.gemini\config\GEMINI.md` para que active automáticamente la disciplina SDD si detecta `.specify/`.
- [ ] **Paso 2.4:** Verificar que la skill esté disponible en la configuración del agente.

---

### Task 3: Integración del Motor de Decisión Kev / Jev en el Bootstrap

**Files:**
- Create: `c:/Users/pubes/Desktop/Proyectos/elite-agent-bootstrap-main/docs/kev-decision-guide.md`
- Modify: `c:/Users/pubes/Desktop/Proyectos/elite-agent-bootstrap-main/.specify/memory/constitution-template.md`

**Interfaces:**
- Consumes: Contrato API `/v1/systemone` y MCP `jev-classifier`.
- Produces: Guía de integración de modelos de decisión rápida para clasificación y enrutamiento sin coste de LLM.

- [ ] **Paso 3.1:** Crear `docs/kev-decision-guide.md` explicando cómo funciona Kev (`jaredpalmer/kev`), las 3 modalidades de pregunta (`noul` sí/no, `choice` opción múltiple, `score` nivel) y su conexión con el MCP `jev-classifier`.
- [ ] **Paso 3.2:** Integrar en `constitution-template.md` la cláusula de uso preferente de clasificadores tipados para tareas de decisión unitaria.
- [ ] **Paso 3.3:** Verificar coherencia documental.

---

### Task 4: Scripts de Instalación Rápida y Portabilidad Universal

**Files:**
- Create: `c:/Users/pubes/Desktop/Proyectos/elite-agent-bootstrap-main/scripts/install-sdd.bat`
- Create: `c:/Users/pubes/Desktop/Proyectos/elite-agent-bootstrap-main/scripts/install-sdd.ps1`
- Create: `c:/Users/pubes/Desktop/Proyectos/elite-agent-bootstrap-main/scripts/init-project-sdd.bat`

**Interfaces:**
- Consumes: Directorio de usuario `%USERPROFILE%` / `$HOME`.
- Produces: Instalador de un clic para configurar Antigravity en cualquier PC e inicializador para nuevos proyectos.

- [ ] **Paso 4.1:** Crear `install-sdd.ps1` que detecte `~/.gemini/config/`, copie la skill `speckit-sdd`, registre las reglas en `GEMINI.md` y verifique la instalación.
- [ ] **Paso 4.2:** Crear `install-sdd.bat` como lanzador de doble clic en Windows que ejecute el script de PowerShell con bypass de execution policy.
- [ ] **Paso 4.3:** Crear `init-project-sdd.bat` para inyectar la estructura `.specify/` en cualquier carpeta de proyecto con una sola orden.
- [ ] **Paso 4.4:** Probar la ejecución de los scripts en modo dry-run / comprobación de sintaxis.

---

### Task 5: Actualización del Mega-Prompt y README de `elite-agent-bootstrap-main`

**Files:**
- Modify: `c:/Users/pubes/Desktop/Proyectos/elite-agent-bootstrap-main/AGENT_BOOTSTRAP.md`
- Modify: `c:/Users/pubes/Desktop/Proyectos/elite-agent-bootstrap-main/README.md`

**Interfaces:**
- Consumes: Arquitectura completa de Spec Kit, Kev y Antigravity.
- Produces: Documentación maestra actualizada al 100%.

- [ ] **Paso 5.1:** Actualizar `AGENT_BOOTSTRAP.md` sustituyendo el flujo anterior por el estándar oficial Spec Kit (`.specify/`, `specs/`), la integración con Kev y las 5 fases agénticas.
- [ ] **Paso 5.2:** Actualizar `README.md` detallando las nuevas capacidades, los scripts de portabilidad para otros ordenadores y el estándar GitHub Spec Kit.
- [ ] **Paso 5.3:** Validar que ambos archivos estén completamente en español y sin referencias rotas.

---

### Task 6: Despliegue de la Estructura SDD en `SeartchJobs-main`

**Files:**
- Create: `c:/Users/pubes/Desktop/Proyectos/SeartchJobs-main/.specify/memory/constitution.md`
- Create: `c:/Users/pubes/Desktop/Proyectos/SeartchJobs-main/.specify/templates/spec.md`
- Create: `c:/Users/pubes/Desktop/Proyectos/SeartchJobs-main/.specify/templates/plan.md`
- Create: `c:/Users/pubes/Desktop/Proyectos/SeartchJobs-main/.specify/templates/tasks.md`
- Create: `c:/Users/pubes/Desktop/Proyectos/SeartchJobs-main/specs/001-sdd-baseline/spec.md`
- Create: `c:/Users/pubes/Desktop/Proyectos/SeartchJobs-main/AGENTS.md`
- Modify: `c:/Users/pubes/Desktop/Proyectos/SeartchJobs-main/GEMINI.md`

**Interfaces:**
- Consumes: Plantillas generadas en el bootstrap y principios de SeartchJobs.
- Produces: Repositorio `SeartchJobs` 100% gobernado por Spec Kit y Kev.

- [ ] **Paso 6.1:** Crear `.specify/memory/constitution.md` específico para `SeartchJobs` (Coste cero, GitHub Actions, SQLite `data/empleo.db`, Telegram emisor, filtros estrictos de Hellín/Albacete turno tarde o 100% remoto, Kev/Jev para clasificación de ofertas Clase A/B/C).
- [ ] **Paso 6.2:** Desplegar plantillas `.specify/templates/` en `SeartchJobs`.
- [ ] **Paso 6.3:** Crear la línea base documentada en `specs/001-sdd-baseline/spec.md`.
- [ ] **Paso 6.4:** Crear `AGENTS.md` y `GEMINI.md` en la raíz de `SeartchJobs-main`.
- [ ] **Paso 6.5:** Ejecutar suite de pruebas de SeartchJobs (`py -m unittest` o tests existentes) para asegurar integridad.
