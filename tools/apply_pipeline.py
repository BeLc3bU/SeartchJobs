import os
import re
import html
import unicodedata
from datetime import datetime
from typing import Dict, Any, Optional, Union

from .security import sanitize_posting
from src.db.manager import DatabaseManager

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CV_TEMPLATE_PATH = os.path.join(REPO_ROOT, "cv", "cv_pedro_template.md")
COVER_TEMPLATE_PATH = os.path.join(REPO_ROOT, "cover_letters", "cover_template.md")
DEFAULT_APPLICATIONS_DIR = os.path.join(REPO_ROOT, "documents", "applications")

MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}

def slugify(text: str) -> str:
    # Normalizar acentos y diacríticos (á -> a, ñ -> n, etc.)
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = text.lower().strip()
    text = re.sub(r'[\s_]+', '_', text)
    text = re.sub(r'[^a-z0-9_]', '', text)
    return text[:40] or "puesto"

class JobApplicationDrafter:
    """
    Pipeline de generación asistida de candidaturas (CV quirúrgico y Carta de Presentación).
    Aplica el flujo Drafter-Reviewer y genera salidas en Markdown y HTML imprimible.
    """
    def __init__(self, db_path: Optional[str] = None):
        self.db = DatabaseManager(db_path=db_path) if db_path else DatabaseManager()

    def _cargar_oferta(self, oferta_or_id: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        if isinstance(oferta_or_id, dict):
            return oferta_or_id
        
        oferta = self.db.obtener_oferta(oferta_or_id)
        if oferta:
            return oferta
        
        raise ValueError(f"No se encontró ninguna oferta con identificador '{oferta_or_id}'.")

    def generar_postulacion(
        self,
        oferta_or_id: Union[str, Dict[str, Any]],
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        oferta = self._cargar_oferta(oferta_or_id)

        puesto = oferta.get("puesto", "Puesto Técnico").strip()
        empresa = oferta.get("empresa", "Empresa Confidencial").strip()
        descripcion = oferta.get("descripcion", "")
        ubicacion = oferta.get("ubicacion", "España")
        of_id = oferta.get("id", "generada")[:8]

        # 1. Sanitización de seguridad contra Prompt Injections y zero-width chars
        sec_res = sanitize_posting(f"{puesto} {descripcion}")
        clean_desc = sec_res["clean_text"]
        threats = sec_res["threats"]

        # 2. Análisis de palabras clave para tailoring
        desc_lower = clean_desc.lower()
        skills_destacadas = []
        if any(k in desc_lower for k in ["linux", "debian", "ubuntu", "redhat", "centos"]):
            skills_destacadas.append("Administración avanzada de servidores Linux (Debian/Ubuntu/RHEL)")
        if any(k in desc_lower for k in ["redes", "lan", "wan", "cisco", "routing", "switching", "vlan"]):
            skills_destacadas.append("Infraestructura de red, routing/switching, VLANs y seguridad perimetral")
        if any(k in desc_lower for k in ["proxmox", "vmware", "vsphere", "virtualizacion"]):
            skills_destacadas.append("Virtualización y alta disponibilidad con Proxmox VE y VMware vSphere")
        if any(k in desc_lower for k in ["python", "bash", "scripting", "automatizacion"]):
            skills_destacadas.append("Automatización de tareas y desarrollo de scripts en Python y Bash")
        if any(k in desc_lower for k in ["avionica", "simulador", "hardware", "calibracion", "electronica"]):
            skills_destacadas.append("Diagnóstico, calibración y banco de pruebas de aviónica y simuladores críticos")
        if any(k in desc_lower for k in ["ciberseguridad", "seguridad", "incibe", "soc"]):
            skills_destacadas.append("Seguridad de sistemas e infraestructuras críticas (INCIBE y NATO CRYPTO)")

        if not skills_destacadas:
            skills_destacadas.append("Administración de sistemas informáticos en red (ASIR) y soporte técnico especializado L2/L3")

        # 3. Leer y adaptar la plantilla del CV
        if os.path.exists(CV_TEMPLATE_PATH):
            with open(CV_TEMPLATE_PATH, "r", encoding="utf-8") as f:
                cv_content = f.read()
        else:
            cv_content = f"# Pedro Úbeda Sánchez\n**Candidatura para {puesto} en {empresa}**\n"

        # Inyectar bloque destacado al inicio de competencias
        bloque_destacado = "\n### Competencias Clave Adaptadas a la Oferta:\n" + "".join([f"- ⭐ **{s}**\n" for s in skills_destacadas])
        cv_adaptado = cv_content.replace("## Competencias Técnicas\n", f"## Competencias Técnicas\n{bloque_destacado}\n")

        # 4. Leer y adaptar la Carta de Presentación
        now = datetime.now()
        fecha_hoy = f"{now.day} de {MESES_ES[now.month]} de {now.year}"
        if os.path.exists(COVER_TEMPLATE_PATH):
            with open(COVER_TEMPLATE_PATH, "r", encoding="utf-8") as f:
                cover_content = f.read()
        else:
            cover_content = "Estimados señores:\n\nPresento mi candidatura para {{PUESTO}} en {{EMPRESA}}.\n"

        valor_especifico = f"En particular, para este rol de {puesto}, puedo aportar de forma inmediata mis conocimientos consolidados en {', '.join(skills_destacadas[:2])}, respaldados por la disciplina metódica adquirida en mis 22 años de servicio en sistemas de vuelo del Ejército del Aire."

        carta_adaptada = cover_content.replace("{{FECHA}}", fecha_hoy)
        carta_adaptada = carta_adaptada.replace("{{EMPRESA}}", empresa)
        carta_adaptada = carta_adaptada.replace("{{PUESTO}}", puesto)
        carta_adaptada = carta_adaptada.replace("{{VALOR_ESPECIFICO_OFERTA}}", valor_especifico)

        # 5. Generar vista HTML integrada con CSS elegante para impresión
        puesto_esc = html.escape(puesto)
        empresa_esc = html.escape(empresa)
        carta_esc = html.escape(carta_adaptada)
        cv_esc = html.escape(cv_adaptado)

        html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Postulación: {puesto_esc} - {empresa_esc}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #222; max-width: 800px; margin: 40px auto; padding: 0 20px; }}
  h1, h2, h3 {{ color: #0f4c81; margin-top: 1.2em; }}
  hr {{ border: 0; border-top: 1px solid #ccc; margin: 20px 0; }}
  .badge {{ background: #e3f2fd; color: #0d47a1; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.9em; }}
  .page-break {{ page-break-after: always; }}
  @media print {{ body {{ margin: 10mm; }} .no-print {{ display: none; }} }}
</style>
</head>
<body>
<div class="no-print" style="background:#f5f5f5; padding:15px; border-radius:6px; margin-bottom:30px; text-align:center;">
  <strong>Dossier de Postulación Generado</strong> | Pulsa <kbd>Ctrl+P</kbd> para imprimir o guardar como PDF.
</div>
<div>
  <h2>Carta de Presentación</h2>
  <pre style="white-space: pre-wrap; font-family: inherit;">{carta_esc}</pre>
</div>
<div class="page-break"></div>
<div>
  <h2>Currículum Vitae Adaptado</h2>
  <pre style="white-space: pre-wrap; font-family: inherit;">{cv_esc}</pre>
</div>
</body>
</html>"""

        # 6. Guardar archivos en el destino
        if not output_dir:
            slug = f"{slugify(empresa)}_{slugify(puesto)}_{of_id}"
            output_dir = os.path.join(DEFAULT_APPLICATIONS_DIR, slug)

        os.makedirs(output_dir, exist_ok=True)
        cv_path = os.path.join(output_dir, "cv_adaptado.md")
        carta_path = os.path.join(output_dir, "carta_presentacion.md")
        html_path = os.path.join(output_dir, "postulacion_completa.html")

        with open(cv_path, "w", encoding="utf-8") as f:
            f.write(cv_adaptado)

        with open(carta_path, "w", encoding="utf-8") as f:
            f.write(carta_adaptada)

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return {
            "exito": True,
            "cv_path": cv_path,
            "carta_path": carta_path,
            "html_path": html_path,
            "output_dir": output_dir,
            "skills_destacadas": skills_destacadas,
            "amenazas": threats
        }
