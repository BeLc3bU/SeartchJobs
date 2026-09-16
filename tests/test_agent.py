"""
test_agent.py - Suite de pruebas unitarias y de integración para AlertasEmpleo.
"""

import os
import sys
import unittest
import sqlite3
import json

# Añadir src al path
SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
sys.path.insert(0, SRC_DIR)

from job_agent import DatabaseManager, ProfileMatcher, TelegramDispatcher, generar_hash, limpiar_html


class TestProfileMatcher(unittest.TestCase):
    def setUp(self):
        self.matcher = ProfileMatcher()

    def test_remoto_espana_sysadmin_clase_a(self):
        oferta = {
            "puesto": "Administrador de Sistemas Linux y Redes",
            "descripcion": "Buscamos un administrador de sistemas con experiencia en Debian, Ubuntu, gestión de Active Directory, firewall y soporte L3. Trabajo 100% remoto desde España.",
            "ubicacion": "Remoto España",
            "modalidad": "REMOTO",
            "horario": "FLEXIBLE"
        }
        res = self.matcher.evaluar_oferta(oferta)
        self.assertEqual(res["clasificacion"], "A")
        self.assertTrue(any("Linux" in c or "sistemas" in c for c in res["requisitos_cumple"]))
        self.assertEqual(len(res["requisitos_verificar"]), 0)

    def test_descarte_presencial_madrid(self):
        oferta = {
            "puesto": "Técnico de Soporte e Infraestructura",
            "descripcion": "Puesto presencial obligatorio en nuestras oficinas centrales de Madrid.",
            "ubicacion": "Madrid",
            "modalidad": "PRESENCIAL",
            "horario": "Jornada completa"
        }
        res = self.matcher.evaluar_oferta(oferta)
        self.assertEqual(res["clasificacion"], "C")
        self.assertIn("Descartada por restricciones de ubicación/horario", res["motivo"])

    def test_descarte_albacete_turno_manana(self):
        oferta = {
            "puesto": "Técnico Informático y Redes",
            "descripcion": "Mantenimiento informático presencial en Albacete capital. Horario: Turno de mañana de 08:00 a 15:00.",
            "ubicacion": "Albacete",
            "modalidad": "PRESENCIAL",
            "horario": "Turno de mañana"
        }
        res = self.matcher.evaluar_oferta(oferta)
        self.assertEqual(res["clasificacion"], "C")
        self.assertIn("mañana", res["motivo"].lower())

    def test_albacete_turno_tarde_avionica_clase_a(self):
        oferta = {
            "puesto": "Técnico de Mantenimiento Electrónico y Calibración",
            "descripcion": "Diagnóstico de hardware, instrumentación, banco de pruebas y calibración electrónica en Hellín. Horario: Turno de tarde de 15:00 a 22:00.",
            "ubicacion": "Hellín",
            "modalidad": "PRESENCIAL",
            "horario": "Turno de tarde"
        }
        res = self.matcher.evaluar_oferta(oferta)
        self.assertEqual(res["clasificacion"], "A")
        self.assertTrue(any("Aviónica" in c or "hardware" in c for c in res["requisitos_cumple"]))

    def test_remoto_verificacion_certificacion_clase_b(self):
        oferta = {
            "puesto": "Ingeniero de Redes y Seguridad",
            "descripcion": "Gestión de redes WAN, switches Cisco, VPN y firewall. Requisito deseable o certificación oficial Cisco CCNA o Azure. Modalidad teletrabajo.",
            "ubicacion": "España",
            "modalidad": "REMOTO",
            "horario": "FLEXIBLE"
        }
        res = self.matcher.evaluar_oferta(oferta)
        self.assertEqual(res["clasificacion"], "B")
        self.assertTrue(any("CCNA" in v or "Azure" in v for v in res["requisitos_verificar"]))

    def test_remoto_administrativo_contable_clase_a(self):
        oferta = {
            "puesto": "Auxiliar Administrativo y Gestión Documental",
            "descripcion": "Gestión de facturación, albaranes, pedidos y conciliación bancaria con Excel y ERP. Puesto 100% teletrabajo.",
            "ubicacion": "España",
            "modalidad": "REMOTO",
            "horario": "FLEXIBLE"
        }
        res = self.matcher.evaluar_oferta(oferta)
        self.assertEqual(res["clasificacion"], "A")
        self.assertTrue(any("Administración" in c or "contable" in c for c in res["requisitos_cumple"]))


class TestDatabaseAndDeduplication(unittest.TestCase):
    def setUp(self):
        self.test_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_empleo.db")
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        self.db = DatabaseManager(self.test_db)

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_hash_generation(self):
        h1 = generar_hash("Inetum", "Administrador Linux", "https://example.com/job1")
        h2 = generar_hash("inetum", "ADMINISTRADOR LINUX", "https://example.com/job1")
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 12)

    def test_guardar_y_recuperar(self):
        h = generar_hash("EmpresaTest", "PuestoTest", "https://test.com/1")
        oferta = {
            "id": h,
            "puesto": "DevOps & Sysadmin",
            "empresa": "EmpresaTest",
            "ubicacion": "Remoto",
            "modalidad": "REMOTO",
            "horario": "FLEXIBLE",
            "salario": "35.000€",
            "url": "https://test.com/1",
            "fuente": "Test Source",
            "clasificacion": "A",
            "requisitos_cumple": ["Linux", "Python"],
            "requisitos_verificar": [],
            "motivo": "Buen encaje",
            "fecha_publicacion": "2026-09-16"
        }
        self.assertFalse(self.db.existe_oferta(h))
        self.db.guardar_oferta(oferta)
        self.assertTrue(self.db.existe_oferta(h))

        recientes = self.db.obtener_nuevas_relevantes(horas=24)
        self.assertEqual(len(recientes), 1)
        self.assertEqual(recientes[0]["id"], h)
        self.assertEqual(recientes[0]["clasificacion"], "A")
        self.assertEqual(recientes[0]["requisitos_cumple"], ["Linux", "Python"])


class TestTelegramFormatting(unittest.TestCase):
    def test_formatear_oferta(self):
        dispatcher = TelegramDispatcher()
        oferta = {
            "id": "abc123def456",
            "puesto": "Especialista en Simulación y Electrónica",
            "empresa": "Airbus / FAS Partner",
            "clasificacion": "A",
            "ubicacion": "Albacete",
            "modalidad": "Presencial Tardes",
            "salario": "32.000€ - 38.000€",
            "requisitos_cumple": ["Aviónica y bancos de prueba", "Diagnóstico de hardware"],
            "requisitos_verificar": [],
            "motivo": "Excelente adecuación a simuladores C-101 y sistemas críticos.",
            "url": "https://ofertas.example.com/simulacion",
            "fuente": "Tecnoempleo RSS"
        }
        html = dispatcher.formatear_oferta_html(oferta)
        self.assertIn("Especialista en Simulación y Electrónica", html)
        self.assertIn("CLASE A", html)
        self.assertIn("Requisitos que cumplo", html)
        self.assertIn("Hash: abc123def456", html)


if __name__ == "__main__":
    unittest.main()
