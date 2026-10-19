---
framework_version: 1.0.0
---

# Agent Guidelines: AlertasEmpleo & AI Job Application Assistant

Este espacio de trabajo gestiona la búsqueda activa, clasificación y postulación inteligente de empleo para **Pedro Úbeda Sánchez**.

## Thin-Pointer Design (Fuente Única de Verdad)

Para evitar duplicaciones y divergencias entre diferentes motores de agentes de IA (Google Antigravity, Claude Code, Gemini CLI, Codex, Cursor), este repositorio adopta el diseño unificado de puntero único:

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
