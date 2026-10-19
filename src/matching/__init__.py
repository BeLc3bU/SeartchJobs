# src/matching/__init__.py
from .normalizer import generar_hash, limpiar_html, formatear_salario
from .matcher import ProfileMatcher

__all__ = ["generar_hash", "limpiar_html", "formatear_salario", "ProfileMatcher"]
