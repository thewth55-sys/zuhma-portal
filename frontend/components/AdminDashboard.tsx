"use client";

import { useEffect, useState } from "react";

import { Icon } from "./Icon";
import { api } from "@/lib/api";
import type { IconName } from "@/lib/nav";

type PerClient = { id: number; name: string; plan: string | null; status: string; lead_mode: string; leads: number; qualified: number; users: number };
type Recent = { lead_id: string; name: string; channel: string; band: string | null; at: string | null; client: string };
type Dash = {
  clients_total: number; clients_active: number; leads_total: number; leads_pending: number;
  leads_qualified: number; events_sent: number; events_queued: number; per_client: PerClient[]; recent: Recent[];
};

function bandCls(band: string | null) {
  return band === "alta" ? { bg: "#e7f7f0", c: "#0f7a54", label: "Alta" } : band === "media" ? { bg: "#fdf3dd", c: "#8a6b16", label: "Media" } : { bg: "#fde8e7", c: "#b23a3a", label: "Baja" };
}

function Kpi({ icon, val, lbl }: { icon: IconName; val: string | number; lbl: string }) {
  return (
    <div className="rounded-card p-[18px]" style={{ background: "var(--surface)", border: "1px solid var(--line)", boxShadow: "0 1px 2px rgba(20,18,40,.04),0 8px 24px rgba(20,18,40,.05)" }}>
      <div className="w-[38px] h-[38px] rounded-[11px] grid place-items-center mb-3" style={{ background: "var(--accent-soft)", color: "var(--accent)" }}><Icon name={icon} className="zi" /></div>
      <div className="text-[30px] font-extrabold leading-none tracking-tight">{val}</div>
      <div className="text-[13px] mt-[5px]" style={{ color: "var(--muted)" }}>{lbl}</div>
    </div>
  );
}

export function AdminDashboard({ onOpenClients, onOpenLeads }: { onOpenClients: () => void; onOpenLeads: () => void }) {
  const [d, setD] = useState<Dash | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => { api<Dash>("/admin/dashboard").then(setD).catch((e) => setErr(e instanceof Error ? e.message : "Error")); }, []);

  return (
    <div className="px-[30px] pt-[26px] pb-[60px] max-w-[1180px]">
      <h1 className="text-[27px] tracking-tight m-0 mb-[3px] font-bold">Dashboard</h1>
      <p className="m-0 mb-[22px]" style={{ color: "var(--muted)" }}>Vista general del negocio · Zuhma</p>

      {err && <div className="rounded-card p-4 text-[13px]" style={{ background: "#fde8e7", color: "#b23a3a", border: "1px solid #f6c9c2" }}>{err.includes("403") ? "Requiere rol admin." : err}</div>}

      <div className="grid gap-4 mb-4" style={{ gridTemplateColumns: "repeat(4,1fr)" }}>
        <Kpi icon="users" val={`${d?.clients_active ?? "—"}/${d?.clients_total ?? "—"}`} lbl="Clientes activos" />
        <Kpi icon="inbox" val={d?.leads_total ?? "—"} lbl="Leads totales" />
        <Kpi icon="check" val={d?.leads_qualified ?? "—"} lbl="Leads calificados" />
        <Kpi icon="target" val={d?.events_sent ?? "—"} lbl="Conversiones enviadas" />
      </div>

      <div className="grid gap-4" style={{ gridTemplateColumns: "1.4fr 1fr", alignItems: "start" }}>
        <div className="rounded-card p-[18px]" style={{ background: "var(--surface)", border: "1px solid var(--line)", boxShadow: "0 1px 2px rgba(20,18,40,.04)" }}>
          <div className="flex items-center justify-between mb-3"><h2 className="text-[16px] m-0 font-bold">Clientes</h2><button onClick={onOpenClients} className="text-[12.5px] font-semibold" style={{ color: "var(--accent)" }}>Gestionar →</button></div>
          <table className="w-full">
            <thead><tr>{["Cliente", "Plan", "Modo", "Leads", "Calif.", "Usuarios"].map((h) => <th key={h} className="text-left text-[11px] uppercase font-bold pb-2" style={{ color: "var(--faint)" }}>{h}</th>)}</tr></thead>
            <tbody>
              {d?.per_client.map((c) => (
                <tr key={c.id}>
                  <td className="py-2 text-[13.5px] font-semibold" style={{ borderTop: "1px solid var(--line)" }}>{c.name}</td>
                  <td className="py-2 text-[13px]" style={{ borderTop: "1px solid var(--line)" }}>{c.plan ?? "—"}</td>
                  <td className="py-2 text-[12px]" style={{ borderTop: "1px solid var(--line)", color: "var(--muted)" }}>{c.lead_mode === "agency_managed" ? "Zuhma califica" : "Cliente califica"}</td>
                  <td className="py-2 text-[13px]" style={{ borderTop: "1px solid var(--line)" }}>{c.leads}</td>
                  <td className="py-2 text-[13px]" style={{ borderTop: "1px solid var(--line)" }}>{c.qualified}</td>
                  <td className="py-2 text-[13px]" style={{ borderTop: "1px solid var(--line)" }}>{c.users}</td>
                </tr>
              ))}
              {d && d.per_client.length === 0 && <tr><td colSpan={6} className="py-6 text-center text-[13px]" style={{ color: "var(--muted)" }}>Aún no hay clientes. <button onClick={onOpenClients} style={{ color: "var(--accent)", fontWeight: 600 }}>Crear el primero →</button></td></tr>}
            </tbody>
          </table>
        </div>

        <div className="rounded-card p-[18px]" style={{ background: "var(--surface)", border: "1px solid var(--line)", boxShadow: "0 1px 2px rgba(20,18,40,.04)" }}>
          <div className="flex items-center justify-between mb-3"><h2 className="text-[16px] m-0 font-bold">Leads recientes</h2><button onClick={onOpenLeads} className="text-[12.5px] font-semibold" style={{ color: "var(--accent)" }}>Ver todos →</button></div>
          {d?.recent.length === 0 && <div className="text-[13px]" style={{ color: "var(--muted)" }}>Sin leads todavía.</div>}
          {d?.recent.map((r) => {
            const bd = bandCls(r.band);
            return (
              <div key={r.lead_id} className="flex items-center gap-3 py-[10px]" style={{ borderTop: "1px solid var(--line)" }}>
                <div className="w-8 h-8 rounded-[9px] grid place-items-center font-bold text-[12px] flex-none" style={{ background: bd.bg, color: bd.c }}>{bd.label[0]}</div>
                <div className="flex-1 min-w-0">
                  <div className="text-[13.5px] font-semibold truncate">{r.name}</div>
                  <div className="text-[12px]" style={{ color: "var(--faint)" }}>{r.client} · {r.channel}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="rounded-card p-[14px_18px] text-[13px] mt-4 flex gap-3 items-center" style={{ background: "var(--accent-soft)", border: "1px solid #f8d3c8", color: "#a23c2f" }}>
        <Icon name="bolt" className="zi" />
        <div>{(d?.events_queued ?? 0) > 0 ? <><b>{d?.events_queued} eventos de conversión en cola</b> — configura CAPI/Google en cada cliente para dispararlos.</> : "Circuito de conversiones al día."}</div>
      </div>
    </div>
  );
}
