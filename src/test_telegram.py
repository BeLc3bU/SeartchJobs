"""
test_telegram.py - Script de verificación y obtención automática de TELEGRAM_CHAT_ID.

Uso:
  python src/test_telegram.py
  python src/test_telegram.py <TELEGRAM_TOKEN>
  python src/test_telegram.py <TELEGRAM_TOKEN> <TELEGRAM_CHAT_ID>
"""

import sys
import os
import requests

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def verificar_telegram(token: str, chat_id: str = None):
    print(f"🔍 Comprobando bot con token: {token[:10]}...{token[-5:] if len(token) > 15 else ''}")
    
    # 1. Comprobar identidad del bot (getMe)
    try:
        url_me = f"https://api.telegram.org/bot{token}/getMe"
        resp_me = requests.get(url_me, timeout=10)
        data_me = resp_me.json()
        if not data_me.get("ok"):
            print(f"❌ Error al autenticar bot: {data_me.get('description', 'Token inválido')}")
            return
        bot_info = data_me["result"]
        print(f"✅ Bot autenticado correctamente:")
        print(f"   • Nombre:   {bot_info.get('first_name')}")
        print(f"   • Username: @{bot_info.get('username')}")
    except Exception as e:
        print(f"❌ Error de red al conectar con Telegram: {e}")
        return

    # 2. Si no se proporcionó chat_id, buscarlo en getUpdates
    if not chat_id:
        print("\n📥 Buscando mensajes recientes enviados al bot (getUpdates)...")
        try:
            url_updates = f"https://api.telegram.org/bot{token}/getUpdates"
            resp_up = requests.get(url_updates, timeout=10)
            data_up = resp_up.json()
            updates = data_up.get("result", [])
            
            if not updates:
                print("⚠️ No se ha detectado ningún mensaje aún.")
                print(f"👉 Abre Telegram, entra en tu bot @{bot_info.get('username')} y pulsa 'INICIAR' (o envíale /start).")
                print("   Luego vuelve a ejecutar este script para capturar tu Chat ID.")
                return

            # Extraer el último chat_id
            ultimo = updates[-1]
            msg = ultimo.get("message") or ultimo.get("my_chat_member") or {}
            chat = msg.get("chat", {})
            chat_id = str(chat.get("id"))
            remitente = chat.get("username") or chat.get("first_name") or "Usuario"

            print(f"🎉 ¡Mensaje /start detectado!")
            print(f"   • Remitente:        {remitente}")
            print(f"   • TELEGRAM_CHAT_ID: {chat_id}")
            print(f"\nGuarda este valor como secreto en GitHub con el nombre: TELEGRAM_CHAT_ID")
        except Exception as e:
            print(f"❌ Error al consultar getUpdates: {e}")
            return

    # 3. Enviar mensaje de prueba
    if chat_id:
        print(f"\n📤 Enviando mensaje de prueba a Chat ID: {chat_id}...")
        url_send = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": (
                "🤖 <b>¡Conexión establecida con éxito!</b>\n\n"
                "Hola Pedro, tu bot de alertas de empleo está correctamente vinculado con tu cuenta de Telegram.\n"
                "A partir de ahora, recibirás aquí el reporte diario automático a las 08:00 hora española."
            ),
            "parse_mode": "HTML"
        }
        try:
            resp_send = requests.post(url_send, json=payload, timeout=10)
            if resp_send.status_code == 200:
                print("✅ ¡Mensaje enviado con éxito! Revisa tu chat de Telegram.")
            else:
                print(f"❌ Error al enviar mensaje: {resp_send.text}")
        except Exception as e:
            print(f"❌ Error de red al enviar mensaje: {e}")


def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if len(sys.argv) > 1:
        token = sys.argv[1]
    if len(sys.argv) > 2:
        chat_id = sys.argv[2]

    if not token:
        print("ℹ️ Introduce tu TELEGRAM_TOKEN (obtenido de @BotFather):")
        token = input("Token: ").strip()

    if not token:
        print("❌ Token no proporcionado. Cancelando.")
        sys.exit(1)

    verificar_telegram(token, chat_id)


if __name__ == "__main__":
    main()
