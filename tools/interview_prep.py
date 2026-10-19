import os
from typing import Dict, Any, Optional, Union
from src.db.manager import DatabaseManager

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def generar_dossier_entrevista(
    oferta_or_id: Union[str, Dict[str, Any]],
    output_file: Optional[str] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Genera un dossier exhaustivo de preparación de entrevista para Pedro Úbeda Sánchez.
    """
    if isinstance(oferta_or_id, dict):
        oferta = oferta_or_id
    else:
        db = DatabaseManager(db_path=db_path) if db_path else DatabaseManager()
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ofertas WHERE id LIKE ? LIMIT 1", (f"{oferta_or_id}%",))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"No se encontró la oferta '{oferta_or_id}'.")
            oferta = dict(row)

    empresa = oferta.get("empresa", "Empresa Objetivo")
    puesto = oferta.get("puesto", "Puesto Técnico")
    descripcion = oferta.get("descripcion", "")

    dossier = f"""# Dossier de Preparación de Entrevista: {puesto} en {empresa}
**Candidato:** Pedro Úbeda Sánchez  
**Perfil:** Aviónica, Sistemas Críticos y ASIR (22 años en el Ejército del Aire y del Espacio)

---

## 🎯 1. Análisis del Rol y Objetivos de la Empresa
- **Puesto:** {puesto}
- **Empresa:** {empresa}
- **Contexto Operativo:** La empresa busca una persona de máxima fiabilidad técnica para gestionar {puesto}.
- **Puntos Fuertes Diferenciales de Pedro:** Disciplina militar procedimental (cero fallos), veteranía en sistemas críticos de vuelo y simuladores, titulación superior ASIR y versatilidad técnica.

---

## 🧭 2. Preguntas Clave y Marco de Respuesta STAR

### Pregunta 1: "¿Por qué decides dar el paso del Ejército al sector civil / teletrabajo?"
- **Situación:** He dedicado 22 años de servicio continuo en el Ejército del Aire manteniendo aviónica y sistemas de vuelo críticos.
- **Tarea:** Tras completar mi Grado Superior en ASIR, formación en INCIBE y certificaciones NATO, he alcanzado el momento idóneo para canalizar toda esta experiencia técnica y procedimental hacia el ámbito civil.
- **Acción:** Aporto madurez, ética de trabajo estricta y habilidad contrastada para operar bajo presión en proyectos tecnológicos de alta exigencia.
- **Resultado:** Integración inmediata, nula rotación y total alineamiento con los objetivos de calidad del equipo.

### Pregunta 2: "¿Cómo manejas una avería crítica imprevista en un servidor o sistema operativo?"
- **Situación:** En sistemas de simuladores y aviónica (C-101 / Pilatus), las averías intermitentes pueden paralizar operaciones críticas.
- **Tarea:** Aislar la causa raíz sin comprometer la seguridad ni alterar configuraciones no verificadas.
- **Acción:** Empleo estricto de checklists y metodologías de diagnóstico por aislamiento (logs, instrumentación de red, análisis de interfaces).
- **Resultado:** Resolución sistemática y documentación de la incidencia para evitar su repetición futura.

### Pregunta 3: "¿Qué experiencia tienes en Linux, Redes y Automatización?"
- **Situación:** Administración de redes en entornos de control y titulación ASIR.
- **Tarea:** Despliegue y mantenimiento de infraestructuras Linux (Debian, Ubuntu, RHEL), VLANs y políticas de seguridad perimetral.
- **Acción:** Automatización de copias de seguridad, comprobaciones de estado y parseo de datos mediante scripts en Python y Bash.
- **Resultado:** Aumento de la resiliencia de los sistemas y minimización de tareas manuales repetitivas.

---

## ❓ 3. Preguntas Estratégicas para el Entrevistador
1. *"¿Cuáles son los principales cuellos de botella técnicos o retos que enfrenta el equipo en este momento?"*
2. *"¿Qué metodologías o estándares de calidad y documentación siguen en la gestión diaria de incidencias?"*
3. *"¿Qué definiría el éxito para esta posición durante los primeros 90 días?"*

---
*Dossier generado automáticamente por el Framework de Postulación Inteligente AlertasEmpleo.*
"""

    if not output_file:
        output_file = os.path.join(REPO_ROOT, "documents", f"interview_{empresa.replace(' ', '_')}_{puesto.replace(' ', '_')}.md")

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(dossier)

    return {
        "exito": True,
        "output_file": output_file,
        "empresa": empresa,
        "puesto": puesto
    }
