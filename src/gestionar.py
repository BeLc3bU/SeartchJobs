"""
gestionar.py - Herramienta de línea de comandos (CLI) para gestionar el estado de las ofertas de empleo.
Uso:
  python src/gestionar.py <hash_o_prefijo> <ESTADO>
  python src/gestionar.py --list [ESTADO]
  python src/gestionar.py --info <hash_o_prefijo>
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

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "empleo.db")

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
        # Buscar por prefijo de hash
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


def purgar_base_datos():
    from datetime import datetime, timezone
    with get_connection() as conn:
        cursor = conn.cursor()
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

    json_path = os.path.join(os.path.dirname(DB_PATH), "ofertas.json")
    with open(json_path, "w", encoding="utf-8") as f:
        f.write("[]\n")

    print(f"🧹 Base de datos purgada con éxito. Se eliminaron {total} ofertas registradas.")
    print(f"📄 Archivo '{json_path}' restablecido a lista vacía.")


def ayuda():
    print("""
Uso de la herramienta de gestión de ofertas:

  1. Actualizar estado de una oferta por hash:
     python src/gestionar.py <hash> <ESTADO>
     Ejemplo: python src/gestionar.py a7c612 INTERESANTE
     (Estados disponibles: NUEVA, INTERESANTE, SOLICITADA, DESCARTADA)

  2. Listar ofertas registradas:
     python src/gestionar.py --list
     python src/gestionar.py --list INTERESANTE
     python src/gestionar.py --list SOLICITADA

  3. Ver información detallada de una oferta:
     python src/gestionar.py --info <hash>
     Ejemplo: python src/gestionar.py --info a7c612

  4. Purgar base de datos y restablecer ofertas:
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
    elif arg1 == "--purgar":
        purgar_base_datos()
    else:
        # Modo: <hash> <ESTADO>
        if len(sys.argv) < 3:
            print("❌ Sintaxis: python src/gestionar.py <hash> <ESTADO>")
            print(f"   Estados válidos: {', '.join(ESTADOS_VALIDOS)}")
            sys.exit(1)
        hash_val = arg1
        estado_val = sys.argv[2]
        actualizar_estado(hash_val, estado_val)


if __name__ == "__main__":
    main()
