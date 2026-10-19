import pytest
from src.matching.matcher import ProfileMatcher

def test_profile_matcher_remoto_directo():
    matcher = ProfileMatcher()
    oferta = {
        "puesto": "Administrador de Sistemas Linux y Redes",
        "descripcion": "Gestión de servidores Linux, Proxmox, redes. 100% teletrabajo en tiempo parcial tardes.",
        "ubicacion": "Remoto España",
        "modalidad": "REMOTO",
        "horario": "Tiempo parcial por la tarde"
    }
    resultado = matcher.evaluar_oferta(oferta)
    assert resultado["clasificacion"] in ["A", "B"]
    assert "Teletrabajo" in resultado["motivo"] or "Remoto" in resultado["motivo"]

def test_profile_matcher_descarte_presencial_madrid():
    matcher = ProfileMatcher()
    oferta = {
        "puesto": "Técnico de Redes",
        "descripcion": "Presencial en Madrid en jornada partida.",
        "ubicacion": "Madrid",
        "modalidad": "Presencial",
        "horario": "Jornada partida"
    }
    resultado = matcher.evaluar_oferta(oferta)
    assert resultado["clasificacion"] == "C"
