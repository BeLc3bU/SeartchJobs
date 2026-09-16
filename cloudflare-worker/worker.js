/**
 * worker.js - Cloudflare Worker Serverless para @UbedaBot
 * Responde 24/7 de forma instantánea a los comandos de Telegram con coste 0€.
 * Soporta navegación interactiva de ofertas con botones Anterior / Siguiente.
 */

const GITHUB_RAW_URL = "https://raw.githubusercontent.com/BeLc3bU/SeartchJobs/main/data/ofertas.json";

export default {
  async fetch(request, env, ctx) {
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
      const token = env.TELEGRAM_TOKEN;
      const allowedChatId = String(env.TELEGRAM_CHAT_ID || "6222316");

      // 1. Manejo de pulsaciones de botones (Callback Query)
      if (update.callback_query) {
        const cq = update.callback_query;
        const chatId = String(cq.message?.chat?.id || "");
        const messageId = cq.message?.message_id;
        const data = cq.data || "";
        const queryId = cq.id;

        if (chatId !== allowedChatId) {
          return new Response("Unauthorized", { status: 403 });
        }

        await handleCallbackQuery(queryId, chatId, messageId, data, token, env);
        return new Response("OK");
      }

      // 2. Manejo de mensajes de texto normales
      const message = update.message || update.edited_message;
      if (!message || !message.text) {
        return new Response("OK");
      }

      const chatId = String(message.chat.id);
      const text = message.text.trim();

      if (chatId !== allowedChatId) {
        return new Response("Unauthorized", { status: 403 });
      }

      await handleCommand(text, chatId, token, env);
      return new Response("OK");
    } catch (err) {
      console.error("Error procesando webhook:", err);
      return new Response("Error", { status: 500 });
    }
  },
};

/**
 * Envía un mensaje nuevo a Telegram
 */
async function sendTelegramMessage(token, chatId, textHtml, replyMarkup = null) {
  const url = `https://api.telegram.org/bot${token}/sendMessage`;
  const payload = {
    chat_id: chatId,
    text: textHtml,
    parse_mode: "HTML",
    disable_web_page_preview: false,
  };
  if (replyMarkup) {
    payload.reply_markup = replyMarkup;
  }
  return await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

/**
 * Edita un mensaje existente en Telegram de forma interactiva
 */
async function editTelegramMessage(token, chatId, messageId, textHtml, replyMarkup = null) {
  const url = `https://api.telegram.org/bot${token}/editMessageText`;
  const payload = {
    chat_id: chatId,
    message_id: messageId,
    text: textHtml,
    parse_mode: "HTML",
    disable_web_page_preview: false,
  };
  if (replyMarkup) {
    payload.reply_markup = replyMarkup;
  }
  return await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

/**
 * Confirma a Telegram la pulsación de un botón (elimina el reloj de carga)
 */
async function answerCallbackQuery(token, queryId, text = null, showAlert = false) {
  const url = `https://api.telegram.org/bot${token}/answerCallbackQuery`;
  const payload = { callback_query_id: queryId };
  if (text) {
    payload.text = text;
    payload.show_alert = showAlert;
  }
  return await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

/**
 * Carga las ofertas activas sincronizadas desde GitHub Raw
 */
async function fetchOfertas() {
  try {
    const res = await fetch(`${GITHUB_RAW_URL}?t=${Date.now()}`);
    if (res.ok) {
      return await res.json();
    }
  } catch (e) {
    console.error("Error al cargar ofertas.json:", e);
  }
  return [];
}

/**
 * Construye el contenido formateado de una oferta individual
 */
function formatOfferCard(of, index, total) {
  const badge = of.clasificacion === "A" ? "🟢 <b>CLASE A (Encaje Directo)</b>" : "🟡 <b>CLASE B (Encaje Potencial)</b>";
  const cumpleList = (of.requisitos_cumple || []).slice(0, 3).map(c => `  • ${c}`).join("\n");
  const cumpleHtml = cumpleList ? `\n<b>✅ Requisitos que cumplo:</b>\n${cumpleList}\n` : "";
  const h = of.id ? of.id.substring(0, 8) : "";
  const fuente = of.fuente || "Portal";
  const motivo = of.motivo ? `\n<b>💡 Por qué merece atención:</b>\n<i>${of.motivo}</i>\n` : "";

  return (
    `🎯 <b>OFERTA (${index + 1} de ${total})</b> | ${badge}\n` +
    `💼 <b>${of.puesto}</b>\n` +
    `🏢 <b>Empresa:</b> ${of.empresa}\n` +
    `📍 <b>Ubicación:</b> ${of.ubicacion} (${of.modalidad || 'No especificada'})\n` +
    `💰 <b>Salario:</b> ${of.salario || 'No especificado'}\n` +
    cumpleHtml +
    motivo +
    `🔗 <b>Fuente:</b> ${fuente}\n` +
    `🆔 <code>${h}</code>`
  );
}

/**
 * Construye los botones de paginación interactiva
 */
function buildOfferKeyboard(of, index, total) {
  const navRow = [];

  // Botón Anterior
  if (index > 0) {
    navRow.push({ text: "⬅️ Anterior", callback_data: `of_${index - 1}` });
  } else {
    navRow.push({ text: "⏮️ Inicio", callback_data: `of_noop` });
  }

  // Indicador de página
  navRow.push({ text: `📄 ${index + 1} / ${total}`, callback_data: `of_noop` });

  // Botón Siguiente
  if (index < total - 1) {
    navRow.push({ text: "Siguiente ➡️", callback_data: `of_${index + 1}` });
  } else {
    navRow.push({ text: "Fin ⏭️", callback_data: `of_noop` });
  }

  const h = of.id ? of.id.substring(0, 8) : "";
  const actionsRow = [];
  if (of.url) {
    actionsRow.push({ text: "🔗 Ver Oferta", url: of.url });
  }
  actionsRow.push({ text: "⭐ Interesante", callback_data: `fav_${h}` });

  return {
    inline_keyboard: [navRow, actionsRow],
  };
}

/**
 * Gestiona eventos de pulsación de botones interactivos
 */
async function handleCallbackQuery(queryId, chatId, messageId, data, token, env) {
  if (data === "of_noop") {
    await answerCallbackQuery(token, queryId);
    return;
  }

  if (data.startsWith("of_")) {
    const targetIdx = parseInt(data.replace("of_", ""), 10);
    const ofertas = await fetchOfertas();

    if (isNaN(targetIdx) || targetIdx < 0 || targetIdx >= ofertas.length) {
      await answerCallbackQuery(token, queryId, "No hay más ofertas en esta dirección.");
      return;
    }

    const of = ofertas[targetIdx];
    const textHtml = formatOfferCard(of, targetIdx, ofertas.length);
    const keyboard = buildOfferKeyboard(of, targetIdx, ofertas.length);

    await editTelegramMessage(token, chatId, messageId, textHtml, keyboard);
    await answerCallbackQuery(token, queryId);
    return;
  }

  if (data.startsWith("fav_")) {
    const h = data.replace("fav_", "");
    await answerCallbackQuery(token, queryId, `⭐ ¡Oferta (${h}) marcada como interesante!`, true);
    return;
  }

  await answerCallbackQuery(token, queryId);
}

/**
 * Gestiona comandos de texto de Telegram
 */
async function handleCommand(text, chatId, token, env) {
  const t = text.toLowerCase();

  if (t === "/start" || t === "/ayuda" || t === "ayuda" || t === "hola") {
    const msg = 
      `👋 <b>¡Hola Pedro! Asistente de Empleo activo 24/7.</b>\n\n` +
      `Comandos disponibles en tiempo real:\n` +
      `• /ofertas — 📋 Explorar todas las ofertas con botones ⬅️ Anterior / Siguiente ➡️\n` +
      `• /resumen — 📊 Estadísticas de la base de datos\n` +
      `• /interesantes — ⭐ Ver tus vacantes guardadas\n` +
      `• /buscar — 🚀 Lanzar rastreo en vivo en GitHub Actions\n` +
      `• /interesante_&lt;hash&gt; — Guardar vacante\n` +
      `• /solicitada_&lt;hash&gt; — Marcar como enviada\n` +
      `• /descartar_&lt;hash&gt; — Descartar vacante`;
    await sendTelegramMessage(token, chatId, msg);
    return;
  }

  const ofertas = await fetchOfertas();

  if (t.startsWith("/resumen")) {
    const total = ofertas.length;
    const claseA = ofertas.filter(o => o.clasificacion === "A").length;
    const claseB = ofertas.filter(o => o.clasificacion === "B").length;
    const interesantes = ofertas.filter(o => o.estado === "INTERESANTE").length;
    const nuevas = ofertas.filter(o => o.estado === "NUEVA").length;

    const msg = 
      `📊 <b>ESTADO DE LA BASE DE DATOS</b>\n\n` +
      `• <b>Total ofertas para Grado Superior:</b> ${total}\n` +
      `  - 🟢 Clase A (Encaje directo): ${claseA}\n` +
      `  - 🟡 Clase B (Encaje potencial): ${claseB}\n\n` +
      `• <b>Por Estado:</b>\n` +
      `  - 🆕 Nuevas: ${nuevas}\n` +
      `  - ⭐ Interesantes: ${interesantes}\n\n` +
      `👉 <i>Toca /ofertas para navegar interactivamente entre todas ellas.</i>`;
    await sendTelegramMessage(token, chatId, msg);
    return;
  }

  if (t.startsWith("/ofertas") || t.startsWith("/ultimas")) {
    if (ofertas.length === 0) {
      await sendTelegramMessage(token, chatId, "⚠️ No se han encontrado ofertas activas para Grado Superior actualmente.");
      return;
    }

    let startIndex = 0;
    const partes = t.split(" ");
    if (partes.length > 1) {
      const num = parseInt(partes[1], 10);
      if (!isNaN(num) && num >= 1 && num <= ofertas.length) {
        startIndex = num - 1;
      }
    }

    const of = ofertas[startIndex];
    const textHtml = formatOfferCard(of, startIndex, ofertas.length);
    const keyboard = buildOfferKeyboard(of, startIndex, ofertas.length);

    await sendTelegramMessage(token, chatId, textHtml, keyboard);
    return;
  }

  if (t.startsWith("/interesantes")) {
    const favs = ofertas.filter(o => o.estado === "INTERESANTE");
    if (favs.length === 0) {
      await sendTelegramMessage(token, chatId, "⭐ No tienes ninguna vacante guardada como <b>INTERESANTE</b>.\nToca /ofertas para explorar y guardar.");
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
          await sendTelegramMessage(token, chatId, "🚀 <b>Búsqueda en vivo lanzada en GitHub Actions.</b>\nEl agente está rastreando los 5 portales. Recibirás las novedades en cuanto concluya.");
          return;
        }
      } catch (e) {
        console.error("Error disparando GitHub Actions:", e);
      }
    }
    
    await sendTelegramMessage(
      token, 
      chatId, 
      "🚀 <b>Búsqueda programada activa.</b>\nEl rastreador corre automáticamente cada mañana a las 08:00 hora peninsular. Puedes explorar todas las ofertas activas tocando <b>/ofertas</b>."
    );
    return;
  }

  // Si no coincide con ningún comando
  await sendTelegramMessage(token, chatId, `❓ Comando no reconocido: <code>${text}</code>\nEscribe /ayuda para ver los comandos disponibles.`);
}
