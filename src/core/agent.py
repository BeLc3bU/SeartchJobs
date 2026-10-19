# src/core/agent.py
import sys
import logging
import requests
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from ..db.manager import DatabaseManager
from ..matching.matcher import ProfileMatcher
from ..notifiers.telegram import TelegramDispatcher
from ..connectors.tecnoempleo import TecnoempleoConnector
from ..connectors.infojobs import InfoJobsConnector
from ..connectors.linkedin import LinkedInConnector
from ..connectors.indeed import IndeedConnector
from ..connectors.jobtoday import JobTodayConnector

logger = logging.getLogger("JobAgent.Core")

class JobAgent:
    def __init__(self):
        self.db = DatabaseManager()
        self.matcher = ProfileMatcher()
        self.telegram = TelegramDispatcher()
        
        self.connectors = [
            TecnoempleoConnector(),
            InfoJobsConnector(),
            LinkedInConnector(),
            IndeedConnector(),
            JobTodayConnector()
        ]

    def ejecutar(self):
        logger.info("=== INICIANDO AGENTE DE BÚSQUEDA DE EMPLEO ===")
        ahora_str = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

        eliminadas = self.db.purgar_ofertas_antiguas(dias=60, conservar_interesantes=True)
        if eliminadas > 0:
            logger.info("Mantenimiento: %d ofertas de más de 60 días no interesantes eliminadas.", eliminadas)


        self.db.reclasificar_bd(self.matcher)

        todas_ofertas = []
        for conn in self.connectors:
            try:
                items = conn.fetch()
                todas_ofertas.extend(items)
            except Exception as e:
                logger.error("Error en conector %s: %s", conn.__class__.__name__, e)

        logger.info("Total de ofertas crudas recopiladas: %d", len(todas_ofertas))

        nuevas_procesadas = 0
        ofertas_notificar = []

        for raw_job in todas_ofertas:
            job_id = raw_job["id"]
            
            if self.db.existe_oferta(job_id):
                continue

            evaluacion = self.matcher.evaluar_oferta(raw_job)
            
            raw_job["clasificacion"] = evaluacion["clasificacion"]
            raw_job["motivo"] = evaluacion["motivo"]
            raw_job["requisitos_cumple"] = evaluacion["requisitos_cumple"]
            raw_job["requisitos_verificar"] = evaluacion["requisitos_verificar"]
            raw_job["fecha_procesada"] = datetime.now(timezone.utc).isoformat()

            self.db.guardar_oferta(raw_job)
            nuevas_procesadas += 1

            if raw_job["clasificacion"] in ("A", "B"):
                ofertas_notificar.append(raw_job)

        logger.info("Nuevas ofertas insertadas en BD: %d. Relevantes (A/B): %d.", nuevas_procesadas, len(ofertas_notificar))

        self.db.exportar_json(solo_nuevas_horas=48)

        if ofertas_notificar:
            total_n = len(ofertas_notificar)
            cabecera = (
                f"🎯 <b>REPORTE DIARIO DE EMPLEO PERSONALIZADO</b>\n"
                f"📅 <i>{ahora_str}</i>\n"
                f"👤 <b>Candidato:</b> Pedro Úbeda Sánchez\n\n"
                f"Se han detectado <b>{total_n} vacante{'s' if total_n > 1 else ''}</b> con encaje estricto en turno de tarde / tiempo parcial / fin de semana.\n"
                f"────────────────────────\n"
                f"👇 <i>Navega por las vacantes con los botones interactivos a continuación:</i>"
            )
            self.telegram.enviar_mensaje(cabecera)

            primera_of = ofertas_notificar[0]
            card_html = self.telegram.formatear_oferta_tarjeta(primera_of, 0, total_n)
            teclado = self.telegram.construir_teclado_oferta(primera_of, 0, total_n)
            self.telegram.enviar_mensaje(card_html, inline_keyboard=teclado)
        else:
            msg_tranquilidad = (
                f"✅ <b>Agente de Empleo: Búsqueda Diaria Finalizada</b>\n"
                f"📅 <i>{ahora_str}</i>\n\n"
                f"No se han detectado nuevas ofertas con encaje <b>Clase A</b> o <b>Clase B</b> en las últimas 24 horas "
                f"que cumplan las restricciones horarias y geográficas (Turno de tarde, Tiempo parcial o Fines de semana en Remoto España o Albacete/Hellín).\n\n"
                f"Base de datos SQLite y ofertas.json actualizadas correctamente."
            )
            self.telegram.enviar_mensaje(msg_tranquilidad)

        logger.info("=== EJECUCIÓN FINALIZADA SATISFACTORIAMENTE ===")

    def procesar_comandos_telegram(self):
        if not self.telegram.esta_configurado():
            return

        try:
            url = f"https://api.telegram.org/bot{self.telegram.token}/getUpdates"
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                return

            updates = resp.json().get("result", [])
            if not updates:
                return

            max_update_id = 0
            for u in updates:
                up_id = u.get("update_id", 0)
                if up_id > max_update_id:
                    max_update_id = up_id

                msg = u.get("message", {})
                texto = (msg.get("text") or "").strip().lower()
                chat_id = str(msg.get("chat", {}).get("id", ""))

                if not texto or chat_id != str(self.telegram.chat_id):
                    continue

                logger.info("Comando recibido en Telegram: %s", texto)

                if texto.startswith("/start") or texto.startswith("/ayuda"):
                    respuesta = (
                        "👋 <b>Hola Pedro. Soy tu Agente de Búsqueda de Empleo.</b>\n\n"
                        "Comandos disponibles:\n"
                        "• /ofertas - Explorar todas las ofertas interactivamente (Anterior/Siguiente)\n"
                        "• /resumen - Conteo de ofertas por estado y clase\n"
                        "• /interesantes - Ver tus ofertas guardadas\n"
                        "• /interesante_&lt;hash&gt; - Marcar oferta como interesante\n"
                        "• /solicitada_&lt;hash&gt; - Marcar oferta como solicitada/enviada\n"
                        "• /descartar_&lt;hash&gt; - Descartar oferta\n"
                        "• /buscar - Ejecutar búsqueda inmediata de ofertas"
                    )
                    self.telegram.enviar_mensaje(respuesta)

                elif texto.startswith("/ofertas"):
                    ofertas = self.db.obtener_nuevas_relevantes(horas=720)
                    if not ofertas:
                        self.telegram.enviar_mensaje("⚠️ No se encontraron ofertas activas en la base de datos.")
                    else:
                        of = ofertas[0]
                        total = len(ofertas)
                        h = of['id'][:8]
                        card = self.telegram.formatear_oferta_html(of)
                        keyboard = [
                            [
                                {"text": "⏮️ Inicio", "callback_data": "of_noop"},
                                {"text": f"📄 1 / {total}", "callback_data": "of_noop"},
                                {"text": "Siguiente ➡️" if total > 1 else "Fin ⏭️", "callback_data": "of_1" if total > 1 else "of_noop"}
                            ],
                            [
                                {"text": "🔗 Ver Oferta", "url": of['url']},
                                {"text": "⭐ Interesante", "callback_data": f"fav_{h}"}
                            ]
                        ]
                        self.telegram.enviar_mensaje(card, inline_keyboard=keyboard)

                elif texto.startswith("/resumen"):
                    res = self.db.obtener_resumen()
                    estados = res.get("estados", {})
                    clases = res.get("clases", {})
                    lineas_est = "\n".join([f"  • <b>{k}:</b> {v}" for k, v in estados.items()])
                    lineas_cl = "\n".join([f"  • <b>Clase {k}:</b> {v}" for k, v in clases.items()])
                    respuesta = (
                        f"📊 <b>RESUMEN DE LA BASE DE DATOS</b>\n\n"
                        f"<b>Por Estado:</b>\n{lineas_est}\n\n"
                        f"<b>Por Clasificación:</b>\n{lineas_cl}"
                    )
                    self.telegram.enviar_mensaje(respuesta)

                elif texto.startswith("/interesantes"):
                    lista = self.db.obtener_interesantes(limite=5)
                    if not lista:
                        self.telegram.enviar_mensaje("⭐ No tienes ninguna oferta marcada como <b>INTERESANTE</b> actualmente.")
                    else:
                        bloques = ["⭐ <b>TUS OFERTAS INTERESANTES GUARDADAS:</b>\n"]
                        for of in lista:
                            bloques.append(
                                f"💼 <b>{of['puesto']}</b> ({of['empresa']})\n"
                                f"📍 {of['ubicacion']} | 💰 {of['salario']}\n"
                                f"🔗 <a href='{of['url']}'>Ver Oferta</a>\n"
                                f"🆔 <code>{of['id'][:8]}</code> | /solicitada_{of['id'][:8]} | /descartar_{of['id'][:8]}"
                            )
                        self.telegram.enviar_mensaje("\n\n".join(bloques))

                elif texto.startswith("/interesante_"):
                    h = texto.replace("/interesante_", "").strip()
                    of = self.db.actualizar_estado_oferta(h, "INTERESANTE")
                    if of:
                        self.telegram.enviar_mensaje(f"⭐ Oferta <b>{of['puesto']}</b> ({of['empresa']}) marcada como <b>INTERESANTE</b>.")
                    else:
                        self.telegram.enviar_mensaje(f"⚠️ No se encontró la oferta con hash '{h}'.")

                elif texto.startswith("/solicitada_"):
                    h = texto.replace("/solicitada_", "").strip()
                    of = self.db.actualizar_estado_oferta(h, "SOLICITADA")
                    if of:
                        self.telegram.enviar_mensaje(f"📨 Oferta <b>{of['puesto']}</b> ({of['empresa']}) marcada como <b>SOLICITADA / CV ENVIADO</b>.")
                    else:
                        self.telegram.enviar_mensaje(f"⚠️ No se encontró la oferta con hash '{h}'.")

                elif texto.startswith("/descartar_"):
                    h = texto.replace("/descartar_", "").strip()
                    of = self.db.actualizar_estado_oferta(h, "DESCARTADA")
                    if of:
                        self.telegram.enviar_mensaje(f"🗑️ Oferta <b>{of['puesto']}</b> ({of['empresa']}) <b>DESCARTADA</b>.")
                    else:
                        self.telegram.enviar_mensaje(f"⚠️ No se encontró la oferta con hash '{h}'.")

                elif texto.startswith("/buscar"):
                    self.telegram.enviar_mensaje("🚀 <b>Iniciando búsqueda de empleo en tiempo real...</b>\nConsultando los 5 portales de empleo. Espera unos instantes...")
                    self.ejecutar()

            if max_update_id > 0:
                requests.get(f"{url}?offset={max_update_id + 1}", timeout=10)

        except Exception as e:
            logger.error("Error al procesar comandos de Telegram: %s", e)
