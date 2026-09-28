# Plan Técnico: [NOMBRE DE LA CARACTERÍSTICA]

- **Especificación asociada:** `specs/{{NNN}}-{{NOMBRE_FEATURE}}/spec.md`
- **Estado:** `PROPOSED` | `ACCEPTED` | `SUPERSEDED`

---

## 1. Visión General de la Arquitectura
Explicación técnica de la solución: cómo encaja en el sistema existente, qué módulos interactúan y qué patrones de diseño se aplican.

```
[Diagrama de flujo o texto explicativo de componentes]
```

---

## 2. Archivos Impactados
Lista exhaustiva de archivos que serán creados, modificados o eliminados:
- **Nuevos:** `ruta/al/nuevo_archivo.py`
- **Modificados:** `ruta/al/archivo_existente.py` (Líneas aproximadas o funciones)
- **Eliminados / Deprecados:** `ruta/al/antiguo.py`

---

## 3. Modelo de Datos y Contratos de Interfaz
- **Esquema de Base de Datos:** (Migraciones, tablas SQLite, índices o cambios de columnas).
- **Contratos de Funciones / APIs:** Firmas exactas de métodos públicos, parámetros y tipos de retorno esperados.
- **Capa de Decisión (si aplica):** Preguntas y contratos para Kev/Jev (`noul`, `choice`, `score`).

---

## 4. Dependencias Nuevas (YAGNI)
- Lista de nuevas librerías indispensables (justificar por qué no se puede resolver con la biblioteca estándar).

---

## 5. Estrategia de Pruebas y Validación
- **Tests Unitarios:** Qué módulos y funciones tendrán pruebas dedicadas en `tests/`.
- **Tests de Integración:** Flujos de extremo a extremo a validar.
- **Comandos de Verificación:** Comandos exactos a ejecutar durante el desarrollo.

---

## 6. Riesgos y Plan de Reversión (Rollback)
- Qué podría fallar en entornos reales y cómo revertir el cambio sin pérdida de datos.
