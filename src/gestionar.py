"""
gestionar.py - Herramienta de línea de comandos (CLI) para gestionar el estado de las ofertas de empleo
y ejecutar acciones del framework de postulación inteligente.
Uso:
  python src/gestionar.py <hash_o_prefijo> <ESTADO>
  python src/gestionar.py --list [ESTADO]
  python src/gestionar.py --info <hash_o_prefijo>
  python src/gestionar.py --apply <hash_o_prefijo>
  python src/gestionar.py --interview <hash_o_prefijo>
  python src/gestionar.py --report
  python src/gestionar.py --upskill
  python src/gestionar.py --purgar
"""

import os
import sys
import json
import sqlite3
from contextlib import contextmanager
from typing import Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

DB_PATH = os.path.join(REPO_ROOT, "data", "empleo.db")

ESTADOS_VALIDOS = ["NUEVA", "INTERESANTE", "SOLICITADA", "DESCARTADA"]

@contextmanager
def get_connection():
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: La base de datos no existe en '{DB_PATH}'. Ejecuta primero 'job_agent.py'.")
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def actualizar_estado(hash_prefix: str, nuevo_estado: str):
    nuevo_estado = nuevo_estado.upper().strip()
    if nuevo_estado not in ESTADOS_VALIDOS:
        print(f"❌ Estado inválido: '{nuevo_estado}'. Estados permitidos: {', '.join(ESTADOS_VALIDOS)}")
        return

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, puesto, empresa, estado, clasificacion FROM ofertas WHERE id LIKE ?", (f"{hash_prefix}%",))
        filas = cursor.fetchall()

        if not filas:
            print(f"⚠️ No se encontró ninguna oferta que empiece por el hash '{hash_prefix}'.")
            return
        elif len(filas) > 1:
            print(f"⚠️ El prefijo '{hash_prefix}' coincide con múltiples ofertas ({len(filas)}). Especifica más caracteres:")
            for f in filas:
                print(f"  • {f['id'][:12]} | {f['puesto']} en {f['empresa']} [{f['estado']}]")
            return

        oferta = filas[0]
        cursor.execute("UPDATE ofertas SET estado = ? WHERE id = ?", (nuevo_estado, oferta["id"]))
        conn.commit()

        iconos = {"INTERESANTE": "⭐", "SOLICITADA": "📨", "DESCARTADA": "🗑️", "NUEVA": "🆕"}
        print(f"{iconos.get(nuevo_estado, '✅')} Oferta actualizada con éxito:")
        print(f"   ID:       {oferta['id']}")
        print(f"   Puesto:   {oferta['puesto']}")
        print(f"   Empresa:  {oferta['empresa']}")
        print(f"   Estado:   {oferta['estado']} ➔ {nuevo_estado}")

def listar_ofertas(filtro_estado: Optional[str] = None):
    with get_connection() as conn:
        cursor = conn.cursor()
        if filtro_estado:
            cursor.execute("""
                SELECT id, puesto, empresa, modalidad, clasificacion, estado, fecha_procesada 
                FROM ofertas 
                WHERE estado = ? 
                ORDER BY fecha_procesada DESC
            """, (filtro_estado.upper(),))
        else:
            cursor.execute("""
                SELECT id, puesto, empresa, modalidad, clasificacion, estado, fecha_procesada 
                FROM ofertas 
                WHERE clasificacion IN ('A', 'B')
                ORDER BY fecha_procesada DESC
            """)
        filas = cursor.fetchall()

        titulo = f"Ofertas con estado '{filtro_estado.upper()}'" if filtro_estado else "Ofertas Relevantes (Clase A y B)"
        print(f"\n📋 === {titulo} ({len(filas)}) ===")
        if not filas:
            print("   No hay ofertas registradas que coincidan con el criterio.")
            return

        print(f"{'HASH':<14} | {'CLASE':<5} | {'ESTADO':<12} | {'MODALIDAD':<18} | {'PUESTO & EMPRESA'}")
        print("-" * 90)
        for f in filas:
            puesto_empresa = f"{f['puesto']} ({f['empresa']})"
            if len(puesto_empresa) > 42:
                puesto_empresa = puesto_empresa[:39] + "..."
            mod = f['modalidad'] if f['modalidad'] else "No esp."
            if len(mod) > 18:
                mod = mod[:15] + "..."
            print(f"{f['id'][:12]:<14} | {f['clasificacion']:<5} | {f['estado']:<12} | {mod:<18} | {puesto_empresa}")
        print()

def mostrar_info(hash_prefix: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ofertas WHERE id LIKE ?", (f"{hash_prefix}%",))
        filas = cursor.fetchall()

        if not filas:
            print(f"⚠️ No se encontró ninguna oferta con hash '{hash_prefix}'.")
            return
        elif len(filas) > 1:
            print(f"⚠️ Múltiples ofertas encontradas. Especifica más caracteres:")
            for f in filas:
                print(f"  • {f['id']} - {f['puesto']}")
            return

        of = dict(filas[0])
        cumple = json.loads(of.get("requisitos_cumple") or "[]")
        verificar = json.loads(of.get("requisitos_verificar") or "[]")

        print(f"\n🔍 DETALLE DE LA OFERTA [{of['id']}]")
        print(f"────────────────────────────────────────────────────────────")
        print(f"💼 Puesto:            {of['puesto']}")
        print(f"🏢 Empresa:           {of['empresa']}")
        print(f"🏷️  Clasificación:     Clase {of['clasificacion']}")
        print(f"📌 Estado Actual:     {of['estado']}")
        print(f"📍 Ubicación:         {of['ubicacion']}")
        print(f"🌐 Modalidad:         {of['modalidad']}")
        print(f"⏰ Horario/Turno:     {of['horario']}")
        print(f"💰 Salario:           {of['salario']}")
        print(f"📡 Fuente:            {of['fuente']}")
        print(f"📅 Fecha Publicada:   {of['fecha_publicacion']}")
        print(f"🕒 Fecha Procesada:   {of['fecha_procesada']}")
        print(f"🔗 Enlace:            {of['url']}")
        print(f"\n✅ Requisitos que cumplo:")
        if cumple:
            for c in cumple:
                print(f"   • {c}")
        else:
            print("   (Ninguno destacado automáticamente)")

        print(f"\n🔍 Requisitos a verificar:")
        if verificar:
            for v in verificar:
                print(f"   • {v}")
        else:
            print("   (Ninguno crítico detectado)")

        print(f"\n💡 Motivo de interés:")
        print(f"   {of.get('motivo', 'N/A')}\n")

def ejecutar_apply(hash_prefix: str):
    from tools.apply_pipeline import JobApplicationDrafter
    drafter = JobApplicationDrafter(db_path=DB_PATH)
    try:
        res = drafter.generar_postulacion(hash_prefix)
        print(f"✨ ¡Dossier de postulación generado con éxito!")
        print(f"📁 Directorio: {res['output_dir']}")
        print(f"📄 CV Adaptado:          {res['cv_path']}")
        print(f"✉️ Carta de Presentación: {res['carta_path']}")
        print(f"🌐 Vista Web Imprimible: {res['html_path']}")
        if res.get("amenazas"):
            print(f"⚠️ Advertencias de seguridad detectadas en el texto: {res['amenazas']}")
    except Exception as e:
        print(f"❌ Error al generar postulación: {e}")

def ejecutar_interview(hash_prefix: str):
    from tools.interview_prep import generar_dossier_entrevista
    try:
        res = generar_dossier_entrevista(hash_prefix, db_path=DB_PATH)
        print(f"🎤 ¡Dossier de entrevista generado con éxito!")
        print(f"🏢 Empresa:  {res['empresa']}")
        print(f"💼 Puesto:   {res['puesto']}")
        print(f"📄 Archivo:  {res['output_file']}")
    except Exception as e:
        print(f"❌ Error al generar dossier de entrevista: {e}")

def ejecutar_report():
    from tools.html_reporter import generar_reporte_html
    try:
        res = generar_reporte_html(db_path=DB_PATH)
        print(f"📊 Cuadro de mando generado con éxito ({res['total_ofertas']} ofertas analizadas).")
        print(f"🌐 Archivo: {res['output_file']}")
    except Exception as e:
        print(f"❌ Error al generar cuadro de mando: {e}")

def ejecutar_upskill():
    from tools.upskill_analyzer import analizar_brechas_db
    try:
        res = analizar_brechas_db(db_path=DB_PATH)
        print(f"\n📈 === ANÁLISIS DE BRECHAS FORMATIVAS ({res['total_analizadas']} ofertas analizadas) ===")
        print(f"{'TECNOLOGÍA':<20} | {'CATEGORÍA':<22} | {'MENCIONES':<10} | {'% OFERTAS'}")
        print("-" * 65)
        for b in res["brechas"]:
            print(f"{b['tecnologia']:<20} | {b['categoria']:<22} | {b['menciones']:<10} | {b['porcentaje_ofertas']}%")
        print("\n💡 Recomendaciones de aprendizaje prioritario:")
        for r in res["recomendaciones"]:
            print(f"  • {r}")
        print()
    except Exception as e:
        print(f"❌ Error al analizar brechas: {e}")

def purgar_base_datos(conservar_interesantes: bool = True):
    from datetime import datetime, timezone
    with get_connection() as conn:
        cursor = conn.cursor()
        if conservar_interesantes:
            cursor.execute("SELECT COUNT(*) FROM ofertas WHERE estado NOT IN ('INTERESANTE', 'SOLICITADA')")
            total = cursor.fetchone()[0]
            cursor.execute("DELETE FROM ofertas WHERE estado NOT IN ('INTERESANTE', 'SOLICITADA')")
        else:
            cursor.execute("SELECT COUNT(*) FROM ofertas")
            total = cursor.fetchone()[0]
            cursor.execute("DELETE FROM ofertas")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                clave TEXT PRIMARY KEY,
                valor TEXT NOT NULL
            )
        """)
        cursor.execute("INSERT OR REPLACE INTO metadata (clave, valor) VALUES ('ultima_purga', ?)",
                       (datetime.now(timezone.utc).isoformat(),))
        conn.commit()
        cursor.execute("VACUUM")
        conn.commit()

        cursor.execute("""
            SELECT id, puesto, empresa, ubicacion, modalidad, horario, salario,
                   url, fuente, clasificacion, estado, requisitos_cumple,
                   requisitos_verificar, motivo, fecha_publicacion, fecha_procesada
            FROM ofertas
            WHERE clasificacion IN ('A', 'B')
            ORDER BY clasificacion ASC, fecha_procesada DESC
        """)
        filas = cursor.fetchall()
        datos = []
        for f in filas:
            d = dict(f)
            d["requisitos_cumple"] = json.loads(d["requisitos_cumple"] or "[]")
            d["requisitos_verificar"] = json.loads(d["requisitos_verificar"] or "[]")
            datos.append(d)

    json_path = os.path.join(os.path.dirname(DB_PATH), "ofertas.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

    print(f"🧹 Base de datos purgada con éxito. Se eliminaron {total} ofertas (conservando interesantes/solicitadas).")
    print(f"📄 Archivo '{json_path}' sincronizado ({len(datos)} ofertas activas).")

def ayuda():
    print("""
Uso de la herramienta de gestión y postulación:

  1. Gestión de estado de ofertas:
     python src/gestionar.py <hash> <ESTADO>
     Ejemplo: python src/gestionar.py a7c612 INTERESANTE
     (Estados disponibles: NUEVA, INTERESANTE, SOLICITADA, DESCARTADA)

  2. Listar ofertas registradas:
     python src/gestionar.py --list
     python src/gestionar.py --list INTERESANTE

  3. Ver detalle completo de una oferta:
     python src/gestionar.py --info <hash>

  4. Generar CV adaptado y Carta de Presentación (/apply):
     python src/gestionar.py --apply <hash>

  5. Generar dossier de preparación de entrevista (/interview):
     python src/gestionar.py --interview <hash>

  6. Generar cuadro de mando visual offline (/html-report):
     python src/gestionar.py --report

  7. Analizar brechas tecnológicas en el mercado (/upskill):
     python src/gestionar.py --upskill

  8. Purgar base de datos:
     python src/gestionar.py --purgar
""")

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        ayuda()
        sys.exit(0)

    arg1 = sys.argv[1]

    if arg1 == "--list":
        estado = sys.argv[2] if len(sys.argv) > 2 else None
        listar_ofertas(estado)
    elif arg1 == "--info":
        if len(sys.argv) < 3:
            print("❌ Debes indicar el hash de la oferta: python src/gestionar.py --info <hash>")
            sys.exit(1)
        mostrar_info(sys.argv[2])
    elif arg1 == "--apply":
        if len(sys.argv) < 3:
            print("❌ Debes indicar el hash de la oferta: python src/gestionar.py --apply <hash>")
            sys.exit(1)
        ejecutar_apply(sys.argv[2])
    elif arg1 == "--interview":
        if len(sys.argv) < 3:
            print("❌ Debes indicar el hash de la oferta: python src/gestionar.py --interview <hash>")
            sys.exit(1)
        ejecutar_interview(sys.argv[2])
    elif arg1 == "--report":
        ejecutar_report()
    elif arg1 == "--upskill":
        ejecutar_upskill()
    elif arg1 == "--purgar":
        purgar_base_datos()
    else:
        if len(sys.argv) < 3:
            print("❌ Sintaxis: python src/gestionar.py <hash> <ESTADO>")
            print(f"   Estados válidos: {', '.join(ESTADOS_VALIDOS)}")
            sys.exit(1)
        hash_val = arg1
        estado_val = sys.argv[2]
        actualizar_estado(hash_val, estado_val)

if __name__ == "__main__":
    main()
