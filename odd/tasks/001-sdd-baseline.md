# Línea Base de SeartchJobs (Ingesta, Filtrado y Telegram)

## Objective and problem
Línea base funcional probada de capacidades de SeartchJobs para la ingesta multi-fuente, filtrado estricto por ubicación/horario, persistencia en SQLite y notificación vía Telegram.

## Scope and constraints
- Rama: main
- Runner de tests: py -m unittest tests/test_agent.py
- Entorno: Python 3.10+, SQLite (data/empleo.db), Telegram Bot API

## Specs
- **S1 (Ingesta Multi-fuente):** Ingesta automática de feeds RSS y scraping de portales de empleo de referencia.
- **S2 (Filtros Estrictos de Ubicación y Horario):** Admisión de ofertas 100% teletrabajo en España; admisión de presenciales/híbridas únicamente en Hellín o Albacete capital en turno de tarde; descarte automático de turnos de mañana o partidos fuera de zona.
- **S3 (Clasificación Tipada A/B/C):** Clase A (encaje directo), Clase B (encaje potencial a validar), Clase C (incompatibles/excluyentes).
- **S4 (Persistencia en SQLite):** Registro idempotente en data/empleo.db y CLI src/gestionar.py.
- **S5 (Notificación por Telegram):** Informe diario formateado y envío por Telegram Bot API.
- **S6 (Orquestación en GitHub Actions):** Cron diario a las 06:00 UTC en .github/workflows/empleo.yml.
- **S7 (Calidad y Coste Cero):** Arquitectura serverless sin coste, manejo resiliente de caídas y suite de tests unitarios verificada.

## Tasks
- [x] T1 (S1-S6): Implementación de pipeline base de ingesta, filtrado, persistencia y notificaciones | Ruta: inline | Commit: baseline-initial
- [x] T2 (S7): Suite de pruebas unitarias (23 tests) en tests/test_agent.py | Ruta: inline | Commit: baseline-tests

## Log
- L1 (2026-09-28): Petición original de formalizar la línea base probada de SeartchJobs.
- L2 (2026-11-04): Migración formal de SDD a ODD (Organic-Driven Development). Verificación de suite de tests ejecutada.
