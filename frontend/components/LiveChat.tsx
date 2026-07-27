"use client";

import { useEffect } from "react";

/**
 * Chat en vivo = Odoo Livechat NATIVO (no construimos chat propio).
 * Inyecta el snippet oficial de Odoo. Requiere:
 *   NEXT_PUBLIC_ODOO_LIVECHAT_URL     (host de tu Odoo)
 *   NEXT_PUBLIC_ODOO_LIVECHAT_CHANNEL (id del canal de Livechat)
 * Si no están configurados, no renderiza nada (sin romper la UI).
 */
export function LiveChat() {
  const url = process.env.NEXT_PUBLIC_ODOO_LIVECHAT_URL;
  const channel = process.env.NEXT_PUBLIC_ODOO_LIVECHAT_CHANNEL;

  useEffect(() => {
    if (!url || !channel) return;
    if (document.getElementById("odoo-livechat-loader")) return;

    (window as unknown as { odoo_web_livechat?: unknown }).odoo_web_livechat = {
      channel_id: Number(channel),
    };
    const s = document.createElement("script");
    s.id = "odoo-livechat-loader";
    s.src = `${url.replace(/\/$/, "")}/im_livechat/loader`;
    s.async = true;
    document.body.appendChild(s);
  }, [url, channel]);

  return null;
}
