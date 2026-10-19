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

def test_db_obtener_oferta(tmp_path):
    db_file = str(tmp_path / "test_empleo.db")
    db = DatabaseManager(db_path=db_file)
    db.guardar_oferta({
        "id": "abc123456789",
        "puesto": "Sysadmin",
        "empresa": "Tech",
        "url": "https://ejemplo.com",
        "clasificacion": "A"
    })
    of = db.obtener_oferta("abc12345")
    assert of is not None
    assert of["puesto"] == "Sysadmin"
    assert db.obtener_oferta("inexistente") is None

def test_db_actualizar_estado_oferta(tmp_path):
    import json
    db_file = str(tmp_path / "test_empleo.db")
    db = DatabaseManager(db_path=db_file)
    db.guardar_oferta({
        "id": "abc123456789",
        "puesto": "Sysadmin",
        "empresa": "Tech",
        "url": "https://ejemplo.com",
        "clasificacion": "A",
        "estado": "NUEVA"
    })
    res = db.actualizar_estado_oferta("abc12345", "INTERESANTE")
    assert res is not None
    assert res["id"] == "abc123456789"
    of = db.obtener_oferta("abc12345")
    assert of["estado"] == "INTERESANTE"

    json_file = str(tmp_path / "ofertas.json")
    assert os.path.exists(json_file)
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert len(data) == 1
        assert data[0]["estado"] == "INTERESANTE"


