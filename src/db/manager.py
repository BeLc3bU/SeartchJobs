import os
import json
import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

logger = logging.getLogger("JobAgent.DB")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "empleo.db")

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ofertas (
                    id TEXT PRIMARY KEY,
                    puesto TEXT NOT NULL,
                    empresa TEXT NOT NULL,
                    ubicacion TEXT,
                    modalidad TEXT,
                    horario TEXT,
                    salario TEXT,
                    url TEXT NOT NULL,
                    fuente TEXT NOT NULL,
                    clasificacion TEXT NOT NULL,  -- 'A', 'B', 'C'
                    estado TEXT DEFAULT 'NUEVA',  -- 'NUEVA', 'INTERESANTE', 'SOLICITADA', 'DESCARTADA'
                    requisitos_cumple TEXT,
                    requisitos_verificar TEXT,
                    motivo TEXT,
                    fecha_publicacion TEXT,
                    fecha_procesada TEXT NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ofertas_clasificacion ON ofertas(clasificacion)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ofertas_estado ON ofertas(estado)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ofertas_fecha ON ofertas(fecha_procesada)")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    clave TEXT PRIMARY KEY,
                    valor TEXT NOT NULL
                )
            """)

            # Migración: asegurar que la columna descripcion existe
            cursor.execute("PRAGMA table_info(ofertas)")
            cols = [col[1] for col in cursor.fetchall()]
            if "descripcion" not in cols:
                cursor.execute("ALTER TABLE ofertas ADD COLUMN descripcion TEXT DEFAULT ''")

            conn.commit()
            logger.info("Base de datos SQLite verificada en %s", self.db_path)

    def existe_oferta(self, oferta_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM ofertas WHERE id = ?", (oferta_id,))
            return cursor.fetchone() is not None

    def guardar_oferta(self, oferta: Dict[str, Any]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO ofertas (
                    id, puesto, empresa, ubicacion, modalidad, horario, salario,
                    url, fuente, clasificacion, estado, requisitos_cumple,
                    requisitos_verificar, motivo, fecha_publicacion, fecha_procesada, descripcion
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                oferta["id"],
                oferta["puesto"],
                oferta["empresa"],
                oferta.get("ubicacion", "No especificada"),
                oferta.get("modalidad", "No especificada"),
                oferta.get("horario", "No especificado"),
                oferta.get("salario", "No especificado"),
                oferta["url"],
                oferta.get("fuente", "Desconocida"),
                oferta["clasificacion"],
                oferta.get("estado", "NUEVA" if oferta["clasificacion"] in ("A", "B") else "DESCARTADA"),
                json.dumps(oferta.get("requisitos_cumple", []), ensure_ascii=False),
                json.dumps(oferta.get("requisitos_verificar", []), ensure_ascii=False),
                oferta.get("motivo", ""),
                oferta.get("fecha_publicacion", ""),
                oferta.get("fecha_procesada", datetime.now(timezone.utc).isoformat()),
                oferta.get("descripcion", "")
            ))
            conn.commit()

    def guardar_ofertas_batch(self, ofertas: List[Dict[str, Any]]) -> int:
        nuevas = 0
        for of in ofertas:
            if not self.existe_oferta(of["id"]):
                self.guardar_oferta(of)
                nuevas += 1
            else:
                self.guardar_oferta(of)
        return nuevas

    def obtener_nuevas_relevantes(self, horas: int = 24) -> List[Dict[str, Any]]:
        limite_tiempo = (datetime.now(timezone.utc) - timedelta(hours=horas)).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM ofertas 
                WHERE clasificacion IN ('A', 'B') 
                  AND estado = 'NUEVA'
                  AND fecha_procesada >= ?
                ORDER BY clasificacion ASC, fecha_procesada DESC
            """, (limite_tiempo,))
            filas = cursor.fetchall()
            resultado = []
            for f in filas:
                d = dict(f)
                d["requisitos_cumple"] = json.loads(d["requisitos_cumple"] or "[]")
                d["requisitos_verificar"] = json.loads(d["requisitos_verificar"] or "[]")
                resultado.append(d)
            return resultado

    def obtener_resumen(self) -> Dict[str, int]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT estado, COUNT(*) FROM ofertas GROUP BY estado")
            estados = dict(cursor.fetchall())
            cursor.execute("SELECT clasificacion, COUNT(*) FROM ofertas GROUP BY clasificacion")
            clases = dict(cursor.fetchall())
            return {"estados": estados, "clases": clases}

    def obtener_interesantes(self, limite: int = 10) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM ofertas 
                WHERE estado = 'INTERESANTE' 
                ORDER BY fecha_procesada DESC LIMIT ?
            """, (limite,))
            filas = cursor.fetchall()
            res = []
            for f in filas:
                d = dict(f)
                d["requisitos_cumple"] = json.loads(d["requisitos_cumple"] or "[]")
                d["requisitos_verificar"] = json.loads(d["requisitos_verificar"] or "[]")
                res.append(d)
            return res

    def purgar_ofertas_anteriores(self, conservar_interesantes: bool = True) -> int:
        hoy_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if conservar_interesantes:
                cursor.execute("""
                    DELETE FROM ofertas 
                    WHERE DATE(fecha_procesada) < ? 
                      AND estado NOT IN ('INTERESANTE', 'SOLICITADA')
                """, (hoy_str,))
            else:
                cursor.execute("""
                    DELETE FROM ofertas 
                    WHERE DATE(fecha_procesada) < ?
                """, (hoy_str,))
            eliminadas = cursor.rowcount
            cursor.execute("INSERT OR REPLACE INTO metadata (clave, valor) VALUES ('ultima_purga', ?)",
                           (datetime.now(timezone.utc).isoformat(),))
            conn.commit()
            cursor.execute("VACUUM")
            conn.commit()

        self.exportar_json()
        logger.info("Purga de ofertas anteriores completada: %d ofertas eliminadas.", eliminadas)
        return eliminadas

    def purgar(self, conservar_interesantes: bool = False) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if conservar_interesantes:
                cursor.execute("SELECT COUNT(*) FROM ofertas WHERE estado NOT IN ('INTERESANTE', 'SOLICITADA')")
                total = cursor.fetchone()[0]
                cursor.execute("DELETE FROM ofertas WHERE estado NOT IN ('INTERESANTE', 'SOLICITADA')")
            else:
                cursor.execute("SELECT COUNT(*) FROM ofertas")
                total = cursor.fetchone()[0]
                cursor.execute("DELETE FROM ofertas")
            cursor.execute("INSERT OR REPLACE INTO metadata (clave, valor) VALUES ('ultima_purga', ?)",
                           (datetime.now(timezone.utc).isoformat(),))
            conn.commit()
            cursor.execute("VACUUM")
            conn.commit()

        self.exportar_json()
        logger.info("Base de datos purgada: %d ofertas eliminadas.", total)
        return total

    def purgar_semanal_si_procede(self, dias: int = 7) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT valor FROM metadata WHERE clave = 'ultima_purga'")
            fila = cursor.fetchone()

        if not fila:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT OR REPLACE INTO metadata (clave, valor) VALUES ('ultima_purga', ?)",
                               (datetime.now(timezone.utc).isoformat(),))
                conn.commit()
            return False

        try:
            ultima_fecha = datetime.fromisoformat(fila["valor"])
            if ultima_fecha.tzinfo is None:
                ultima_fecha = ultima_fecha.replace(tzinfo=timezone.utc)
            diferencia = datetime.now(timezone.utc) - ultima_fecha
            if diferencia >= timedelta(days=dias):
                logger.info("Han pasado %d días desde la última purga (%s). Ejecutando purga semanal...", diferencia.days, fila["valor"])
                self.purgar()
                return True
        except Exception as e:
            logger.warning("Error al evaluar fecha de última purga: %s", e)

        return False

    def obtener_ultimas_activas(self, limite: int = 5, clasificacion: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if clasificacion:
                cursor.execute("""
                    SELECT * FROM ofertas 
                    WHERE clasificacion = ? AND estado != 'DESCARTADA'
                    ORDER BY fecha_procesada DESC LIMIT ?
                """, (clasificacion, limite))
            else:
                cursor.execute("""
                    SELECT * FROM ofertas 
                    WHERE clasificacion IN ('A', 'B') AND estado != 'DESCARTADA'
                    ORDER BY clasificacion ASC, fecha_procesada DESC LIMIT ?
                """, (limite,))
            filas = cursor.fetchall()
            res = []
            for f in filas:
                d = dict(f)
                d["requisitos_cumple"] = json.loads(d["requisitos_cumple"] or "[]")
                d["requisitos_verificar"] = json.loads(d["requisitos_verificar"] or "[]")
                res.append(d)
            return res

    def actualizar_estado_oferta(self, hash_prefix: str, nuevo_estado: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, puesto, empresa, estado FROM ofertas WHERE id LIKE ?", (f"{hash_prefix}%",))
            filas = cursor.fetchall()
            if not filas or len(filas) > 1:
                return None
            of = filas[0]
            cursor.execute("UPDATE ofertas SET estado = ? WHERE id = ?", (nuevo_estado, of["id"]))
            conn.commit()
            return dict(of)

    def exportar_json(self, output_path: Optional[str] = None):
        if not output_path:
            output_path = os.path.join(os.path.dirname(self.db_path), "ofertas.json")
        with self._get_connection() as conn:
            cursor = conn.cursor()
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
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False, indent=2)
            logger.info("Exportado archivo JSON con %d ofertas en %s", len(datos), output_path)

    def reclasificar_bd(self, matcher: Any) -> int:
        actualizadas = 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ofertas")
            filas = cursor.fetchall()
            for f in filas:
                of_dict = dict(f)
                res = matcher.evaluar_oferta(of_dict)
                nueva_clase = res["clasificacion"]
                nuevo_motivo = res["motivo"]
                nuevo_cumple = json.dumps(res.get("requisitos_cumple", []), ensure_ascii=False)
                nuevo_verif = json.dumps(res.get("requisitos_verificar", []), ensure_ascii=False)
                
                nuevo_estado = of_dict["estado"]
                if nueva_clase == "C" and of_dict["estado"] != "DESCARTADA":
                    nuevo_estado = "DESCARTADA"

                if (nueva_clase != of_dict["clasificacion"] or 
                    nuevo_motivo != of_dict["motivo"] or 
                    nuevo_estado != of_dict["estado"]):
                    cursor.execute("""
                        UPDATE ofertas
                        SET clasificacion = ?, motivo = ?, requisitos_cumple = ?, 
                            requisitos_verificar = ?, estado = ?
                        WHERE id = ?
                    """, (nueva_clase, nuevo_motivo, nuevo_cumple, nuevo_verif, nuevo_estado, of_dict["id"]))
                    actualizadas += 1
            conn.commit()
        logger.info("Reclasificación de BD completada: %d ofertas actualizadas.", actualizadas)
        return actualizadas
