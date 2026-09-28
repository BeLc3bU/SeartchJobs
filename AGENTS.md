# AGENTS.md - Agente Autónomo de Búsqueda Diaria de Empleo (SeartchJobs)

Este repositorio opera bajo el estándar oficial de **Spec-Driven Development (GitHub Spec Kit)** y arquitectura de decisiones tipadas **Kev**.

**REGLA DE ORO:** Todas las comunicaciones, explicaciones, comentarios, especificaciones y mensajes de commit deben ser obligatoriamente en **ESPAÑOL**.

---

## 🏛️ Constitución del Proyecto
- **Archivo rector:** [`.specify/memory/constitution.md`](file:///c:/Users/pubes/Desktop/Proyectos/SeartchJobs-main/.specify/memory/constitution.md)
- **Coste Cero:** Arquitectura serverless en GitHub Actions (cron 06:00 UTC) + SQLite (`data/empleo.db`) + Telegram emisor pasivo.
- **Filtros Estrictos Inviolables:**
  - 100% Remoto en España.
  - Presencial o Híbrido: ÚNICAMENTE en Hellín o Albacete capital en turno de tarde.
  - Descarte automático de ofertas incompatibles o turnos de mañana presenciales.
- **Clasificación Tipada:**
  - Clase A: Encaje directo (notificar a Telegram).
  - Clase B: Encaje potencial a validar (notificar con aviso).
  - Clase C: Encaje limitado (persistir en SQLite, PROHIBIDO notificar).
- **Cero Vibe Coding:** Ningún cambio en `src/` o `tests/` sin contar con `specs/NNN-<feature>/` aprobada.

---

## 🛠️ Stack Tecnológico y Comandos
- **Entorno:** Python 3.13+
- **Base de Datos:** SQLite (`data/empleo.db`)
- **Ejecutar Pruebas:**
  ```bash
  py -m unittest tests/test_agent.py
  ```
- **Ejecución Local del Pipeline:**
  ```bash
  py src/job_agent.py
  ```
- **CLI de Gestión de Candidaturas:**
  ```bash
  py src/gestionar.py
  ```

---

## 🏗️ Flujo de Trabajo SDD (Comandos de Agente)
- `/speckit.specify <feature>`: Redactar especificación en `specs/NNN-<feature>/spec.md`.
- `/speckit.plan`: Elaborar plan técnico en `plan.md`.
- `/speckit.tasks`: Desglosar tareas atómicas y comandos de test en `tasks.md`.
- `/speckit.implement`: Implementar en TDD paso a paso.
- `/speckit.converge`: Verificación integral de tests y cierre.
