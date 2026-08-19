"use client";

import { useCallback, useEffect, useState } from "react";

import { Icon } from "./Icon";
import { LeadDetail } from "./LeadDetail";
import { QualifyModal, type QualifyPayload } from "./QualifyModal";
import { api } from "@/lib/api";
import type { IconName } from "@/lib/nav";

type Contact = { kind: string; value: string };
type Lead = {
  id: string;
  name: string;
  affinity: number | null; // propensidad 0–18
  band: string | null; // alta | media | baja
  channel: string;
  status: string;
  owner: string;
  minutes_in_inbox: number;
  overdue: boolean;
  description: string;
  contacts: Contact[];
};
type Kpis = { pending: number; avg_response_hours: number; qualified_month: number; answered_under_24h_pct: number };
type ListResp = { leads: Lead[]; counts: Record<string, number> };

const TABS: { key: string; label: string }[] = [
  { key: "pending", label: "Nuevo" },
  { key: "waiting", label: "Seguimiento" },
  { key: "potential", label: "Ganado" },
  { key: "discarded", label: "Perdido" },
  { key: "all", label: "Todos" },
];

function initials(name: string) {
  const p = name.trim().split(/\s+/);
  return ((p[0]?.[0] ?? "") + (p[1]?.[0] ?? "")).toUpperCase() || "·";
}
function bandCls(band: string | null) {
  return band === "alta"
    ? { bg: "#e7f7f0", c: "#0f7a54", label: "Alta" }
    : band === "media"
    ? { bg: "#fdf3dd", c: "#8a6b16", label: "Media" }
    : { bg: "#fde8e7", c: "#b23a3a", label: "Baja" };
}
function channelCls(ch: string): { bg: string; c: string } {
  const m: Record<string, { bg: string; c: string }> = {
    "Meta Ads": { bg: "#eef4ff", c: "#2a5fb0" },
    "Google Ads": { bg: "#f0eff5", c: "#6b6a7b" },
    WhatsApp: { bg: "#e7f7f0", c: "#0f7a54" },
  };
  return m[ch] ?? { bg: "#f0eff5", c: "#6b6a7b" };
}
function timeLabel(l: Lead) {
  const m = l.minutes_in_inbox;
  if (m < 60) return `hace ${m} min`;
  const h = Math.round(m / 60);
  return l.overdue ? `+${h} h en bandeja` : `hace ${h} h`;
}

function toast(msg: string) {
  const t = document.createElement("div");
  t.textContent = msg;
  t.style.cssText =
    "position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:var(--brand-ink);color:#fff;padding:11px 20px;border-radius:12px;font-weight:600;font-size:13.5px;box-shadow:0 10px 30px rgba(0,0,0,.25);z-index:99";
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 1800);
}

function Kpi({ icon, val, lbl, delta }: { icon: IconName; val: string; lbl: string; delta?: string }) {
  return (
    <div className="rounded-card p-[18px]" style={{ background: "var(--surface)", border: "1px solid var(--line)", boxShadow: "0 1px 2px rgba(20,18,40,.04),0 8px 24px rgba(20,18,40,.05)" }}>
      <div className="w-[38px] h-[38px] rounded-[11px] grid place-items-center mb-3" style={{ background: "var(--accent-soft)", color: "var(--accent)" }}>
        <Icon name={icon} className="zi" />
      </div>
      <div className="text-[30px] font-extrabold leading-none tracking-tight">{val}</div>
      <div className="text-[13px] mt-[5px]" style={{ color: "var(--muted)" }}>{lbl}</div>
      {delta ? <div className="text-[12px] font-bold mt-2" style={{ color: "var(--good,#1baf7a)" }}>▲ {delta}</div> : null}
    </div>
  );
}

export function LeadsView({ canEdit }: { canEdit: boolean }) {
  const [tab, setTab] = useState("pending");
  const [kpis, setKpis] = useState<Kpis | null>(null);
  const [data, setData] = useState<ListResp | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const [openId, setOpenId] = useState<string | null>(null);
  const [qualify, setQualify] = useState<{ lead: Lead; kind: "potential" | "discarded" } | null>(null);
  const [form, setForm] = useState({ contact_name: "", channel: "Meta Ads", phone: "" });

  const load = useCallback(async (status: string) => {
    setError(null);
    try {
      const [k, d] = await Promise.all([
        api<Kpis>("/leads/kpis"),
        api<ListResp>(`/leads?status_filter=${status}`),
      ]);
      setKpis(k);
      setData(d);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error cargando la bandeja.");
    }
  }, []);

  useEffect(() => {
    load(tab);
  }, [tab, load]);

  async function act(lead: Lead, status: string, label: string) {
    try {
      await api(`/leads/${encodeURIComponent(lead.id)}/status`, { method: "POST", body: JSON.stringify({ status }) });
      toast(label);
      await load(tab);
    } catch {
      toast("No se pudo actualizar el lead");
    }
  }

  // Ganado/Perdido pasan por el modal (datos obligatorios); el backend los valida.
  async function submitQualify(payload: QualifyPayload) {
    if (!qualify) return;
    await api(`/leads/${encodeURIComponent(qualify.lead.id)}/status`, { method: "POST", body: JSON.stringify(payload) });
    toast(payload.status === "potential" ? "Marcado como Ganado ✓" : "Marcado como Perdido");
    setQualify(null);
    await load(tab);
  }

  async function submitAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!form.contact_name.trim()) return;
    try {
      await api("/leads", { method: "POST", body: JSON.stringify(form) });
      setForm({ contact_name: "", channel: "Meta Ads", phone: "" });
      setAdding(false);
      toast("Prospecto agregado ✓");
      await load(tab);
    } catch {
      toast("No se pudo agregar el prospecto");
    }
  }

  function exportCsv() {
    const rows = data?.leads ?? [];
    const head = ["id", "nombre", "afinidad", "canal", "estado", "dueño", "contacto"];
    const body = rows.map((l) =>
      [l.id, l.name, l.affinity, l.channel, l.status, l.owner, l.contacts.map((c) => c.value).join(" / ")]
        .map((v) => `"${String(v).replace(/"/g, '""')}"`)
        .join(","),
    );
    const csv = [head.join(","), ...body].join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = "leads.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  const counts = data?.counts ?? {};

  if (openId) {
    return <LeadDetail leadId={openId} canEdit={canEdit} onBack={() => { setOpenId(null); load(tab); }} />;
  }

  return (
    <div className="px-[30px] pt-[26px] pb-[60px] max-w-[1180px]">
      {qualify && (
        <QualifyModal kind={qualify.kind} leadName={`${qualify.lead.name} · ${qualify.lead.id}`} onCancel={() => setQualify(null)} onSubmit={submitQualify} />
      )}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[27px] tracking-tight m-0 mb-[3px] font-bold">Bandeja de leads</h1>
          <p className="m-0" style={{ color: "var(--muted)" }}>
            Tus prospectos ya calificados, listos para cerrar.{" "}
            <span className="text-[10.5px] font-bold px-[7px] py-[2px] rounded-[6px] uppercase align-middle" style={{ background: "#fff1e6", color: "#c05f16" }}>
              Zuhma Lead Hub
            </span>
          </p>
        </div>
        <div className="flex gap-[10px] items-center">
          <button onClick={exportCsv} className="text-[12.5px] font-semibold px-[11px] py-[6px] rounded-[10px]" style={{ border: "1px solid var(--line)", background: "var(--surface)" }}>
            ⤓ Exportar CSV
          </button>
          {canEdit && (
            <button onClick={() => setAdding((v) => !v)} className="text-[12.5px] font-semibold px-[11px] py-[6px] rounded-[10px] text-white" style={{ background: "var(--accent)" }}>
              + Agregar prospecto
            </button>
          )}
        </div>
      </div>

      {canEdit && adding && (
        <form onSubmit={submitAdd} className="mt-4 rounded-card p-4 flex flex-wrap gap-3 items-end" style={{ background: "var(--surface)", border: "1px solid var(--line)" }}>
          <div className="flex flex-col gap-1">
            <label className="text-[11px] font-bold uppercase" style={{ color: "var(--faint)" }}>Nombre</label>
            <input required value={form.contact_name} onChange={(e) => setForm({ ...form, contact_name: e.target.value })} className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={{ border: "1px solid var(--line)" }} placeholder="Nombre del contacto" />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[11px] font-bold uppercase" style={{ color: "var(--faint)" }}>Canal</label>
            <select value={form.channel} onChange={(e) => setForm({ ...form, channel: e.target.value })} className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={{ border: "1px solid var(--line)" }}>
              <option>Meta Ads</option>
              <option>Google Ads</option>
              <option>WhatsApp</option>
              <option>Orgánico</option>
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[11px] font-bold uppercase" style={{ color: "var(--faint)" }}>Teléfono</label>
            <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={{ border: "1px solid var(--line)" }} placeholder="Teléfono de contacto" />
          </div>
          <button type="submit" className="px-4 py-2 rounded-[10px] text-[13px] font-semibold text-white" style={{ background: "var(--accent)" }}>Guardar</button>
        </form>
      )}

      <div className="grid gap-4 my-5" style={{ gridTemplateColumns: "repeat(4,1fr)" }}>
        <Kpi icon="inbox" val={String(kpis?.pending ?? "—")} lbl="Nuevos por atender" />
        <Kpi icon="clock" val={kpis ? `${kpis.avg_response_hours} h` : "—"} lbl="Tiempo prom. de respuesta" />
        <Kpi icon="check" val={String(kpis?.qualified_month ?? "—")} lbl="Calificados este mes" />
        <Kpi icon="target" val={kpis ? `${kpis.answered_under_24h_pct}%` : "—"} lbl="Atendidos < 24 h" />
      </div>

      <div className="inline-flex gap-[6px] mb-[18px] p-[4px] rounded-xl" style={{ background: "var(--bg)", border: "1px solid var(--line)" }}>
        {TABS.map((t) => {
          const n = counts[t.key];
          const on = t.key === tab;
          return (
            <button key={t.key} onClick={() => setTab(t.key)} className="px-[15px] py-[7px] rounded-lg text-[13px] font-semibold" style={on ? { background: "var(--surface)", color: "var(--ink)", boxShadow: "0 1px 2px rgba(20,18,40,.06)" } : { background: "transparent", color: "var(--muted)" }}>
              {t.label}{typeof n === "number" ? ` (${n})` : ""}
            </button>
          );
        })}
      </div>

      {error && (
        <div className="rounded-card p-4 text-[13px]" style={{ background: "#fde8e7", color: "#b23a3a", border: "1px solid #f6c9c2" }}>
          {error.includes("401") ? "Inicia sesión para ver tu bandeja de leads." : error}
        </div>
      )}

      {!error && data?.leads.length === 0 && (
        <div className="rounded-card p-10 text-center" style={{ color: "var(--muted)", border: "1px dashed var(--line)", background: "var(--surface)" }}>
          No hay leads en esta pestaña.
        </div>
      )}

      {!error &&
        data?.leads.map((l) => {
          const bd = bandCls(l.band);
          const ch = channelCls(l.channel);
          return (
            <div key={l.id} className="flex gap-[14px] rounded-[14px] p-[15px] mb-3" style={{ background: l.overdue ? "#fffaf9" : "var(--surface)", border: `1px solid ${l.overdue ? "#f6c9c2" : "var(--line)"}`, boxShadow: "0 1px 2px rgba(20,18,40,.04)" }}>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-[11px]">
                  <div className="w-8 h-8 rounded-[9px] grid place-items-center font-bold text-[13px]" style={{ background: "var(--accent-soft)", color: "var(--accent)" }}>
                    {initials(l.name)}
                  </div>
                  <div>
                    <div className="font-bold">{l.name}</div>
                    <div className="text-[12px] flex items-center gap-[5px]" style={{ color: "var(--faint)" }}>
                      {l.overdue ? (
                        <span className="inline-flex items-center gap-[5px] text-[11px] font-bold px-2 py-[3px] rounded-[20px]" style={{ background: "#fde8e7", color: "#b23a3a" }}>
                          <Icon name="clock" className="zi" /> {timeLabel(l)}
                        </span>
                      ) : (
                        <><Icon name="clock" className="zi" /> {timeLabel(l)}</>
                      )}
                    </div>
                  </div>
                </div>
                <div className="text-[13px] mt-[9px]" style={{ color: "var(--muted)" }}>{l.description}</div>
                <div className="flex gap-[7px] flex-wrap mt-[11px] items-center">
                  <span className="text-[12px] font-semibold px-[10px] py-[3px] rounded-[20px]" style={{ background: ch.bg, color: ch.c }}>{l.channel}</span>
                  {l.contacts.map((c, i) => (
                    <span key={i} className="inline-flex items-center gap-[5px] text-[12px] font-semibold px-[9px] py-[4px] rounded-[7px]" style={{ background: "var(--bg)", border: "1px solid var(--line)", color: "var(--muted)" }}>
                      <Icon name={(c.kind === "mail" ? "mail" : "phone") as IconName} className="zi" /> {c.value}
                    </span>
                  ))}
                  <span className="inline-flex items-center gap-[5px] text-[12px] font-semibold px-[9px] py-[4px] rounded-[7px]" style={{ background: "var(--bg)", border: "1px solid var(--line)", color: "var(--muted)" }}>
                    <Icon name="user" className="zi" /> {l.owner}
                  </span>
                </div>
              </div>
              <div className="w-[186px] flex-none flex flex-col gap-[7px] items-end">
                <div className="w-full text-center rounded-[10px] p-2 font-extrabold text-[15px] leading-none" style={{ background: bd.bg, color: bd.c }}>
                  {bd.label}<small className="block text-[10px] font-bold uppercase mt-[3px] opacity-80">Propensidad {l.affinity ?? "—"}/18</small>
                </div>
                <button onClick={() => setOpenId(l.id)} className="w-full justify-center text-[12.5px] font-semibold px-[11px] py-[6px] rounded-[10px]" style={{ border: "1px solid var(--line)", background: "var(--bg)" }}>Ver detalle →</button>
                <button onClick={() => setQualify({ lead: l, kind: "potential" })} className="w-full justify-center text-[12.5px] font-semibold px-[11px] py-[6px] rounded-[10px] text-white" style={{ background: "var(--good,#1baf7a)" }}>🏆 Ganado</button>
                <button onClick={() => setQualify({ lead: l, kind: "discarded" })} className="w-full justify-center text-[12.5px] font-semibold px-[11px] py-[6px] rounded-[10px]" style={{ border: "1px solid var(--line)", background: "var(--surface)" }}>✕ Perdido</button>
                <button onClick={() => act(l, "waiting", "Movido a Seguimiento")} className="w-full justify-center text-[12.5px] font-semibold px-[11px] py-[6px] rounded-[10px]" style={{ border: "1px solid var(--line)", background: "var(--surface)" }}>⏳ Seguimiento</button>
              </div>
            </div>
          );
        })}

      <div className="rounded-xl p-[12px_15px] text-[13px] flex gap-[10px] items-start mt-4" style={{ background: "var(--accent-soft)", border: "1px solid #f8d3c8", color: "#a23c2f" }}>
        <Icon name="bolt" className="zi" />
        <div>
          <b>Todo en un lugar · filtro de calidad · control del tiempo de respuesta.</b> Cada lead llega calificado con su % de afinidad; el reloj marca cuánto lleva sin atender. Al marcarlo, el sistema aprenderá y mejorará la pauta (vía Lead Hub → Meta/Google) cuando el circuito esté activo.
        </div>
      </div>
    </div>
  );
}
