# Directrices de Antigravity para SeartchJobs (ODD)

- **Estándar:** Organic-Driven Development (ODD) — Gentle Shell / el Gentleman.
- **Metodología ODD:** 
  1. Authorize (solo lectura para análisis; 1 aclaración ante ambigüedad).
  2. Explore (comprender código existente antes de escribir).
  3. Resolve Uncertainty (resolver dudas reales con 1 pregunta concisa).
  4. Classify (Small inline directo vs Large con seguimiento).
  5. Track: Tareas complejas documentadas en `odd/tasks/<feature>.md`.
  6. Implement task-by-task: TDD por defecto, work-unit commits (~400 líneas).
  7. Close: Comprobación de suite de tests y reporte de evidencias.
- **Verificación:** Ejecutar `py -m unittest tests/test_agent.py` tras cualquier modificación.
- **Idioma:** Siempre en Español.
