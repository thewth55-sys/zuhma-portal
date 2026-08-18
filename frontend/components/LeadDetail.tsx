"use client";

import { useCallback, useEffect, useState } from "react";

import { Icon } from "./Icon";
import { api } from "@/lib/api";

type Opt = { value: string; label?: string; points?: number };
type Question = { key: string; label: string; type: string; section?: string; weight?: number; options?: Opt[] };
type Config = {
  name?: string;
  max_score?: number;
  questions: Question[];
  penalties: Question[];
  info_fields: Question[];
};
type Event = { event: string; destination: string; status: string; event_id: string; value: number | null; sent_at: string | null; response?: string | null };
type Activity = { kind: string; text: string; at: string | null };
type Detail = {
  id: string; name: string; affinity: number | null; band: string | null; channel: string; status: string;
  owner: string; overdue: boolean; description: string; contacts: { kind: string; value: string }[];
  cargo: string | null; company_name: string | null; company_size: string | null; website: string | null;
  session_date: string | null; answers: Record<string, unknown>; propensity_score: number | null; propensity_band: string | null;
  attribution: Record<string, string | null>; events: Event[]; activity: Activity[];
};

const STATUS_LABEL: Record<string, string> = { pending: "Pendiente", waiting: "En espera", potential: "Potencial", discarded: "No potencial" };
const EVENT_STATUS_LABEL: Record<string, string> = { queued: "En cola", sent: "Enviado", failed: "Falló" };

function bandCls(band: string | null) {
  return band === "alta" ? { bg: "#e7f7f0", c: "#0f7a54", label: "Alta" }
    : band === "media" ? { bg: "#fdf3dd", c: "#8a6b16", label: "Media" }
    : { bg: "#fde8e7", c: "#b23a3a", label: "Baja" };
}
function toast(msg: string) {
  const t = document.createElement("div");
  t.textContent = msg;
  t.style.cssText = "position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:var(--brand-ink);color:#fff;padding:11px 20px;border-radius:12px;font-weight:600;font-size:13.5px;box-shadow:0 10px 30px rgba(0,0,0,.25);z-index:99";
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 1800);
}
function optLabel(q: Question, value: unknown): string {
  const o = q.options?.find((x) => x.value === value);
  return o?.label ?? (value == null || value === "" ? "—" : String(value));
}

const TABS = [
  { key: "resumen", label: "Resumen" },
  { key: "calificacion", label: "Calificación" },
  { key: "requerimiento", label: "Requerimiento" },
  { key: "atribucion", label: "Atribución" },
  { key: "actividad", label: "Actividad" },
];

function Row({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <div className="flex justify-between py-[11px]" style={{ borderTop: "1px solid var(--line)" }}>
      <span style={{ color: "var(--muted)" }}>{k}</span>
      <span className="font-semibold text-right">{v ?? "—"}</span>
    </div>
  );
}
function Card({ title, tag, children }: { title: string; tag?: string; children: React.ReactNode }) {
  return (
    <div className="rounded-card p-[18px] mb-4" style={{ background: "var(--surface)", border: "1px solid var(--line)", boxShadow: "0 1px 2px rgba(20,18,40,.04)" }}>
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-[16px] m-0 font-bold">{title}</h2>
        {tag ? <span className="text-[10.5px] font-bold px-[7px] py-[2px] rounded-[6px] uppercase" style={{ background: "#fff1e6", color: "#c05f16" }}>{tag}</span> : null}
      </div>
      {children}
    </div>
  );
}

export function LeadDetail({ leadId, canEdit, onBack, basePath = "/leads", configPath = "/leads/config", adminActions = false }: { leadId: string; canEdit: boolean; onBack: () => void; basePath?: string; configPath?: string; adminActions?: boolean }) {
  const [tab, setTab] = useState("resumen");
  const [detail, setDetail] = useState<Detail | null>(null);
  const [config, setConfig] = useState<Config | null>(null);
  const [answers, setAnswers] = useState<Record<string, unknown>>({});
  const [saving, setSaving] = useState(false);
  const [comment, setComment] = useState("");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [d, c] = await Promise.all([api<Detail>(`${basePath}/${encodeURIComponent(leadId)}`), api<Config>(configPath)]);
      setDetail(d);
      setConfig(c);
      setAnswers(d.answers || {});
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error cargando el lead.");
    }
  }, [leadId, basePath, configPath]);

  useEffect(() => { load(); }, [load]);

  async function save() {
    setSaving(true);
    try {
      const d = await api<Detail>(`${basePath}/${encodeURIComponent(leadId)}`, { method: "PATCH", body: JSON.stringify({ answers }) });
      setDetail(d);
      setAnswers(d.answers || {});
      toast(`Calificación recalculada: ${d.propensity_score}/18 (${d.propensity_band})`);
    } catch {
      toast("No se pudo guardar");
    } finally {
      setSaving(false);
    }
  }

  async function flushEvents() {
    try {
      await api(`${basePath}/${encodeURIComponent(leadId)}/flush`, { method: "POST" });
      toast("Reintentando envío de eventos…");
      load();
    } catch { toast("No se pudo reenviar"); }
  }

  async function sendComment() {
    if (!comment.trim()) return;
    try {
      const d = await api<Detail>(`${basePath}/${encodeURIComponent(leadId)}/comment`, { method: "POST", body: JSON.stringify({ text: comment.trim() }) });
      setDetail(d);
      setComment("");
      toast("Comentario agregado ✓");
    } catch {
      toast("No se pudo comentar");
    }
  }

  function setAns(key: string, value: unknown) {
    setAnswers((a) => ({ ...a, [key]: value }));
  }
  function togglePenalty(key: string, value: string) {
    setAnswers((a) => {
      const cur = Array.isArray(a[key]) ? (a[key] as string[]) : [];
      return { ...a, [key]: cur.includes(value) ? cur.filter((v) => v !== value) : [...cur, value] };
    });
  }

  if (error) {
    return (
      <div className="px-[30px] pt-[26px]">
        <button onClick={onBack} className="text-[13px] font-semibold mb-4" style={{ color: "var(--muted)" }}>← Volver a la bandeja</button>
        <div className="rounded-card p-4 text-[13px]" style={{ background: "#fde8e7", color: "#b23a3a", border: "1px solid #f6c9c2" }}>{error}</div>
      </div>
    );
  }
  if (!detail || !config) {
    return <div className="px-[30px] pt-[26px]" style={{ color: "var(--muted)" }}>Cargando…</div>;
  }

  const bd = bandCls(detail.propensity_band);
  const attr = detail.attribution;

  return (
    <div className="px-[30px] pt-[26px] pb-[60px] max-w-[1180px]">
      <button onClick={onBack} className="text-[13px] font-semibold mb-4" style={{ color: "var(--muted)" }}>← Volver a la bandeja</button>

      {/* Encabezado */}
      <div className="rounded-card p-[18px] mb-4 flex items-center gap-4" style={{ background: "var(--surface)", border: "1px solid var(--line)", boxShadow: "0 1px 2px rgba(20,18,40,.04)" }}>
        <div className="w-[52px] h-[52px] rounded-[12px] grid place-items-center font-bold text-[18px]" style={{ background: "var(--accent-soft)", color: "var(--accent)" }}>
          {(detail.name || "·").slice(0, 2).toUpperCase()}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-[20px] font-extrabold tracking-tight">{detail.name}</div>
          <div className="text-[13px]" style={{ color: "var(--muted)" }}>
            {[detail.cargo, detail.company_name].filter(Boolean).join(" · ") || "—"}
          </div>
          <div className="text-[12px] mt-1 font-mono" style={{ color: "var(--accent)" }}>{detail.id}</div>
        </div>
        <div className="text-center rounded-[10px] px-4 py-2 font-extrabold text-[16px]" style={{ background: bd.bg, color: bd.c }}>
          {bd.label}
          <small className="block text-[10px] font-bold uppercase mt-[2px] opacity-80">Propensidad {detail.propensity_score ?? "—"}/{config.max_score ?? 18}</small>
        </div>
        <span className="text-[12px] font-semibold px-[11px] py-[5px] rounded-[20px]" style={{ background: "#eef4ff", color: "#2a5fb0" }}>{STATUS_LABEL[detail.status] ?? detail.status}</span>
      </div>

      {/* Sub-pestañas */}
      <div className="inline-flex gap-[6px] mb-[18px] p-[4px] rounded-xl" style={{ background: "var(--bg)", border: "1px solid var(--line)" }}>
        {TABS.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)} className="px-[15px] py-[7px] rounded-lg text-[13px] font-semibold" style={t.key === tab ? { background: "var(--surface)", color: "var(--ink)", boxShadow: "0 1px 2px rgba(20,18,40,.06)" } : { background: "transparent", color: "var(--muted)" }}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === "resumen" && (
        <div className="grid gap-4" style={{ gridTemplateColumns: "1fr 1fr", alignItems: "start" }}>
          <Card title="Contacto">
            <Row k="Nombre" v={detail.name} />
            <Row k="Cargo" v={detail.cargo} />
            <Row k="Correo" v={attr && detail.contacts.find((c) => c.kind === "mail")?.value} />
            <Row k="Teléfono" v={detail.contacts.find((c) => c.kind === "phone")?.value} />
            <Row k="Dueño" v={detail.owner} />
          </Card>
          <Card title="Empresa">
            <Row k="Empresa" v={detail.company_name} />
            <Row k="Tamaño" v={detail.company_size} />
            <Row k="Página web" v={detail.website} />
            <Row k="Canal de origen" v={detail.channel} />
          </Card>
          <Card title="Requerimiento">
            <div className="text-[13.5px]" style={{ color: "var(--muted)" }}>{detail.description || "—"}</div>
          </Card>
        </div>
      )}

      {tab === "calificacion" && (
        <Card title="Calificación de propensidad" tag={config.name}>
          {config.questions.map((q) => (
            <div key={q.key} className="flex items-center justify-between gap-4 py-[10px]" style={{ borderTop: "1px solid var(--line)" }}>
              <div className="text-[13.5px]">{q.label} <span style={{ color: "var(--faint)" }}>(máx {q.weight})</span></div>
              {canEdit ? (
                <select value={(answers[q.key] as string) ?? ""} onChange={(e) => setAns(q.key, e.target.value)} className="px-3 py-2 rounded-[10px] text-[13px] outline-none min-w-[200px]" style={{ border: "1px solid var(--line)" }}>
                  <option value="">—</option>
                  {q.options?.map((o) => <option key={o.value} value={o.value}>{o.label} ({o.points})</option>)}
                </select>
              ) : (
                <span className="text-[13.5px] font-semibold">{optLabel(q, answers[q.key])}</span>
              )}
            </div>
          ))}
          {config.penalties.map((p) => (
            <div key={p.key} className="py-[10px]" style={{ borderTop: "1px solid var(--line)" }}>
              <div className="text-[13.5px] mb-2">{p.label}</div>
              <div className="flex gap-4 flex-wrap">
                {p.options?.map((o) => {
                  const on = Array.isArray(answers[p.key]) && (answers[p.key] as string[]).includes(o.value);
                  return canEdit ? (
                    <label key={o.value} className="flex items-center gap-2 text-[13px] cursor-pointer">
                      <input type="checkbox" checked={!!on} onChange={() => togglePenalty(p.key, o.value)} /> {o.label} ({o.points})
                    </label>
                  ) : (
                    <span key={o.value} className="text-[13px]" style={{ opacity: on ? 1 : 0.4 }}>{on ? "☑" : "☐"} {o.label} ({o.points})</span>
                  );
                })}
              </div>
            </div>
          ))}
          <div className="flex items-center justify-between mt-4 pt-4" style={{ borderTop: "2px solid var(--line)" }}>
            <div className="text-[13px]" style={{ color: "var(--muted)" }}>
              Propensidad actual: <b style={{ color: "var(--ink)" }}>{detail.propensity_score}/{config.max_score ?? 18}</b> ({bandCls(detail.propensity_band).label})
            </div>
            {canEdit ? (
              <button onClick={save} disabled={saving} className="px-4 py-2 rounded-[10px] text-[13px] font-semibold text-white disabled:opacity-60" style={{ background: "var(--accent)" }}>
                {saving ? "Guardando…" : "Guardar y recalcular"}
              </button>
            ) : (
              <span className="text-[12px]" style={{ color: "var(--faint)" }}>Solo el equipo Zuhma edita la calificación</span>
            )}
          </div>
        </Card>
      )}

      {tab === "requerimiento" && (
        <Card title="Requerimiento & sesión">
          {config.info_fields.map((f) => (
            <div key={f.key} className="flex items-center justify-between gap-4 py-[10px]" style={{ borderTop: "1px solid var(--line)" }}>
              <div className="text-[13.5px]">{f.label}</div>
              {!canEdit ? (
                <span className="text-[13.5px] font-semibold">
                  {f.type === "boolean" ? (answers[f.key] ? "Sí" : "No") : f.type === "select" ? optLabel(f, answers[f.key]) : ((answers[f.key] as string) || "—")}
                </span>
              ) : f.type === "boolean" ? (
                <input type="checkbox" checked={!!answers[f.key]} onChange={(e) => setAns(f.key, e.target.checked)} />
              ) : f.type === "select" ? (
                <select value={(answers[f.key] as string) ?? ""} onChange={(e) => setAns(f.key, e.target.value)} className="px-3 py-2 rounded-[10px] text-[13px] outline-none min-w-[200px]" style={{ border: "1px solid var(--line)" }}>
                  <option value="">—</option>
                  {f.options?.map((o) => <option key={o.value} value={o.value}>{o.label ?? o.value}</option>)}
                </select>
              ) : (
                <input value={(answers[f.key] as string) ?? ""} onChange={(e) => setAns(f.key, f.type === "number" ? Number(e.target.value) : e.target.value)} type={f.type === "number" ? "number" : "text"} className="px-3 py-2 rounded-[10px] text-[13px] outline-none min-w-[200px]" style={{ border: "1px solid var(--line)" }} />
              )}
            </div>
          ))}
          <Row k="Fecha de sesión" v={detail.session_date} />
          {canEdit && (
            <div className="flex justify-end mt-4">
              <button onClick={save} disabled={saving} className="px-4 py-2 rounded-[10px] text-[13px] font-semibold text-white disabled:opacity-60" style={{ background: "var(--accent)" }}>{saving ? "Guardando…" : "Guardar"}</button>
            </div>
          )}
        </Card>
      )}

      {tab === "atribucion" && (
        <>
          <Card title="Atribución" tag="Lead ID único">
            <div className="font-mono font-bold mb-2" style={{ color: "var(--accent)" }}>{detail.id}</div>
            <Row k="Canal" v={detail.channel} />
            <Row k="GCLID (Google)" v={attr.gclid || "—"} />
            <Row k="FBCLID (Meta)" v={attr.fbclid || "—"} />
            <Row k="fbc / fbp" v={`${attr.fbc || "—"} / ${attr.fbp || "—"}`} />
            <Row k="UTM source / medium" v={`${attr.utm_source || "—"} / ${attr.utm_medium || "—"}`} />
            <Row k="UTM campaign" v={attr.utm_campaign || "—"} />
          </Card>
          <Card title="Eventos de conversión (CAPI / Google Ads)" tag={undefined}>
            {adminActions && (
              <div className="flex justify-end mb-2">
                <button onClick={flushEvents} className="text-[12.5px] font-semibold px-[11px] py-[6px] rounded-[10px] text-white" style={{ background: "var(--accent)" }}>↻ Reintentar envío</button>
              </div>
            )}
            {detail.events.length === 0 ? (
              <div style={{ color: "var(--muted)" }}>Sin eventos todavía.</div>
            ) : (
              <table className="w-full">
                <thead><tr>{["Evento", "Destino", "Estado", "event_id", "Detalle"].map((h) => <th key={h} className="text-left text-[11px] uppercase font-bold pb-2" style={{ color: "var(--faint)" }}>{h}</th>)}</tr></thead>
                <tbody>
                  {detail.events.map((e, i) => (
                    <tr key={i}>
                      <td className="py-2 text-[13px] font-semibold" style={{ borderTop: "1px solid var(--line)" }}><code style={{ background: "#f4f3f8", padding: "2px 6px", borderRadius: 5 }}>{e.event}</code></td>
                      <td className="py-2 text-[13px]" style={{ borderTop: "1px solid var(--line)" }}>{e.destination}</td>
                      <td className="py-2 text-[13px]" style={{ borderTop: "1px solid var(--line)" }}>
                        <span className="text-[12px] font-semibold px-[9px] py-[3px] rounded-[20px]" style={e.status === "sent" ? { background: "#e7f7f0", color: "#0f7a54" } : { background: "#fdf3dd", color: "#8a6b16" }}>{EVENT_STATUS_LABEL[e.status] ?? e.status}</span>
                      </td>
                      <td className="py-2 text-[12px] font-mono" style={{ borderTop: "1px solid var(--line)", color: "var(--muted)" }}>{e.event_id}</td>
                      <td className="py-2 text-[11px]" style={{ borderTop: "1px solid var(--line)", color: "var(--muted)", maxWidth: 240 }} title={e.response ?? ""}><span className="block truncate">{e.response ?? "—"}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            <div className="rounded-xl p-[12px_15px] text-[12.5px] flex gap-[10px] items-start mt-3" style={{ background: "var(--accent-soft)", border: "1px solid #f8d3c8", color: "#a23c2f" }}>
              <Icon name="bolt" className="zi" />
              <div>Los eventos quedan <b>en cola</b> hasta conectar las credenciales de Meta CAPI / Google Ads del cliente. Ahí el portal los dispara server-side (con el mismo Lead ID para deduplicar).</div>
            </div>
          </Card>
        </>
      )}

      {tab === "actividad" && (
        <Card title="Actividad">
          <div className="flex gap-2 mb-4">
            <input value={comment} onChange={(e) => setComment(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") sendComment(); }} placeholder="Escribe un comentario…" className="flex-1 px-3 py-2 rounded-[10px] text-[13px] outline-none" style={{ border: "1px solid var(--line)" }} />
            <button onClick={sendComment} className="px-4 py-2 rounded-[10px] text-[13px] font-semibold text-white" style={{ background: "var(--accent)" }}>Comentar</button>
          </div>
          {detail.activity.length === 0 ? <div style={{ color: "var(--muted)" }}>Sin actividad.</div> : detail.activity.map((a, i) => (
            <div key={i} className="flex gap-3 py-[11px]" style={{ borderTop: i ? "1px solid var(--line)" : "none" }}>
              <div className="w-8 h-8 rounded-[9px] grid place-items-center flex-none" style={{ background: "var(--accent-soft)", color: "var(--accent)" }}><Icon name="bolt" className="zi" /></div>
              <div>
                <div className="text-[13.5px] font-semibold">{a.text}</div>
                <div className="text-[12px]" style={{ color: "var(--faint)" }}>{a.at ? new Date(a.at).toLocaleString("es-MX") : ""}</div>
              </div>
            </div>
          ))}
        </Card>
      )}
    </div>
  );
}
