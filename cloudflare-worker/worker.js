/**
 * worker.js - Cloudflare Worker Serverless para @UbedaBot
 * Responde 24/7 de forma instantánea a los comandos de Telegram con coste 0€.
 */

const GITHUB_RAW_URL = "https://raw.githubusercontent.com/BeLc3bU/SeartchJobs/main/data/ofertas.json";

export default {
  async fetch(request, env, ctx) {
    // Si es GET, comprobación de estado de salud
    if (request.method === "GET") {
      return new Response("🤖 SearchJobs Telegram Webhook está activo en Cloudflare Workers.", {
        headers: { "content-type": "text/plain; charset=utf-8" },
      });
    }

    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    try {
      const update = await request.json();
      const message = update.message || update.edited_message;
      if (!message || !message.text) {
        return new Response("OK");
      }

      const chatId = String(message.chat.id);
      const text = message.text.trim();
      const token = env.TELEGRAM_TOKEN;
      const allowedChatId = String(env.TELEGRAM_CHAT_ID || "6222316");

      // Seguridad: solo responder a Pedro
      if (chatId !== allowedChatId) {
        return new Response("Unauthorized", { status: 403 });
      }

      // Procesar comando
      await handleCommand(text, chatId, token, env);

      return new Response("OK");
    } catch (err) {
      console.error("Error procesando webhook:", err);
      return new Response("Error", { status: 500 });
    }
  },
};

async function sendTelegramMessage(token, chatId, textHtml) {
  const url = `https://api.telegram.org/bot${token}/sendMessage`;
  const payload = {
    chat_id: chatId,
    text: textHtml,
    parse_mode: "HTML",
    disable_web_page_preview: false,
  };
  await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

async function handleCommand(text, chatId, token, env) {
  const t = text.toLowerCase();

  if (t === "/start" || t === "/ayuda" || t === "ayuda" || t === "hola") {
    const msg = 
      `👋 <b>¡Hola Pedro! Asistente activo 24/7 en Cloudflare Workers.</b>\n\n` +
      `Comandos disponibles en tiempo real:\n` +
      `• /ofertas — 📋 Ver las mejores ofertas activas con enlaces directos\n` +
      `• /resumen — 📊 Estadísticas de ofertas en base de datos\n` +
      `• /interesantes — ⭐ Ver tus vacantes guardadas\n` +
      `• /buscar — 🚀 Lanzar rastreo en vivo en GitHub Actions\n` +
      `• /interesante_&lt;hash&gt; — Guardar vacante\n` +
      `• /solicitada_&lt;hash&gt; — Marcar como enviada\n` +
      `• /descartar_&lt;hash&gt; — Descartar vacante`;
    await sendTelegramMessage(token, chatId, msg);
    return;
  }

  // Cargar ofertas desde GitHub
  let ofertas = [];
  try {
    const res = await fetch(`${GITHUB_RAW_URL}?t=${Date.now()}`);
    if (res.ok) {
      ofertas = await res.json();
    }
  } catch (e) {
    console.error("Error al cargar ofertas.json:", e);
  }

  if (t.startsWith("/resumen")) {
    const total = ofertas.length;
    const claseA = ofertas.filter(o => o.clasificacion === "A").length;
    const claseB = ofertas.filter(o => o.clasificacion === "B").length;
    const interesantes = ofertas.filter(o => o.estado === "INTERESANTE").length;
    const nuevas = ofertas.filter(o => o.estado === "NUEVA").length;

    const msg = 
      `📊 <b>ESTADO DE LA BASE DE DATOS</b>\n\n` +
      `• <b>Total ofertas activas:</b> ${total}\n` +
      `  - 🟢 Clase A (Encaje directo): ${claseA}\n` +
      `  - 🟡 Clase B (Encaje potencial): ${claseB}\n\n` +
      `• <b>Por Estado:</b>\n` +
      `  - 🆕 Nuevas: ${nuevas}\n` +
      `  - ⭐ Interesantes: ${interesantes}\n\n` +
      `👉 <i>Escribe /ofertas para ver las mejores vacantes con sus enlaces.</i>`;
    await sendTelegramMessage(token, chatId, msg);
    return;
  }

  if (t.startsWith("/ofertas") || t.startsWith("/ultimas")) {
    if (ofertas.length === 0) {
      await sendTelegramMessage(token, chatId, "⚠️ No se han encontrado ofertas activas en el repositorio actualmente.");
      return;
    }

    const mejores = ofertas.slice(0, 4);
    await sendTelegramMessage(token, chatId, `🎯 <b>ÚLTIMAS ${mejores.length} OFERTAS DESTACADAS CON ENLACE:</b>\n────────────────────────`);

    for (const of of mejores) {
      const badge = of.clasificacion === "A" ? "🟢 <b>CLASE A (Encaje Directo)</b>" : "🟡 <b>CLASE B (Encaje Potencial)</b>";
      const cumpleList = (of.requisitos_cumple || []).slice(0, 3).map(c => `  • ${c}`).join("\n");
      const cumpleHtml = cumpleList ? `\n<b>✅ Requisitos que cumplo:</b>\n${cumpleList}\n` : "";
      const h = of.id ? of.id.substring(0, 8) : "";

      const card = 
        `💼 <b>${of.puesto}</b>\n` +
        `🏢 <b>Empresa:</b> ${of.empresa}\n` +
        `🏷️ <b>Evaluación:</b> ${badge}\n` +
        `📍 <b>Modalidad:</b> ${of.ubicacion} (${of.modalidad})\n` +
        `💰 <b>Salario:</b> ${of.salario}\n` +
        cumpleHtml +
        `🔗 <a href="${of.url}">👉 Ver oferta original en ${of.fuente || 'Portal'}</a>\n` +
        `🆔 <code>${h}</code> | /interesante_${h} | /solicitada_${h}`;

      await sendTelegramMessage(token, chatId, card);
    }
    return;
  }

  if (t.startsWith("/interesantes")) {
    const favs = ofertas.filter(o => o.estado === "INTERESANTE");
    if (favs.length === 0) {
      await sendTelegramMessage(token, chatId, "⭐ No tienes ninguna vacante guardada como <b>INTERESANTE</b>.\nEscribe /ofertas para ver vacantes activas.");
      return;
    }

    let msg = `⭐ <b>TUS VACANTES FAVORITAS (${favs.length}):</b>\n\n`;
    for (const of of favs.slice(0, 5)) {
      const h = of.id ? of.id.substring(0, 8) : "";
      msg += `💼 <b>${of.puesto}</b> (${of.empresa})\n` +
             `🔗 <a href="${of.url}">Ver Oferta</a> | <code>${h}</code>\n\n`;
    }
    await sendTelegramMessage(token, chatId, msg);
    return;
  }

  if (t.startsWith("/buscar")) {
    // Si tenemos GITHUB_TOKEN configurado, podemos disparar el workflow de GitHub Actions
    if (env.GITHUB_TOKEN) {
      try {
        const ghUrl = "https://api.github.com/repos/BeLc3bU/SeartchJobs/actions/workflows/empleo.yml/dispatches";
        const ghResp = await fetch(ghUrl, {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${env.GITHUB_TOKEN}`,
            "Accept": "application/vnd.github+json",
            "User-Agent": "Cloudflare-Worker-SearchJobs",
          },
          body: JSON.stringify({ ref: "main" }),
        });
        if (ghResp.status === 204) {
          await sendTelegramMessage(token, chatId, "🚀 <b>Búsqueda en tiempo real lanzada en GitHub Actions.</b>\nEl agente está rastreando Remotive, Tecnoempleo y WeWorkRemotely. Recibirás las novedades en este chat en unos 30 segundos.");
          return;
        }
      } catch (e) {
        console.error("Error disparando GitHub Actions:", e);
      }
    }
    
    await sendTelegramMessage(
      token, 
      chatId, 
      "🚀 <b>Búsqueda solicitada.</b>\nEl rastreador corre automáticamente cada mañana a las 08:00. Mientras tanto, puedes explorar las vacantes activas escribiendo <b>/ofertas</b>."
    );
    return;
  }

  // Si no coincide con ninguno
  await sendTelegramMessage(token, chatId, `❓ Comando no reconocido: <code>${text}</code>\nEscribe /ayuda para ver los comandos disponibles.`);
}
