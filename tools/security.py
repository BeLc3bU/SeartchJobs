import re
from typing import Dict, List, Any

# Patrones de inyección de instrucciones para LLMs
PROMPT_INJECTION_PATTERNS = [
    r'ignore\s+(?:all\s+)?previous\s+instructions',
    r'disregard\s+(?:all\s+)?prior\s+instructions',
    r'system\s+prompt',
    r'output\s+your\s+initial\s+prompt',
    r'you\s+are\s+now\s+(?:a|an)\b',
    r'\bjailbreak\b',
    r'\bdan\s+mode\b',
    r'override\s+security\s+protocols',
    r'olvida\s+(?:todas\s+)?las\s+instrucciones\s+anteriores',
    r'muestra\s+tu\s+prompt\s+del\s+sistema'
]

ZERO_WIDTH_CHARS = [
    '\u200b',  # Zero-width space
    '\u200c',  # Zero-width non-joiner
    '\u200d',  # Zero-width joiner
    '\u2060',  # Word joiner
    '\ufeff'   # Zero-width no-break space / BOM
]

def sanitize_posting(raw_text: str) -> Dict[str, Any]:
    """
    Analiza y sanitiza el texto de una oferta de empleo para proteger el agente de IA.
    Detecta caracteres invisibles y patrones de inyección de prompts.
    """
    if not raw_text:
        return {
            "is_clean": True,
            "threats": [],
            "clean_text": ""
        }

    threats: List[str] = []

    # 1. Detección de caracteres invisibles / zero-width
    has_zero_width = False
    for ch in ZERO_WIDTH_CHARS:
        if ch in raw_text:
            has_zero_width = True
            break

    if has_zero_width:
        threats.append("zero_width_characters_detected")

    # Limpiar caracteres zero-width
    clean_text = raw_text
    for ch in ZERO_WIDTH_CHARS:
        clean_text = clean_text.replace(ch, "")

    # 2. Detección de inyecciones de prompt
    text_lower = clean_text.lower()
    for pat in PROMPT_INJECTION_PATTERNS:
        if re.search(pat, text_lower):
            threats.append(f"prompt_injection_pattern: {pat}")

    is_clean = (len(threats) == 0)

    # Limpieza básica de espacios
    clean_text = re.sub(r'[ \t]+', ' ', clean_text).strip()

    return {
        "is_clean": is_clean,
        "threats": threats,
        "clean_text": clean_text
    }
