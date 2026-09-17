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

from job_agent import DatabaseManager, ProfileMatcher, TelegramDispatcher, generar_hash, limpiar_html, formatear_salario


class TestProfileMatcher(unittest.TestCase):
    def setUp(self):
        self.matcher = ProfileMatcher()

    def test_remoto_espana_sysadmin_parcial_tarde_clase_a(self):
        oferta = {
            "puesto": "Administrador de Sistemas Linux y Redes",
            "descripcion": "Buscamos un administrador de sistemas con experiencia en Debian, Ubuntu, Active Directory. Modalidad: 100% teletrabajo en tiempo parcial tardes.",
            "ubicacion": "Remoto España",
            "modalidad": "REMOTO",
            "horario": "Tiempo parcial por la tarde"
        }
        res = self.matcher.evaluar_oferta(oferta)
        self.assertEqual(res["clasificacion"], "A")
        self.assertTrue(any("Linux" in c or "sistemas" in c for c in res["requisitos_cumple"]))
        self.assertEqual(len(res["requisitos_verificar"]), 0)

    def test_descarte_jornada_completa(self):
        oferta = {
            "puesto": "Administrador de Sistemas Linux y Redes",
            "descripcion": "Puesto 100% remoto en España. Jornada completa de 40 horas semanales de lunes a viernes.",
            "ubicacion": "Remoto España",
            "modalidad": "REMOTO",
            "horario": "Jornada completa"
        }
        res = self.matcher.evaluar_oferta(oferta)
        self.assertEqual(res["clasificacion"], "C")
        self.assertIn("tiempo completo", res["motivo"].lower())

    def test_descarte_presencial_madrid(self):
        oferta = {
            "puesto": "Técnico de Soporte e Infraestructura",
            "descripcion": "Puesto presencial obligatorio en nuestras oficinas centrales de Madrid.",
            "ubicacion": "Madrid",
            "modalidad": "PRESENCIAL",
            "horario": "Media jornada tarde"
        }
        res = self.matcher.evaluar_oferta(oferta)
        self.assertEqual(res["clasificacion"], "C")
        self.assertIn("restricciones de ubicación", res["motivo"].lower())

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
        self.assertIn("turno de mañana", res["motivo"].lower())

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

    def test_remoto_fin_de_semana_clase_a(self):
        oferta = {
            "puesto": "Operador de Sistemas y Soporte IT",
            "descripcion": "Monitorización y soporte de sistemas los fines de semana (sábados y domingos). 100% teletrabajo.",
            "ubicacion": "España",
            "modalidad": "REMOTO",
            "horario": "Fin de semana"
        }
        res = self.matcher.evaluar_oferta(oferta)
        self.assertEqual(res["clasificacion"], "A")

    def test_descarte_horario_no_especificado_sin_parcial_clase_c(self):
        oferta = {
            "puesto": "Técnico de Redes y Seguridad",
            "descripcion": "Gestión de redes WAN, switches Cisco, VPN y firewall. Modalidad teletrabajo.",
            "ubicacion": "España",
            "modalidad": "REMOTO",
            "horario": "No especificado"
        }
        res = self.matcher.evaluar_oferta(oferta)
        self.assertEqual(res["clasificacion"], "C")
        self.assertIn("No especifica turno de tarde", res["motivo"])

    def test_descarte_jornada_parcial_manana(self):
        oferta = {
            "puesto": "Administrador de Sistemas Linux",
            "descripcion": "Gestión de servidores Linux y soporte técnico. Horario parcial en turno de mañana.",
            "ubicacion": "España",
            "modalidad": "REMOTO",
            "horario": "Jornada parcial - mañana"
        }
        res = self.matcher.evaluar_oferta(oferta)
        self.assertEqual(res["clasificacion"], "C")
        self.assertIn("turno de mañana", res["motivo"].lower())

    def test_remoto_tiempo_parcial_flexible_clase_b(self):
        oferta = {
            "puesto": "Técnico de Redes y Seguridad",
            "descripcion": "Gestión de redes WAN, switches Cisco, VPN y firewall. Modalidad teletrabajo 20 horas semanales.",
            "ubicacion": "España",
            "modalidad": "REMOTO",
            "horario": "Tiempo parcial"
        }
        res = self.matcher.evaluar_oferta(oferta)
        self.assertEqual(res["clasificacion"], "B")
        self.assertTrue(any("tiempo parcial" in v.lower() for v in res["requisitos_verificar"]))

    def test_remoto_administrativo_contable_tarde_clase_a(self):
        oferta = {
            "puesto": "Auxiliar Administrativo y Gestión Documental",
            "descripcion": "Gestión de facturación, albaranes, pedidos y conciliación bancaria con Excel y ERP. Horario vespertino de tardes. Puesto 100% teletrabajo.",
            "ubicacion": "España",
            "modalidad": "REMOTO",
            "horario": "Turno de tarde"
        }
        res = self.matcher.evaluar_oferta(oferta)
        self.assertEqual(res["clasificacion"], "A")
        self.assertTrue(any("Administración" in c or "contable" in c for c in res["requisitos_cumple"]))

    def test_descarte_idioma_ingles(self):
        oferta = {
            "puesto": "Senior Systems Engineer / Linux Sysadmin",
            "descripcion": "We are looking for a senior systems administrator to join our remote team. Requirements: 5 years experience with Linux, Kubernetes, AWS, and networking. Fully remote from Spain or worldwide.",
            "ubicacion": "Remote (Spain)",
            "modalidad": "REMOTO",
            "horario": "Part-time afternoon"
        }
        res = self.matcher.evaluar_oferta(oferta)
        self.assertEqual(res["clasificacion"], "C")
        self.assertIn("solo ofertas en español", res["motivo"])

    def test_descarte_ingenieria_universitaria(self):
        oferta = {
            "puesto": "Ingeniero/a Civil | Energías Renovables",
            "descripcion": "Buscamos un ingeniero civil para diseño estructural. Imprescindible carrera universitaria o máster en ingeniería de caminos/civil.",
            "ubicacion": "Madrid",
            "modalidad": "REMOTO",
            "horario": "Media jornada tarde"
        }
        res = self.matcher.evaluar_oferta(oferta)
        self.assertEqual(res["clasificacion"], "C")
        self.assertIn("FP Grado Superior", res["motivo"])

    def test_descarte_profesion_no_afin(self):
        oferta = {
            "puesto": "Ortodoncista Clínicas Dentales",
            "descripcion": "Seleccionamos odontólogo especialista en ortodoncia para atención a pacientes en Albacete.",
            "ubicacion": "Albacete",
            "modalidad": "PRESENCIAL",
            "horario": "Turno de tarde"
        }
        res = self.matcher.evaluar_oferta(oferta)
        self.assertEqual(res["clasificacion"], "C")
        self.assertIn("Profesión no afín", res["motivo"])

    def test_acepta_grado_superior_asir_tiempo_parcial(self):
        oferta = {
            "puesto": "Técnico de Sistemas y Redes (ASIR / Grado Superior)",
            "descripcion": "Buscamos técnico informático con Formación Profesional Grado Superior (ASIR) para administración de Linux, Active Directory, soporte técnico y redes. Jornada parcial 20 horas semanales por la tarde. 100% teletrabajo.",
            "ubicacion": "España",
            "modalidad": "REMOTO",
            "horario": "Tiempo parcial"
        }
        res = self.matcher.evaluar_oferta(oferta)
        self.assertEqual(res["clasificacion"], "A")
        self.assertTrue(any("sistemas" in c.lower() for c in res["requisitos_cumple"]))


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

    def test_purgar_base_datos(self):
        h = generar_hash("EmpresaPurga", "PuestoPurga", "https://test.com/purga")
        oferta = {
            "id": h,
            "puesto": "Puesto Purga",
            "empresa": "EmpresaPurga",
            "ubicacion": "Remoto",
            "modalidad": "REMOTO",
            "horario": "FLEXIBLE",
            "salario": "25.000€",
            "url": "https://test.com/purga",
            "fuente": "Test Source",
            "clasificacion": "A",
            "requisitos_cumple": [],
            "requisitos_verificar": [],
            "motivo": "Test",
            "fecha_publicacion": "2026-09-16"
        }
        self.db.guardar_oferta(oferta)
        self.assertTrue(self.db.existe_oferta(h))

        borradas = self.db.purgar()
        self.assertEqual(borradas, 1)
        self.assertFalse(self.db.existe_oferta(h))

    def test_purgar_semanal_si_procede(self):
        from datetime import datetime, timezone, timedelta
        # Cuando se inicializa por primera vez, no purga inmediatamente
        purgado = self.db.purgar_semanal_si_procede(dias=7)
        self.assertFalse(purgado)

        # Si simulamos que la última purga fue hace 8 días
        hace_8_dias = (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
        with self.db._get_connection() as conn:
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO metadata (clave, valor) VALUES ('ultima_purga', ?)", (hace_8_dias,))
            conn.commit()

        # Guardamos una oferta de prueba
        h = generar_hash("EmpresaVieja", "PuestoViejo", "https://test.com/vieja")
        self.db.guardar_oferta({
            "id": h, "puesto": "Viejo", "empresa": "EmpresaVieja", "url": "https://test.com/vieja",
            "clasificacion": "A"
        })
        self.assertTrue(self.db.existe_oferta(h))

        # Al llamar de nuevo, debe detectar que han pasado > 7 días y purgar
        purgado = self.db.purgar_semanal_si_procede(dias=7)
        self.assertTrue(purgado)
        self.assertFalse(self.db.existe_oferta(h))


class TestJobAgentConnectors(unittest.TestCase):
    def test_cinco_portales_configurados(self):
        from job_agent import (
            JobAgent,
            TecnoempleoConnector,
            InfoJobsConnector,
            LinkedInConnector,
            IndeedConnector,
            JobTodayConnector
        )
        agent = JobAgent()
        clases_conectores = [c.__class__.__name__ for c in agent.connectors]
        
        # Verificar que exactamente los 5 portales solicitados están presentes
        self.assertIn("TecnoempleoConnector", clases_conectores)
        self.assertIn("InfoJobsConnector", clases_conectores)
        self.assertIn("LinkedInConnector", clases_conectores)
        self.assertIn("IndeedConnector", clases_conectores)
        self.assertIn("JobTodayConnector", clases_conectores)
        self.assertEqual(len(agent.connectors), 5)


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
            "horario": "Turno de tarde",
            "salario": "32.000€ - 38.000€",
            "requisitos_cumple": ["Aviónica y bancos de prueba", "Diagnóstico de hardware"],
            "requisitos_verificar": [],
            "motivo": "Excelente adecuación a simuladores C-101 y sistemas críticos.",
            "url": "https://ofertas.example.com/simulacion",
            "fuente": "Tecnoempleo"
        }
        html = dispatcher.formatear_oferta_html(oferta)
        self.assertIn("Especialista en Simulación y Electrónica", html)
        self.assertIn("CLASE A", html)
        self.assertIn("Jornada/Turno", html)
        self.assertIn("Turno de tarde", html)
        self.assertIn("Requisitos que cumplo", html)
        self.assertIn("Hash: abc123def456", html)

    def test_formatear_salario_dict_y_string(self):
        sal_dict = {'from': 18000, 'to': 22000, 'currencyCode': 'EUR', 'period': 'YEARLY', 'extraOptions': 'Kilometraje', 'isValid': True}
        res_dict = formatear_salario(sal_dict)
        self.assertIn("18.000 - 22.000 € / año", res_dict)
        self.assertIn("Kilometraje", res_dict)

        sal_str = "{'from': 400, 'currencyCode': 'EUR', 'period': 'MONTHLY', 'extraOptions': '15% comisiones'}"
        res_str = formatear_salario(sal_str)
        self.assertIn("400 € / mes", res_str)
        self.assertIn("15% comisiones", res_str)

    def test_tarjeta_interactiva_y_teclado(self):
        dispatcher = TelegramDispatcher()
        oferta = {
            "id": "07683d50eac0",
            "puesto": "Técnico Informático",
            "empresa": "TecnoEmpresa",
            "clasificacion": "A",
            "ubicacion": "Remoto",
            "modalidad": "REMOTO",
            "horario": "Tiempo parcial tardes",
            "salario": "15.000 € / año",
            "url": "https://ejemplo.com/of1",
            "fuente": "Job Today"
        }
        tarjeta = dispatcher.formatear_oferta_tarjeta(oferta, 0, 5)
        self.assertIn("OFERTA (1 de 5)", tarjeta)
        self.assertIn("Jornada/Turno", tarjeta)
        self.assertIn("Tiempo parcial tardes", tarjeta)

        teclado = dispatcher.construir_teclado_oferta(oferta, 0, 5)
        self.assertEqual(len(teclado), 2)
        # Fila 1: [Inicio, 1 / 5, Siguiente]
        self.assertEqual(teclado[0][1]["text"], "📄 1 / 5")
        self.assertEqual(teclado[0][2]["callback_data"], "of_1")
        # Fila 2: [Ver Oferta, Interesante]
        self.assertEqual(teclado[1][0]["url"], "https://ejemplo.com/of1")
        self.assertEqual(teclado[1][1]["callback_data"], "fav_07683d50")


if __name__ == "__main__":
    unittest.main()
