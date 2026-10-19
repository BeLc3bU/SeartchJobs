import os
import pytest
from src.db.manager import DatabaseManager
from src.matching.normalizer import generar_hash, limpiar_html, formatear_salario

def test_normalizer_functions():
    assert limpiar_html("<p>Hola   <b>Mundo</b></p>") == "Hola Mundo"
    h = generar_hash("Empresa", "Puesto", "https://ejemplo.com")
    assert len(h) == 12
    assert "30.000 - 40.000 €" in formatear_salario({"from": 30000, "to": 40000})

def test_db_manager_creation(tmp_path):
    db_file = str(tmp_path / "test_empleo.db")
    db = DatabaseManager(db_path=db_file)
    assert os.path.exists(db_file)
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM ofertas")
        assert cursor.fetchone()[0] == 0
