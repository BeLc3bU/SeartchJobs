import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from src.db.manager import DatabaseManager

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_REPORT_PATH = os.path.join(REPO_ROOT, "documents", "reporte_empleo.html")

def generar_reporte_html(db_path: Optional[str] = None, output_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Genera un cuadro de mando local interactivo en HTML con gráficos SVG autónomos.
    """
    db = DatabaseManager(db_path=db_path) if db_path else DatabaseManager()
    
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM ofertas")
        total_ofertas = cursor.fetchone()[0]

        cursor.execute("SELECT clasificacion, count(*) FROM ofertas GROUP BY clasificacion")
        clases = dict(cursor.fetchall())

        cursor.execute("SELECT estado, count(*) FROM ofertas GROUP BY estado")
        estados = dict(cursor.fetchall())

        cursor.execute("SELECT fuente, count(*) FROM ofertas GROUP BY fuente")
        fuentes = dict(cursor.fetchall())

        cursor.execute("""
            SELECT id, puesto, empresa, ubicacion, modalidad, salario, fuente, clasificacion, estado, fecha_procesada
            FROM ofertas
            ORDER BY fecha_procesada DESC LIMIT 50
        """)
        ultimas_ofertas = [dict(f) for f in cursor.fetchall()]

    clase_a = clases.get("A", 0)
    clase_b = clases.get("B", 0)
    clase_c = clases.get("C", 0)
    interesantes = estados.get("INTERESANTE", 0)
    solicitadas = estados.get("SOLICITADA", 0)

    # Gráfico SVG de barras por fuente
    max_fuente = max(fuentes.values()) if fuentes else 1
    svg_barras = ""
    y_offset = 25
    for f_nom, f_cnt in fuentes.items():
        w = int((f_cnt / max_fuente) * 280)
        svg_barras += f"""
        <text x="10" y="{y_offset + 14}" font-size="12" fill="#444">{f_nom} ({f_cnt})</text>
        <rect x="150" y="{y_offset}" width="{w}" height="18" rx="3" fill="#0f4c81" opacity="0.85" />
        """
        y_offset += 30

    svg_fuentes = f"""
    <svg width="450" height="{max(120, y_offset + 10)}" viewBox="0 0 450 {max(120, y_offset + 10)}">
      {svg_barras}
    </svg>
    """

    # Filas de la tabla de ofertas
    filas_html = ""
    for of in ultimas_ofertas:
        clase_badge = f'<span class="badge badge-{of["clasificacion"].lower()}">Clase {of["clasificacion"]}</span>'
        estado_badge = f'<span class="badge badge-estado">{of["estado"]}</span>'
        filas_html += f"""
        <tr>
          <td>{clase_badge}</td>
          <td><strong>{of['puesto']}</strong></td>
          <td>{of['empresa']}</td>
          <td>{of['ubicacion']} ({of['modalidad']})</td>
          <td>{of['fuente']}</td>
          <td>{estado_badge}</td>
          <td><code>{of['id'][:8]}</code></td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Reporte de Empleo: Pedro Úbeda Sánchez</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; background: #f8fafc; color: #1e293b; margin: 0; padding: 24px; }}
  .container {{ max-width: 1100px; margin: 0 auto; }}
  header {{ background: #fff; padding: 24px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; }}
  h1 {{ margin: 0; font-size: 22px; color: #0f172a; }}
  .subtitle {{ color: #64748b; font-size: 14px; margin-top: 4px; }}
  .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }}
  .card {{ background: #fff; padding: 20px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
  .kpi-num {{ font-size: 28px; font-weight: bold; margin-top: 6px; }}
  .kpi-label {{ font-size: 13px; color: #64748b; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; }}
  .color-a {{ color: #16a34a; }}
  .color-b {{ color: #ca8a04; }}
  .color-int {{ color: #2563eb; }}
  .color-sol {{ color: #9333ea; }}
  .charts-grid {{ display: grid; grid-template-columns: 1fr; gap: 24px; margin-bottom: 24px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
  th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; font-size: 13.5px; }}
  th {{ background: #f1f5f9; color: #475569; font-weight: 600; }}
  .badge {{ display: inline-block; padding: 3px 8px; border-radius: 9999px; font-size: 11px; font-weight: 600; }}
  .badge-a {{ background: #dcfce7; color: #166534; }}
  .badge-b {{ background: #fef9c3; color: #854d0e; }}
  .badge-c {{ background: #f1f5f9; color: #475569; }}
  .badge-estado {{ background: #e0f2fe; color: #0369a1; }}
</style>
</head>
<body>
<div class="container">
  <header>
    <div>
      <h1>Cuadro de Mando y Reporte de Empleo Personalizado</h1>
      <div class="subtitle">Candidato: Pedro Úbeda Sánchez | Generado el {datetime.now().strftime("%d/%m/%Y %H:%M")}</div>
    </div>
  </header>

  <div class="kpi-grid">
    <div class="card">
      <div class="kpi-label">Total Ofertas</div>
      <div class="kpi-num">{total_ofertas}</div>
    </div>
    <div class="card">
      <div class="kpi-label">Clase A (Encaje Directo)</div>
      <div class="kpi-num color-a">{clase_a}</div>
    </div>
    <div class="card">
      <div class="kpi-label">Clase B (Potencial)</div>
      <div class="kpi-num color-b">{clase_b}</div>
    </div>
    <div class="card">
      <div class="kpi-label">Interesantes</div>
      <div class="kpi-num color-int">{interesantes}</div>
    </div>
    <div class="card">
      <div class="kpi-label">Solicitadas / Enviadas</div>
      <div class="kpi-num color-sol">{solicitadas}</div>
    </div>
  </div>

  <div class="charts-grid">
    <div class="card">
      <h3>Distribución de Ofertas por Portal</h3>
      {svg_fuentes}
    </div>
  </div>

  <div class="card">
    <h3>Últimas Vacantes Procesadas</h3>
    <table>
      <thead>
        <tr>
          <th>Clase</th>
          <th>Puesto</th>
          <th>Empresa</th>
          <th>Ubicación</th>
          <th>Fuente</th>
          <th>Estado</th>
          <th>Hash</th>
        </tr>
      </thead>
      <tbody>
        {filas_html}
      </tbody>
    </table>
  </div>
</div>
</body>
</html>"""

    if not output_file:
        output_file = DEFAULT_REPORT_PATH

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    return {
        "exito": True,
        "output_file": output_file,
        "total_ofertas": total_ofertas
    }
