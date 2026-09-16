"""
bot_listener.py - Servicio de escucha continua en tiempo real para el bot de Telegram.
Permite interactuar con el bot al instante desde el móvil:
  • /resumen - Estado de ofertas en base de datos
  • /interesantes - Ver ofertas guardadas
  • /buscar - Ejecutar rastreo de empleo en vivo y recibir novedades
  • /interesante_<hash> - Marcar oferta como interesante
  • /solicitada_<hash> - Marcar oferta como solicitada
  • /descartar_<hash> - Descartar oferta
"""

import os
import sys
import time
import logging
import requests

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Añadir directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from job_agent import JobAgent, DatabaseManager, TelegramDispatcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] BotListener: %(message)s"
)
logger = logging.getLogger("BotListener")

TOKEN = os.environ.get("TELEGRAM_TOKEN", "8841287760:AAGiXoRBUqaKyG70db5T84AtGcMxOJ08pT4")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "6222316")


class BotListener:
    def __init__(self, token: str = TOKEN, chat_id: str = CHAT_ID):
        self.token = token
        self.chat_id = str(chat_id)
        self.agent = JobAgent()
        self.db = self.agent.db
        self.telegram = TelegramDispatcher(token=self.token, chat_id=self.chat_id)
        self.offset = 0

    def procesar_mensaje(self, texto: str, chat_id: str):
        texto = texto.strip().lower()
        logger.info("Comando recibido: %s", texto)

        if texto in ("/start", "/ayuda", "ayuda", "hola"):
            msg = (
                "👋 <b>¡Hola Pedro! Asistente activo en tiempo real.</b>\n\n"
                "Comandos rápidos disponibles:\n"
                "• /resumen — Estadísticas de ofertas en base de datos\n"
                "• /interesantes — Ver tus vacantes guardadas\n"
                "• /buscar — 🚀 Lanzar búsqueda de nuevas ofertas ahora mismo\n"
                "• /interesante_&lt;hash&gt; — Guardar vacante\n"
                "• /solicitada_&lt;hash&gt; — Marcar como enviada\n"
                "• /descartar_&lt;hash&gt; — Descartar vacante"
            )
            self.telegram.enviar_mensaje(msg)

        elif texto.startswith("/resumen"):
            res = self.db.obtener_resumen()
            estados = res.get("estados", {})
            clases = res.get("clases", {})
            lineas_est = "\n".join([f"  • <b>{k}:</b> {v}" for k, v in estados.items()])
            lineas_cl = "\n".join([f"  • <b>Clase {k}:</b> {v}" for k, v in clases.items()])
            msg = (
                f"📊 <b>ESTADO DE TU BASE DE DATOS</b>\n\n"
                f"<b>Por Estado:</b>\n{lineas_est}\n\n"
                f"<b>Por Clasificación:</b>\n{lineas_cl}"
            )
            self.telegram.enviar_mensaje(msg)

        elif texto.startswith("/interesantes"):
            lista = self.db.obtener_interesantes(limite=8)
            if not lista:
                self.telegram.enviar_mensaje("⭐ No tienes ninguna oferta marcada como <b>INTERESANTE</b> actualmente.")
            else:
                bloques = ["⭐ <b>TUS OFERTAS GUARDADAS COMO INTERESANTES:</b>\n"]
                for of in lista:
                    h = of['id'][:8]
                    bloques.append(
                        f"💼 <b>{of['puesto']}</b> ({of['empresa']})\n"
                        f"📍 {of['ubicacion']} | 💰 {of['salario']}\n"
                        f"🔗 <a href='{of['url']}'>Ver Oferta</a>\n"
                        f"⚡ <code>{h}</code>: /solicitada_{h} | /descartar_{h}"
                    )
                self.telegram.enviar_mensaje("\n\n".join(bloques))

        elif texto.startswith("/buscar"):
            self.telegram.enviar_mensaje("🚀 <b>Iniciando búsqueda de empleo en tiempo real...</b>\nConsultando Remotive, Tecnoempleo y WeWorkRemotely. Espera un momento...")
            try:
                self.agent.ejecutar()
                self.telegram.enviar_mensaje("✅ <b>Búsqueda completada.</b> Si se han encontrado nuevas ofertas A o B, las habrás recibido arriba.")
            except Exception as e:
                self.telegram.enviar_mensaje(f"❌ Error durante la búsqueda: {e}")

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

    def iniciar_escucha(self):
        logger.info("Iniciando servicio de escucha continua en Telegram para chat_id %s...", self.chat_id)
        print("=" * 60)
        print("🤖 SERVICIO DE ESCUCHA TELEGRAM ACTIVO")
        print("El bot responderá instantáneamente a tus comandos desde el móvil.")
        print("Pulsa Ctrl+C para detener.")
        print("=" * 60)

        # Limpiar mensajes viejos iniciales
        try:
            url = f"https://api.telegram.org/bot{self.token}/getUpdates"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                updates = r.json().get("result", [])
                if updates:
                    self.offset = updates[-1]["update_id"] + 1
        except Exception:
            pass

        while True:
            try:
                url = f"https://api.telegram.org/bot{self.token}/getUpdates?offset={self.offset}&timeout=20"
                resp = requests.get(url, timeout=25)
                if resp.status_code != 200:
                    time.sleep(3)
                    continue

                updates = resp.json().get("result", [])
                for u in updates:
                    self.offset = u["update_id"] + 1
                    msg = u.get("message", {})
                    texto = msg.get("text", "")
                    chat_id = str(msg.get("chat", {}).get("id", ""))

                    if texto and chat_id == self.chat_id:
                        self.procesar_mensaje(texto, chat_id)

            except requests.exceptions.Timeout:
                continue
            except KeyboardInterrupt:
                print("\n🛑 Servicio detenido por el usuario.")
                break
            except Exception as e:
                logger.error("Error en polling: %s", e)
                time.sleep(3)


if __name__ == "__main__":
    listener = BotListener()
    listener.iniciar_escucha()
