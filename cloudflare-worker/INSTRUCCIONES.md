# ⚡ Despliegue del Webhook 24/7 en Cloudflare Workers (Gratis y sin tarjeta)

Con este Webhook, tu bot de Telegram **@UbedaBot** responderá al instante las 24 horas del día a cualquier comando (`/ofertas`, `/resumen`, `/buscar`, `/interesantes`) desde tu móvil, **sin necesidad de tener tu ordenador encendido y con coste 0€ de por vida**.

---

## 🚀 Método Rápido (Desde el navegador en 2 minutos)

### Paso 1: Crear tu Worker en Cloudflare
1. Entra en **[cloudflare.com](https://dash.cloudflare.com/)** e inicia sesión (o regístrate gratis si no tienes cuenta; no pide tarjeta de crédito).
2. En el menú lateral izquierdo, pulsa en **Compute (Workers) ➔ Workers & Pages**.
3. Pulsa el botón azul **Create application** (o **Create Worker**).
4. Asigna un nombre a tu worker (por ejemplo: `searchjobs-bot`) y pulsa **Deploy**.

---

### Paso 2: Pegar el código del Worker
1. En la pantalla que aparece tras el despliegue, pulsa en **Edit code** (arriba a la derecha).
2. Borra el código de ejemplo que viene en el editor y pega el contenido completo del archivo [`cloudflare-worker/worker.js`](file:///c:/Proyectos/AlertasEmpleo/cloudflare-worker/worker.js).
3. Pulsa el botón azul **Save and deploy**.

---

### Paso 3: Configurar los Secretos en Cloudflare
1. Vuelve a la pantalla principal de tu Worker y entra en la pestaña **Settings ➔ Variables and Secrets**.
2. En la sección **Secrets and Variables**, pulsa **Add**:
   * **Variable 1 (Secreto):**
     * Type: **Secret**
     * Name: `TELEGRAM_TOKEN`
     * Value: `8841287760:AAGiXoRBUqaKyG70db5T84AtGcMxOJ08pT4`
   * **Variable 2 (Texto plano o secreto):**
     * Type: **Secret** o **Variable**
     * Name: `TELEGRAM_CHAT_ID`
     * Value: `6222316`
   * **Variable 3 (Secreto opcional para /buscar en vivo):**
     * Type: **Secret**
     * Name: `GITHUB_TOKEN`
     * Value: Tu Personal Access Token de GitHub con permiso `workflow` (permite lanzar `/buscar` en GitHub Actions desde tu móvil en cualquier momento)
3. Pulsa **Save and deploy**.

---

### Paso 4: Vincular el Webhook con Telegram (1 clic)

1. Copia la URL pública de tu Worker que aparece arriba (tendrá un aspecto como: `https://searchjobs-bot.<tu-subdominio>.workers.dev`).
2. Abre una pestaña en tu navegador y visita esta dirección (sustituyendo `<TU_URL_DE_WORKER>` por la tuya):

```text
https://api.telegram.org/bot8841287760:AAGiXoRBUqaKyG70db5T84AtGcMxOJ08pT4/setWebhook?url=<TU_URL_DE_WORKER>
```

Telegram te responderá en el navegador con:
```json
{"ok": true, "result": true, "description": "Webhook was set"}
```

---

## 🎯 ¡Listo!
A partir de este momento:
* Puedes apagar tu ordenador.
* Cada vez que abras Telegram y toques **`/ofertas`**, **`/resumen`** o **`/buscar`**, Cloudflare te responderá en menos de 0,05 segundos con las vacantes actualizadas y sus enlaces directos.
