import re
import ast
import json
import hashlib
from typing import Any
from bs4 import BeautifulSoup

def generar_hash(empresa: str, puesto: str, url: str) -> str:
    """Genera un hash SHA-256 corto y unívoco."""
    semilla = f"{empresa.strip().lower()}|{puesto.strip().lower()}|{url.strip().lower()}"
    return hashlib.sha256(semilla.encode("utf-8")).hexdigest()[:12]

def limpiar_html(html_text: str) -> str:
    """Elimina etiquetas HTML y limpia espacios redundantes."""
    if not html_text:
        return ""
    soup = BeautifulSoup(html_text, "html.parser")
    texto = soup.get_text(separator=" ")
    return re.sub(r'\s+', ' ', texto).strip()

def formatear_salario(salario_raw: Any) -> str:
    """Formatea limpiamente el salario en caso de ser dict, JSON o texto crudo."""
    if not salario_raw or salario_raw == "No especificado":
        return "No especificado"
    
    if isinstance(salario_raw, str):
        s_strip = salario_raw.strip()
        if s_strip.startswith("{") and s_strip.endswith("}"):
            try:
                val = ast.literal_eval(s_strip)
                if isinstance(val, dict):
                    salario_raw = val
            except Exception:
                try:
                    val = json.loads(s_strip)
                    if isinstance(val, dict):
                        salario_raw = val
                except Exception:
                    pass

    if isinstance(salario_raw, dict):
        val_from = salario_raw.get("from")
        val_to = salario_raw.get("to")
        currency = salario_raw.get("currencyCode", "EUR")
        curr_sym = "€" if currency == "EUR" else currency
        period = (salario_raw.get("period") or "").upper()
        
        p_map = {
            "YEARLY": "año",
            "MONTHLY": "mes",
            "HOURLY": "hora",
            "WEEKLY": "semana",
            "DAILY": "día"
        }
        p_str = p_map.get(period, period.lower() if period else "")
        extra = salario_raw.get("extraOptions")

        res = ""
        if val_from is not None and val_to is not None:
            res = f"{val_from:,.0f} - {val_to:,.0f} {curr_sym}".replace(",", ".")
        elif val_from is not None:
            res = f"{val_from:,.0f} {curr_sym}".replace(",", ".")
        elif val_to is not None:
            res = f"Hasta {val_to:,.0f} {curr_sym}".replace(",", ".")

        if res:
            if p_str:
                res += f" / {p_str}"
            if extra:
                res += f" ({extra})"
            return res
        elif extra:
            return str(extra)
        else:
            return "No especificado"

    return str(salario_raw).strip()
