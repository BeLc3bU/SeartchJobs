# Especificación de Característica: Línea Base de SeartchJobs (Lógica de Ingesta, Filtrado y Telegram)

- **Identificador:** `specs/001-sdd-baseline/spec.md`
- **Fecha:** 2026-09-28
- **Autor:** Pedro Úbeda Sánchez
- **Estado:** `IMPLEMENTED`

---

## 1. Contexto y Planteamiento del Problema
`SeartchJobs` cuenta con una arquitectura funcional probada para la búsqueda diaria de empleo. Esta especificación documenta formalmente la línea base de capacidades existentes para someter cualquier evolución futura a la disciplina de Spec-Driven Development (SDD).

---

## 2. Requerimientos Funcionales Implementados (FR)
- **FR-1 (Ingesta Multi-fuente):** Ingesta automática de feeds RSS y scraping de portales de empleo de referencia.
- **FR-2 (Filtros Estrictos de Ubicación y Horario):**
  - Admisión de ofertas 100% teletrabajo en España.
  - Admisión de ofertas presenciales o híbridas únicamente en Hellín o Albacete capital en turno de tarde.
  - Descarte sistemático de turnos de mañana o turnos partidos presenciales fuera del área de compatibilidad.
- **FR-3 (Clasificación Tipada A/B/C):**
  - Clase A: Encaje directo con el perfil multidisciplinar (Sistemas, Redes, Aviónica, Ciberseguridad, Telecomunicaciones, Automatización).
  - Clase B: Encaje potencial con requisitos civiles o certificaciones a validar.
  - Clase C: Ofertas incompatibles o excluyentes.
- **FR-4 (Persistencia en SQLite):**
  - Registro de ofertas procesadas en `data/empleo.db` para garantizar idempotencia y evitar notificaciones repetidas.
  - Gestión de estados de postulación mediante la CLI de gestión (`src/gestionar.py`).
- **FR-5 (Notificación por Telegram):**
  - Generación de informe diario formateado y envío a través de la API de Telegram Bot a los destinatarios autorizados.
- **FR-6 (Orquestación en GitHub Actions):**
  - Ejecución programada mediante cron a las 06:00 UTC en `.github/workflows/empleo.yml` con commit automático de la base de datos persistida.

---

## 3. Requerimientos No Funcionales Cumplidos (NFR)
- **NFR-1 (Coste Cero):** Sin servidores dedicados ni servicios cloud de pago.
- **NFR-2 (Resiliencia):** Manejo robusto de caídas de red o errores HTTP en la ingesta sin detener el pipeline.
- **NFR-3 (Pruebas Automatizadas):** Cobertura de tests unitarios verificada mediante 23 pruebas en `tests/test_agent.py`.

---

## 4. Criterios de Aceptación Verificados
- [x] **AC-1:** La suite `py -m unittest tests/test_agent.py` ejecuta y aprueba los 23 tests sin fallos.
- [x] **AC-2:** La base de datos SQLite preserva la integridad referencial y el historial de ofertas.
- [x] **AC-3:** La constitución `.specify/memory/constitution.md` gobierna todas las reglas del agente.
