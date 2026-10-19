# src/notifiers/telegram.py
import os
import json
import logging
import requests
from typing import List, Dict, Any, Optional
from ..matching.normalizer import formatear_salario

logger = logging.getLogger("JobAgent.Telegram")

class TelegramDispatcher:
    """Envío de alertas formateadas mediante la API REST de Telegram."""
    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        self.token = token or os.environ.get("TELEGRAM_TOKEN", "8841287760:AAGiXoRBUqaKyG70db5T84AtGcMxOJ08pT4")
        self.chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID", "6222316")
        self.api_url = f"https://api.telegram.org/bot{self.token}/sendMessage" if self.token else None

    def esta_configurado(self) -> bool:
        return bool(self.token and self.chat_id)

    def enviar_mensaje(self, texto_html: str, inline_keyboard: Optional[List[List[Dict[str, str]]]] = None) -> bool:
        if not self.esta_configurado():
            logger.warning("Telegram no está configurado (faltan TELEGRAM_TOKEN o TELEGRAM_CHAT_ID). Mensaje en log:\n%s", texto_html)
            return False

        payload = {
            "chat_id": self.chat_id,
            "text": texto_html,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        if inline_keyboard:
            payload["reply_markup"] = {"inline_keyboard": inline_keyboard}

        try:
            resp = requests.post(self.api_url, json=payload, timeout=20)
            if resp.status_code == 200:
                logger.info("Mensaje enviado con éxito a Telegram.")
                return True
            else:
                logger.error("Error al enviar a Telegram (status %d): %s", resp.status_code, resp.text)
                return False
        except Exception as e:
            logger.error("Excepción de conexión con Telegram: %s", e)
            return False

    def enviar_bloques(self, bloques: List[str]):
        """Envía una lista de bloques HTML asegurando el límite de 4096 caracteres de Telegram."""
        if not bloques:
            return

        mensaje_actual = ""
        for bloque in bloques:
            if len(mensaje_actual) + len(bloque) + 2 > 4000:
                self.enviar_mensaje(mensaje_actual.strip())
                mensaje_actual = bloque + "\n\n"
            else:
                mensaje_actual += bloque + "\n\n"

        if mensaje_actual.strip():
            self.enviar_mensaje(mensaje_actual.strip())

    def editar_mensaje(self, message_id: int, texto_html: str, inline_keyboard: Optional[List[List[Dict[str, str]]]] = None) -> bool:
        """Edita un mensaje existente en Telegram de forma interactiva."""
        if not self.esta_configurado():
            return False
        url = f"https://api.telegram.org/bot{self.token}/editMessageText"
        payload = {
            "chat_id": self.chat_id,
            "message_id": message_id,
            "text": texto_html,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        if inline_keyboard:
            payload["reply_markup"] = {"inline_keyboard": inline_keyboard}

        try:
            resp = requests.post(url, json=payload, timeout=15)
            if resp.status_code == 200:
                return True
            else:
                logger.error("Error al editar mensaje en Telegram (%d): %s", resp.status_code, resp.text)
                return False
        except Exception as e:
            logger.error("Excepción al editar mensaje en Telegram: %s", e)
            return False

    def responder_callback(self, query_id: str, texto: Optional[str] = None, alert: bool = False) -> bool:
        """Confirma a Telegram la recepción de una pulsación de botón callback."""
        if not self.esta_configurado():
            return False
        url = f"https://api.telegram.org/bot{self.token}/answerCallbackQuery"
        payload = {"callback_query_id": query_id}
        if texto:
            payload["text"] = texto
            payload["show_alert"] = alert

        try:
            resp = requests.post(url, json=payload, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            logger.error("Excepción al responder callback query: %s", e)
            return False

    def formatear_oferta_html(self, oferta: Dict[str, Any]) -> str:
        """Formatea una vacante individual con la estructura exigida."""
        clase = oferta.get("clasificacion", "A")
        badge = "🟢 <b>CLASE A (Encaje Directo)</b>" if clase == "A" else "🟡 <b>CLASE B (Encaje Potencial)</b>"
        
        req_cumple = oferta.get("requisitos_cumple", [])
        if isinstance(req_cumple, str):
            try:
                req_cumple = json.loads(req_cumple)
            except Exception:
                req_cumple = [req_cumple]

        req_verificar = oferta.get("requisitos_verificar", [])
        if isinstance(req_verificar, str):
            try:
                req_verificar = json.loads(req_verificar)
            except Exception:
                req_verificar = [req_verificar]

        cumple_html = ""
        if req_cumple:
            items = "".join([f"  • {c}\n" for c in req_cumple])
            cumple_html = f"\n<b>✅ Requisitos que cumplo:</b>\n{items}"

        verificar_html = ""
        if req_verificar:
            items = "".join([f"  • {v}\n" for v in req_verificar])
            verificar_html = f"\n<b>🔍 Requisitos a verificar:</b>\n{items}"
        elif clase == "B":
            verificar_html = "\n<b>🔍 Requisitos a verificar:</b>\n  • Validar horario presencial o acreditación civil específica.\n"

        motivo = oferta.get("motivo", "")
        motivo_html = f"\n<b>💡 Por qué merece atención:</b>\n<i>{motivo}</i>\n" if motivo else ""
        h = oferta.get('id', '')
        salario = formatear_salario(oferta.get('salario', 'No especificado'))
        horario = oferta.get('horario', 'No especificado')

        bloque = (
            f"💼 <b>{oferta.get('puesto', 'Puesto')}</b>\n"
            f"🏢 <b>Empresa:</b> {oferta.get('empresa', 'No indicada')}\n"
            f"🏷️ <b>Evaluación:</b> {badge}\n"
            f"📍 <b>Ubicación/Modalidad:</b> {oferta.get('ubicacion', '')} ({oferta.get('modalidad', '')})\n"
            f"⏰ <b>Jornada/Turno:</b> {horario}\n"
            f"💰 <b>Salario:</b> {salario}\n"
            f"{cumple_html}"
            f"{verificar_html}"
            f"{motivo_html}"
            f"🔗 <a href='{oferta.get('url', '#')}'>Ver oferta original en {oferta.get('fuente', 'Portal')}</a>\n"
            f"🆔 <code>Hash: {h}</code>\n"
            f"⚡ <b>Acciones:</b> /interesante_{h[:8]} | /solicitada_{h[:8]} | /descartar_{h[:8]}"
        )
        return bloque

    def formatear_oferta_tarjeta(self, oferta: Dict[str, Any], index: int, total: int) -> str:
        """Formatea una vacante individual para la tarjeta interactiva paginada con botones."""
        clase = oferta.get("clasificacion", "A")
        badge = "🟢 <b>CLASE A (Encaje Directo)</b>" if clase == "A" else "🟡 <b>CLASE B (Encaje Potencial)</b>"
        
        req_cumple = oferta.get("requisitos_cumple", [])
        if isinstance(req_cumple, str):
            try:
                req_cumple = json.loads(req_cumple)
            except Exception:
                req_cumple = [req_cumple]
        cumple_items = req_cumple[:3] if req_cumple else []
        cumple_html = ""
        if cumple_items:
            items = "".join([f"  • {c}\n" for c in cumple_items])
            cumple_html = f"\n<b>✅ Requisitos que cumplo:</b>\n{items}\n"

        motivo = oferta.get("motivo", "")
        motivo_html = f"\n<b>💡 Por qué merece atención:</b>\n<i>{motivo}</i>\n" if motivo else ""
        h = (oferta.get('id') or '')[:8]
        fuente = oferta.get('fuente', 'Portal')
        salario = formatear_salario(oferta.get('salario', 'No especificado'))
        horario = oferta.get('horario', 'Tiempo parcial / tarde / fin de semana')

        card = (
            f"🎯 <b>OFERTA ({index + 1} de {total})</b> | {badge}\n"
            f"💼 <b>{oferta.get('puesto', 'Sin título')}</b>\n"
            f"🏢 <b>Empresa:</b> {oferta.get('empresa', 'Confidencial')}\n"
            f"📍 <b>Ubicación:</b> {oferta.get('ubicacion', '')} ({oferta.get('modalidad', 'No especificada')})\n"
            f"⏰ <b>Jornada/Turno:</b> {horario}\n"
            f"💰 <b>Salario:</b> {salario}\n"
            f"{cumple_html}"
            f"{motivo_html}"
            f"🔗 <b>Fuente:</b> {fuente}\n"
            f"🆔 <code>{h}</code>"
        )
        return card

    def construir_teclado_oferta(self, oferta: Dict[str, Any], index: int, total: int) -> List[List[Dict[str, str]]]:
        """Construye los botones de paginación e interactividad (Anterior, Siguiente, Enlace, Interesante)."""
        nav_row = []
        if index > 0:
            nav_row.append({"text": "⬅️ Anterior", "callback_data": f"of_{index - 1}"})
        else:
            nav_row.append({"text": "⏮️ Inicio", "callback_data": "of_noop"})

        nav_row.append({"text": f"📄 {index + 1} / {total}", "callback_data": "of_noop"})

        if index < total - 1:
            nav_row.append({"text": "Siguiente ➡️", "callback_data": f"of_{index + 1}"})
        else:
            nav_row.append({"text": "Fin ⏭️", "callback_data": "of_noop"})

        h = (oferta.get('id') or '')[:8]
        actions_row = []
        if oferta.get("url"):
            actions_row.append({"text": "🔗 Ver Oferta", "url": oferta["url"]})
        actions_row.append({"text": "⭐ Interesante", "callback_data": f"fav_{h}"})

        return [nav_row, actions_row]
