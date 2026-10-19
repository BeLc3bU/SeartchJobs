import re
from typing import Dict, Any, List, Optional
from collections import Counter
from src.db.manager import DatabaseManager

TECH_CATALOG = {
    "Cloud Computing": ["aws", "azure", "gcp", "google cloud"],
    "Contenedores & DevOps": ["kubernetes", "k8s", "docker", "terraform", "ansible", "ci/cd", "jenkins"],
    "Redes Avanzadas": ["ccna", "ccnp", "fortinet", "pfsense", "juniper"],
    "Ciberseguridad": ["iso 27001", "ens", "soc", "siem", "ethical hacking", "comptia"],
    "Desarrollo & Datos": ["react", "node", "typescript", "fastapi", "postgresql", "powerbi"]
}

def analizar_brechas_db(db_path: Optional[str] = None, limit: int = 300) -> Dict[str, Any]:
    """
    Analiza las ofertas en SQLite para detectar competencias emergentes y sugerir formación.
    """
    db = DatabaseManager(db_path=db_path) if db_path else DatabaseManager()
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT puesto, descripcion, clasificacion FROM ofertas LIMIT ?", (limit,))
        filas = cursor.fetchall()

    if not filas:
        return {
            "total_analizadas": 0,
            "brechas": [],
            "recomendaciones": ["Activa el agente diario para recopilar vacantes y realizar análisis."]
        }

    contador = Counter()
    total = len(filas)

    for f in filas:
        texto = f"{f['puesto']} {f['descripcion']}".lower()
        for categoria, terminos in TECH_CATALOG.items():
            for t in terminos:
                if re.search(r'\b' + re.escape(t) + r'\b', texto):
                    contador[(categoria, t)] += 1

    brechas = []
    for (categoria, termino), count in contador.most_common(15):
        pct = round((count / total) * 100, 1)
        brechas.append({
            "tecnologia": termino.upper() if len(termino) <= 4 else termino.capitalize(),
            "categoria": categoria,
            "menciones": count,
            "porcentaje_ofertas": pct
        })

    # Recomendaciones sugeridas
    recomendaciones = []
    top_cats = Counter([b["categoria"] for b in brechas[:6]]).most_common(2)
    for cat, _ in top_cats:
        recomendaciones.append(f"Priorizar acreditación formativa en el área de **{cat}** (alta demanda en las vacantes analizadas).")

    if not recomendaciones:
        recomendaciones.append("Mantener el foco en la titulación superior ASIR y profundización en automatización con Python y Linux.")

    return {
        "total_analizadas": total,
        "brechas": brechas,
        "recomendaciones": recomendaciones
    }
