"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { api } from "@/lib/api";

type Notif = { id: number; kind: string; title: string; body: string; lead_code: string | null; tenant_id: number | null; read: boolean; at: string | null };
type Resp = { items: Notif[]; unread: number };

function timeAgo(iso: string | null): string {
  if (!iso) return "";
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return "ahora";
  if (m < 60) return `hace ${m} min`;
  const h = Math.floor(m / 60);
  if (h < 24) return `hace ${h} h`;
  return `hace ${Math.floor(h / 24)} d`;
}

export function NotificationsBell({ onOpenLead }: { onOpenLead?: (clientId: number, leadCode: string) => void }) {
  const [data, setData] = useState<Resp>({ items: [], unread: 0 });
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);

  const load = useCallback(async () => {
    try { setData(await api<Resp>("/me/notifications?limit=20")); } catch { /* silencioso */ }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 60000); // sondeo cada 60 s
    return () => clearInterval(t);
  }, [load]);

  useEffect(() => {
    function onDoc(e: MouseEvent) { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false); }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  async function markAll() {
    try { await api("/me/notifications/read-all", { method: "POST" }); await load(); } catch { /* noop */ }
  }
  async function openItem(n: Notif) {
    if (!n.read) { try { await api(`/me/notifications/${n.id}/read`, { method: "POST" }); } catch { /* noop */ } }
    setOpen(false);
    if (n.tenant_id && n.lead_code && onOpenLead) onOpenLead(n.tenant_id, n.lead_code);
    await load();
  }

  return (
    <div ref={ref} className="relative">
      <button onClick={() => { setOpen((v) => !v); if (!open) load(); }} className="relative grid place-items-center w-9 h-9 rounded-[10px]" style={{ border: "1px solid var(--line)", background: "var(--surface)" }} aria-label="Notificaciones">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 0 1-3.46 0" /></svg>
        {data.unread > 0 && (
          <span className="absolute -top-1 -right-1 min-w-[17px] h-[17px] px-[4px] grid place-items-center rounded-full text-[10px] font-bold text-white" style={{ background: "var(--accent)" }}>
            {data.unread > 9 ? "9+" : data.unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-[340px] rounded-[14px] overflow-hidden z-[50]" style={{ background: "var(--surface)", border: "1px solid var(--line)", boxShadow: "0 20px 50px rgba(20,18,40,.22)" }}>
          <div className="flex items-center justify-between px-4 py-3" style={{ borderBottom: "1px solid var(--line)" }}>
            <b className="text-[14px]">Notificaciones</b>
            {data.unread > 0 && <button onClick={markAll} className="text-[12px] font-semibold" style={{ color: "var(--accent)" }}>Marcar todas como leídas</button>}
          </div>
          <div className="max-h-[380px] overflow-auto">
            {data.items.length === 0 ? (
              <div className="px-4 py-8 text-center text-[13px]" style={{ color: "var(--muted)" }}>Sin notificaciones.</div>
            ) : data.items.map((n) => (
              <button key={n.id} onClick={() => openItem(n)} className="w-full text-left flex gap-3 px-4 py-3" style={{ borderTop: "1px solid var(--line)", background: n.read ? "transparent" : "var(--accent-soft)" }}>
                <span className="mt-[2px] text-[15px]">🔔</span>
                <div className="min-w-0 flex-1">
                  <div className="text-[13px] font-semibold truncate">{n.title}</div>
                  <div className="text-[12.5px]" style={{ color: "var(--muted)" }}>{n.body}</div>
                  <div className="text-[11px] mt-[2px]" style={{ color: "var(--faint)" }}>{n.lead_code ? `${n.lead_code} · ` : ""}{timeAgo(n.at)}</div>
                </div>
                {!n.read && <span className="mt-[6px] w-2 h-2 rounded-full flex-none" style={{ background: "var(--accent)" }} />}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
