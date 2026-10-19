# AGENTS.md - Agente Autónomo de Búsqueda Diaria y Postulación Inteligente (AlertasEmpleo)

Este repositorio opera bajo el estándar oficial de **Spec-Driven Development (GitHub Spec Kit)**, arquitectura de decisiones tipadas y el asistente autónomo de postulación de empleo para **Pedro Úbeda Sánchez**.

**REGLA DE ORO:** Todas las comunicaciones, explicaciones, comentarios, especificaciones y mensajes de commit deben ser obligatoriamente en **ESPAÑOL**.

---

## 🏛️ Constitución y Principios Rectores
- **Archivo rector:** `.specify/memory/constitution.md`
- **Coste Cero:** Arquitectura serverless en GitHub Actions + SQLite (`data/empleo.db`) + Telegram emisor pasivo.
- **Filtros Estrictos Inviolables:**
  - 100% Remoto en España.
  - Presencial o Híbrido: ÚNICAMENTE en Hellín o Albacete capital en turno de tarde o fines de semana.
  - Descarte automático de ofertas incompatibles o turnos de mañana presenciales fuera de zona.
- **Clasificación Tipada:**
  - Clase A: Encaje directo (notificar a Telegram).
  - Clase B: Encaje potencial a validar (notificar con aviso).
  - Clase C: Encaje limitado (persistir en SQLite, PROHIBIDO notificar).

---

## 🎯 Thin-Pointer Design (Fuente Única de Verdad)

Para evitar duplicaciones y divergencias entre diferentes motores de agentes de IA, este repositorio adopta el diseño unificado de puntero único:

1. **Perfil del Candidato:**
   - La formación reglada, trayectoria militar de 22 años, competencias técnicas, proyectos y restricciones se definen en [.agents/skills/job-application-assistant/01-candidate-profile.md](.agents/skills/job-application-assistant/01-candidate-profile.md).
2. **Metodología de Postulación:**
   - El estilo conductual y operativo se especifica en `02-behavioral-profile.md`.
   - La guía de redacción profesional anti-clichés se especifica en `03-writing-style.md`.
   - El sistema de puntuación y descarte estricto se especifica en `04-job-evaluation.md`.
   - Las reglas de confección de CV y cartas se especifican en `05-cv-templates.md` y `06-cover-letter-templates.md`.
   - La preparación de entrevistas y marco STAR se definen en `07-interview-prep.md`.
3. **Flujos de Trabajo y Comandos:**
   - Orquestación en [.agents/skills/](.agents/skills/) y ejecutables directos en `tools/` y `src/gestionar.py`.

---

## 🛠️ Stack Tecnológico y Comandos
- **Entorno:** Python 3.10+
- **Base de Datos:** SQLite (`data/empleo.db`)
- **Ejecutar Pruebas:**
  ```bash
  python -m pytest tests/ -v
  ```
- **Ejecución Local del Pipeline:**
  ```bash
  python src/job_agent.py
  ```
- **CLI de Gestión de Candidaturas:**
  ```bash
  python src/gestionar.py
  ```

---

## 🏗️ Flujo de Trabajo SDD (Comandos de Agente)
- `/speckit.specify <feature>`: Redactar especificación en `specs/NNN-<feature>/spec.md`.
- `/speckit.plan`: Elaborar plan técnico en `plan.md`.
- `/speckit.tasks`: Desglosar tareas atómicas y comandos de test en `tasks.md`.
- `/speckit.implement`: Implementar en TDD paso a paso.
- `/speckit.converge`: Verificación integral de tests y cierre.

