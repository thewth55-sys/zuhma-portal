"use client";

import { useCallback, useEffect, useState } from "react";

import { LeadDetail } from "./LeadDetail";
import { api } from "@/lib/api";

type Client = { id: number; name: string; lead_mode: string };
type Lead = { id: string; name: string; affinity: number | null; band: string | null; channel: string; status: string; owner: string; released: boolean; description: string };
type ListResp = { leads: Lead[]; counts: Record<string, number>; lead_mode: string };
type Opt = { value: string; label?: string; points?: number };
type Question = { key: string; label: string; type: string; section?: string; weight?: number; options?: Opt[] };
type Config = { name?: string; max_score?: number; questions: Question[]; penalties: Question[]; info_fields: Question[] };

function toast(msg: string) {
  const t = document.createElement("div");
  t.textContent = msg;
  t.style.cssText = "position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:var(--brand-ink);color:#fff;padding:11px 20px;border-radius:12px;font-weight:600;font-size:13.5px;box-shadow:0 10px 30px rgba(0,0,0,.25);z-index:99";
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 2000);
}
function slug(s: string) { return s.toLowerCase().normalize("NFKD").replace(/[^\w]+/g, "_").replace(/^_|_$/g, "") || "campo"; }
function bandCls(band: string | null) {
  return band === "alta" ? { bg: "#e7f7f0", c: "#0f7a54", label: "Alta" } : band === "media" ? { bg: "#fdf3dd", c: "#8a6b16", label: "Media" } : { bg: "#fde8e7", c: "#b23a3a", label: "Baja" };
}
const input = { border: "1px solid var(--line)" } as const;
const btnPri = { background: "var(--accent)" } as const;
function Card({ title, right, children }: { title: string; right?: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="rounded-card p-[18px] mb-4" style={{ background: "var(--surface)", border: "1px solid var(--line)", boxShadow: "0 1px 2px rgba(20,18,40,.04)" }}>
      <div className="flex items-center justify-between mb-3"><h2 className="text-[16px] m-0 font-bold">{title}</h2>{right}</div>
      {children}
    </div>
  );
}

export function AdminLeads() {
  const [clients, setClients] = useState<Client[]>([]);
  const [clientId, setClientId] = useState<number | null>(null);
  const [data, setData] = useState<ListResp | null>(null);
  const [mode, setMode] = useState<string>("agency_managed");
  const [openLead, setOpenLead] = useState<string | null>(null);
  const [showCfg, setShowCfg] = useState(false);
  const [showNew, setShowNew] = useState(false);

  useEffect(() => {
    api<Client[]>("/admin/clients").then((cs) => { setClients(cs); if (cs[0]) setClientId(cs[0].id); }).catch(() => toast("Error cargando clientes"));
  }, []);

  const load = useCallback(async () => {
    if (!clientId) return;
    try {
      const d = await api<ListResp>(`/admin/clients/${clientId}/leads`);
      setData(d); setMode(d.lead_mode);
    } catch { toast("Error cargando leads"); }
  }, [clientId]);
  useEffect(() => { load(); }, [load]);

  async function changeMode(m: string) {
    if (!clientId) return;
    setMode(m);
    await api(`/admin/clients/${clientId}`, { method: "PATCH", body: JSON.stringify({ lead_mode: m }) });
    toast(m === "agency_managed" ? "Modo: Zuhma califica y libera" : "Modo: el cliente ve y califica todo");
    load();
  }
  async function act(id: string, path: string, body: object, msg: string) {
    if (!clientId) return;
    try { await api(`/admin/clients/${clientId}/leads/${encodeURIComponent(id)}/${path}`, { method: "POST", body: JSON.stringify(body) }); toast(msg); load(); }
    catch { toast("No se pudo actualizar"); }
  }

  if (openLead && clientId) {
    return <LeadDetail leadId={openLead} canEdit adminActions onBack={() => { setOpenLead(null); load(); }} basePath={`/admin/clients/${clientId}/leads`} configPath={`/admin/clients/${clientId}/lead-config`} />;
  }

  const agency = mode === "agency_managed";

  return (
    <div className="px-[30px] pt-[26px] pb-[60px] max-w-[1180px]">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h1 className="text-[27px] tracking-tight m-0 mb-[3px] font-bold">Leads por cliente</h1>
          <p className="m-0" style={{ color: "var(--muted)" }}>El admin ve <b>todos</b> los leads; libera al cliente según el modelo.</p>
        </div>
        <div className="flex gap-2 items-center">
          <select value={clientId ?? ""} onChange={(e) => setClientId(Number(e.target.value))} className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={input}>
            {clients.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
      </div>

      <Card title="Modelo de leads del cliente">
        <div className="flex gap-3 flex-wrap items-center">
          <label className={`flex items-center gap-2 text-[13px] px-3 py-2 rounded-[10px] cursor-pointer`} style={{ border: `1px solid ${agency ? "var(--accent)" : "var(--line)"}` }}>
            <input type="radio" checked={agency} onChange={() => changeMode("agency_managed")} /> <b>Zuhma califica</b> — el cliente ve solo los liberados (Nextcore)
          </label>
          <label className={`flex items-center gap-2 text-[13px] px-3 py-2 rounded-[10px] cursor-pointer`} style={{ border: `1px solid ${!agency ? "var(--accent)" : "var(--line)"}` }}>
            <input type="radio" checked={!agency} onChange={() => changeMode("client_managed")} /> <b>El cliente califica</b> — ve todos los leads (Cicadehp)
          </label>
        </div>
      </Card>

      <Card
        title={`Leads (${data?.counts.all ?? 0})`}
        right={
          <div className="flex gap-2">
            <button onClick={() => setShowCfg((v) => !v)} className="text-[12.5px] font-semibold px-[11px] py-[6px] rounded-[10px]" style={input as object}>⚙ Campos de calificación</button>
            <button onClick={() => setShowNew((v) => !v)} className="text-[12.5px] font-semibold px-[11px] py-[6px] rounded-[10px] text-white" style={btnPri}>+ Nuevo lead</button>
          </div>
        }
      >
        {showNew && clientId && <NewLead clientId={clientId} onDone={() => { setShowNew(false); load(); }} />}
        {agency && <div className="text-[12.5px] mb-3 px-3 py-2 rounded-[10px]" style={{ background: "#fff7e6", color: "#8a6d1f", border: "1px solid #f6e2b4" }}>En este modo, el cliente <b>solo verá</b> los leads que marques como <b>Liberados</b>.</div>}
        <table className="w-full">
          <thead><tr>{["Lead", "Propensidad", "Canal", "Estado", agency ? "Liberado" : "", ""].map((h, i) => <th key={i} className="text-left text-[11px] uppercase font-bold pb-2" style={{ color: "var(--faint)" }}>{h}</th>)}</tr></thead>
          <tbody>
            {data?.leads.map((l) => {
              const bd = bandCls(l.band);
              return (
                <tr key={l.id}>
                  <td className="py-3" style={{ borderTop: "1px solid var(--line)" }}><div className="font-semibold text-[13.5px]">{l.name}</div><div className="text-[12px] font-mono" style={{ color: "var(--faint)" }}>{l.id}</div></td>
                  <td className="py-3" style={{ borderTop: "1px solid var(--line)" }}><span className="text-[12px] font-bold px-[9px] py-[3px] rounded-[20px]" style={{ background: bd.bg, color: bd.c }}>{bd.label} {l.affinity ?? "—"}/18</span></td>
                  <td className="py-3 text-[13px]" style={{ borderTop: "1px solid var(--line)" }}>{l.channel}</td>
                  <td className="py-3 text-[13px]" style={{ borderTop: "1px solid var(--line)" }}>{l.status}</td>
                  {agency && (
                    <td className="py-3" style={{ borderTop: "1px solid var(--line)" }}>
                      {l.released
                        ? <button onClick={() => act(l.id, "release", { released: false }, "Retirado del cliente")} className="text-[12px] font-semibold px-[9px] py-[4px] rounded-[8px]" style={{ background: "#e7f7f0", color: "#0f7a54" }}>✓ Liberado</button>
                        : <button onClick={() => act(l.id, "release", { released: true }, "Liberado al cliente ✓")} className="text-[12px] font-semibold px-[9px] py-[4px] rounded-[8px] text-white" style={btnPri}>Liberar</button>}
                    </td>
                  )}
                  <td className="py-3 text-right" style={{ borderTop: "1px solid var(--line)" }}><button onClick={() => setOpenLead(l.id)} className="text-[12.5px] font-semibold px-[11px] py-[6px] rounded-[10px]" style={input as object}>Ver detalle →</button></td>
                </tr>
              );
            })}
            {data && data.leads.length === 0 && <tr><td colSpan={6} className="py-6 text-center text-[13px]" style={{ color: "var(--muted)" }}>Sin leads para este cliente.</td></tr>}
          </tbody>
        </table>
      </Card>

      {clientId && <LeadSources clientId={clientId} />}
      {clientId && <MetaConnect clientId={clientId} />}
      {clientId && <ConversionConfigPanel clientId={clientId} />}
      {showCfg && clientId && <ConfigEditor clientId={clientId} />}
    </div>
  );
}

type ConvCfg = {
  meta_ready: boolean; google_ready: boolean; meta_pixel_id: string | null; meta_test_event_code: string | null; has_meta_token: boolean;
  google_customer_id: string | null; google_login_customer_id: string | null; google_conversion_action_id: string | null;
  has_google_dev_token: boolean; google_client_id: string | null; has_google_secret: boolean; has_google_refresh: boolean;
};

function ConversionConfigPanel({ clientId }: { clientId: number }) {
  const [cfg, setCfg] = useState<ConvCfg | null>(null);
  const [meta, setMeta] = useState({ meta_pixel_id: "", meta_capi_token: "", meta_test_event_code: "" });
  const [g, setG] = useState({ google_customer_id: "", google_login_customer_id: "", google_conversion_action_id: "", google_developer_token: "", google_client_id: "", google_client_secret: "", google_refresh_token: "" });
  const [testResult, setTestResult] = useState<string | null>(null);

  async function testMeta() {
    setTestResult("Enviando evento de prueba…");
    try {
      const r = await api<{ ok: boolean; detail: string; test_event_code: string | null }>(`/admin/clients/${clientId}/conversion-config/test-meta`, { method: "POST" });
      setTestResult(`${r.ok ? "✅" : "❌"} ${r.detail}${r.test_event_code ? `  ·  test_event_code=${r.test_event_code}` : "  ·  (sin test_event_code)"}`);
    } catch (e) { setTestResult(e instanceof Error ? e.message.replace(/^API \d+: /, "") : "Error"); }
  }

  const load = useCallback(() => { api<ConvCfg>(`/admin/clients/${clientId}/conversion-config`).then((c) => { setCfg(c); setMeta({ meta_pixel_id: c.meta_pixel_id || "", meta_capi_token: "", meta_test_event_code: c.meta_test_event_code || "" }); setG((s) => ({ ...s, google_customer_id: c.google_customer_id || "", google_login_customer_id: c.google_login_customer_id || "", google_conversion_action_id: c.google_conversion_action_id || "", google_client_id: c.google_client_id || "" })); }).catch(() => {}); }, [clientId]);
  useEffect(() => { load(); }, [load]);

  async function save(payload: object, label: string) {
    const clean = Object.fromEntries(Object.entries(payload).filter(([, v]) => v !== "" && v != null));
    try {
      const r = await api<{ flushed?: { sent: number; failed: number } }>(`/admin/clients/${clientId}/conversion-config`, { method: "PUT", body: JSON.stringify(clean) });
      const f = r.flushed;
      toast(f && (f.sent || f.failed) ? `${label} · ${f.sent} enviados, ${f.failed} con error` : label);
      load();
    } catch { toast("No se pudo guardar"); }
  }

  const badge = (ok: boolean) => <span className="text-[11px] font-bold px-[8px] py-[2px] rounded-[20px]" style={ok ? { background: "#e7f7f0", color: "#0f7a54" } : { background: "#fdf3dd", color: "#8a6b16" }}>{ok ? "Listo" : "Falta config"}</span>;

  return (
    <Card title="Motor de conversiones (CAPI / Google Ads)">
      <div className="text-[12.5px] mb-3" style={{ color: "var(--muted)" }}>Al <b>calificar</b> un lead, el portal dispara el evento de conversión server-side con el mismo Lead ID. Configura las credenciales por cliente (secretos cifrados en reposo).</div>
      <div className="grid gap-4" style={{ gridTemplateColumns: "1fr 1fr", alignItems: "start" }}>
        <div className="p-3 rounded-[10px]" style={{ border: "1px solid var(--line)" }}>
          <div className="flex items-center justify-between mb-2"><div className="font-semibold text-[13.5px]">Meta CAPI</div>{cfg && badge(cfg.meta_ready)}</div>
          <div className="flex flex-col gap-2">
            <input value={meta.meta_pixel_id} onChange={(e) => setMeta({ ...meta, meta_pixel_id: e.target.value })} placeholder="Pixel / Dataset ID" className="px-3 py-2 rounded-[8px] text-[13px] outline-none" style={input} />
            <input value={meta.meta_capi_token} onChange={(e) => setMeta({ ...meta, meta_capi_token: e.target.value })} placeholder={cfg?.has_meta_token ? "CAPI token (guardado — deja vacío para no cambiar)" : "CAPI access token"} className="px-3 py-2 rounded-[8px] text-[13px] outline-none" style={input} />
            <input value={meta.meta_test_event_code} onChange={(e) => setMeta({ ...meta, meta_test_event_code: e.target.value })} placeholder="Test event code (opcional)" className="px-3 py-2 rounded-[8px] text-[13px] outline-none" style={input} />
            <div className="flex gap-2">
              <button onClick={() => save(meta, "Meta CAPI guardado ✓")} className="px-3 py-2 rounded-[8px] text-[13px] font-semibold text-white" style={btnPri}>Guardar Meta</button>
              {cfg?.meta_ready && <button onClick={testMeta} className="px-3 py-2 rounded-[8px] text-[13px] font-semibold" style={{ border: "1px solid var(--line)" }}>Probar Meta CAPI</button>}
            </div>
            {testResult && <div className="text-[11.5px] font-mono mt-1 p-2 rounded-[8px]" style={{ background: "var(--bg)", border: "1px solid var(--line)", wordBreak: "break-all" }}>{testResult}</div>}
          </div>
        </div>
        <div className="p-3 rounded-[10px]" style={{ border: "1px solid var(--line)" }}>
          <div className="flex items-center justify-between mb-2"><div className="font-semibold text-[13.5px]">Google Ads (offline)</div>{cfg && badge(cfg.google_ready)}</div>
          <div className="flex flex-col gap-2">
            <input value={g.google_customer_id} onChange={(e) => setG({ ...g, google_customer_id: e.target.value })} placeholder="Customer ID (sin guiones)" className="px-3 py-2 rounded-[8px] text-[13px] outline-none" style={input} />
            <input value={g.google_login_customer_id} onChange={(e) => setG({ ...g, google_login_customer_id: e.target.value })} placeholder="Login Customer ID (MCC, opcional)" className="px-3 py-2 rounded-[8px] text-[13px] outline-none" style={input} />
            <input value={g.google_conversion_action_id} onChange={(e) => setG({ ...g, google_conversion_action_id: e.target.value })} placeholder="Conversion Action ID" className="px-3 py-2 rounded-[8px] text-[13px] outline-none" style={input} />
            <input value={g.google_developer_token} onChange={(e) => setG({ ...g, google_developer_token: e.target.value })} placeholder={cfg?.has_google_dev_token ? "Developer token (guardado)" : "Developer token"} className="px-3 py-2 rounded-[8px] text-[13px] outline-none" style={input} />
            <input value={g.google_client_id} onChange={(e) => setG({ ...g, google_client_id: e.target.value })} placeholder="OAuth Client ID" className="px-3 py-2 rounded-[8px] text-[13px] outline-none" style={input} />
            <input value={g.google_client_secret} onChange={(e) => setG({ ...g, google_client_secret: e.target.value })} placeholder={cfg?.has_google_secret ? "Client secret (guardado)" : "OAuth Client secret"} className="px-3 py-2 rounded-[8px] text-[13px] outline-none" style={input} />
            <input value={g.google_refresh_token} onChange={(e) => setG({ ...g, google_refresh_token: e.target.value })} placeholder={cfg?.has_google_refresh ? "Refresh token (guardado)" : "OAuth Refresh token"} className="px-3 py-2 rounded-[8px] text-[13px] outline-none" style={input} />
            <button onClick={() => save(g, "Google Ads guardado ✓")} className="px-3 py-2 rounded-[8px] text-[13px] font-semibold text-white self-start" style={btnPri}>Guardar Google</button>
          </div>
        </div>
      </div>
    </Card>
  );
}

type MetaCfg = { callback_path: string; verify_token_set: boolean; app_configured: boolean; graph_version: string };
type MetaPage = { id: number; page_id: string; page_name: string | null; is_active: boolean };
type MetaApp = { configured: boolean; app_id: string | null; has_secret: boolean; verify_token: string | null; webhook_path: string | null };

function MetaConnect({ clientId }: { clientId: number }) {
  const [cfg, setCfg] = useState<MetaCfg | null>(null);
  const [pages, setPages] = useState<MetaPage[]>([]);
  const [app, setApp] = useState<MetaApp | null>(null);
  const [appForm, setAppForm] = useState({ app_id: "", app_secret: "", verify_token: "" });
  const [f, setF] = useState({ page_id: "", page_name: "", page_access_token: "" });

  const load = useCallback(async () => {
    try {
      const [c, p, a] = await Promise.all([
        api<MetaCfg>("/admin/meta/config"),
        api<MetaPage[]>(`/admin/clients/${clientId}/meta-pages`),
        api<MetaApp>(`/admin/clients/${clientId}/meta-app`),
      ]);
      setCfg(c); setPages(p); setApp(a);
    } catch { /* noop */ }
  }, [clientId]);
  useEffect(() => { load(); }, [load]);

  async function saveApp(e: React.FormEvent) {
    e.preventDefault();
    if (!appForm.app_id.trim() || !appForm.app_secret.trim() || !appForm.verify_token.trim()) return;
    try {
      await api(`/admin/clients/${clientId}/meta-app`, { method: "PUT", body: JSON.stringify(appForm) });
      setAppForm({ app_id: "", app_secret: "", verify_token: "" });
      toast("App del cliente guardada ✓"); load();
    } catch { toast("No se pudo guardar la App"); }
  }
  async function clearApp() {
    if (!confirm("¿Quitar la App propia? El cliente volverá a usar la App global de Zuhma.")) return;
    await api(`/admin/clients/${clientId}/meta-app`, { method: "DELETE" }); toast("App propia quitada"); load();
  }

  async function connect(e: React.FormEvent) {
    e.preventDefault();
    if (!f.page_id.trim() || !f.page_access_token.trim()) return;
    try {
      const r = await api<{ subscribe: { ok: boolean; detail?: string } }>(`/admin/clients/${clientId}/meta-pages`, { method: "POST", body: JSON.stringify(f) });
      toast(r.subscribe?.ok ? "Página conectada y suscrita ✓" : "Página guardada; revisa la suscripción");
      setF({ page_id: "", page_name: "", page_access_token: "" });
      load();
    } catch (err) { toast(err instanceof Error ? err.message.replace(/^API \d+: /, "").slice(0, 90) : "No se pudo conectar"); }
  }
  async function disconnect(pk: number) {
    await api(`/admin/clients/${clientId}/meta-pages/${pk}`, { method: "DELETE" }); toast("Página desconectada"); load();
  }

  const ownApp = app?.configured && app.webhook_path;
  const callback = ownApp ? `${API_BASE}${app!.webhook_path}` : cfg ? `${API_BASE}${cfg.callback_path}` : "…";

  return (
    <Card title="Meta Lead Ads (integración nativa)">
      <div className="text-[12.5px] mb-3" style={{ color: "var(--muted)" }}>
        Los leads de formularios de Meta llegan <b>directo</b> aquí (sin n8n). {ownApp ? "Este cliente usa su App propia." : "Este cliente usa la App global de Zuhma."} Configura el webhook en la App de Meta y conecta la página.
      </div>

      <div className="p-3 rounded-[10px] mb-4" style={{ background: ownApp ? "var(--accent-soft)" : "var(--bg)", border: `1px solid ${ownApp ? "#f8d3c8" : "var(--line)"}` }}>
        <div className="text-[11px] font-bold uppercase mb-1" style={{ color: "var(--faint)" }}>App de Meta propia del cliente (opcional)</div>
        {ownApp ? (
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="text-[12.5px]">App ID <b>{app!.app_id}</b> · verify token <code>{app!.verify_token}</code> · secret {app!.has_secret ? "✅" : "—"}</div>
            <button onClick={clearApp} className="text-[12px] font-semibold" style={{ color: "var(--bad,#e34948)" }}>Quitar App propia</button>
          </div>
        ) : (
          <form onSubmit={saveApp} className="flex gap-2 flex-wrap items-end mt-1">
            <Field label="App ID"><input value={appForm.app_id} onChange={(e) => setAppForm({ ...appForm, app_id: e.target.value })} className="px-3 py-2 rounded-[8px] text-[13px] outline-none" style={input} /></Field>
            <Field label="App Secret"><input value={appForm.app_secret} onChange={(e) => setAppForm({ ...appForm, app_secret: e.target.value })} className="px-3 py-2 rounded-[8px] text-[13px] outline-none min-w-[200px]" style={input} placeholder="secreto de la App" /></Field>
            <Field label="Verify Token"><input value={appForm.verify_token} onChange={(e) => setAppForm({ ...appForm, verify_token: e.target.value })} className="px-3 py-2 rounded-[8px] text-[13px] outline-none" style={input} placeholder="invéntalo" /></Field>
            <button type="submit" className="px-3 py-2 rounded-[8px] text-[13px] font-semibold text-white" style={btnPri}>Usar App propia</button>
          </form>
        )}
      </div>
      <div className="grid gap-3 mb-4" style={{ gridTemplateColumns: "1fr 1fr" }}>
        <div className="p-3 rounded-[10px]" style={{ background: "var(--bg)", border: "1px solid var(--line)" }}>
          <div className="text-[11px] font-bold uppercase mb-1" style={{ color: "var(--faint)" }}>Webhook (Meta → Developers → Webhooks)</div>
          <div className="flex items-center gap-2"><code className="flex-1 text-[12px] truncate">{callback}</code><button onClick={() => { navigator.clipboard.writeText(callback); toast("Copiado"); }} className="px-2 py-1 rounded-[7px] text-white text-[11px] font-semibold" style={btnPri}>Copiar</button></div>
          <div className="text-[12px] mt-1">Campo a suscribir: <code>leadgen</code></div>
        </div>
        <div className="p-3 rounded-[10px]" style={{ background: "var(--bg)", border: "1px solid var(--line)" }}>
          <div className="text-[11px] font-bold uppercase mb-1" style={{ color: "var(--faint)" }}>Estado de la App</div>
          <div className="text-[12.5px]">App (ID+Secret): {cfg?.app_configured ? "✅ configurada" : "⚠️ falta META_APP_ID/SECRET"}</div>
          <div className="text-[12.5px]">Verify token: {cfg?.verify_token_set ? "✅ definido" : "⚠️ falta META_VERIFY_TOKEN"}</div>
          <div className="text-[12px]" style={{ color: "var(--faint)" }}>Graph {cfg?.graph_version}</div>
        </div>
      </div>

      <form onSubmit={connect} className="flex gap-3 flex-wrap items-end mb-4">
        <Field label="Page ID"><input value={f.page_id} onChange={(e) => setF({ ...f, page_id: e.target.value })} className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={input} placeholder="1234567890" /></Field>
        <Field label="Nombre (opcional)"><input value={f.page_name} onChange={(e) => setF({ ...f, page_name: e.target.value })} className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={input} /></Field>
        <Field label="Page Access Token"><input value={f.page_access_token} onChange={(e) => setF({ ...f, page_access_token: e.target.value })} className="px-3 py-2 rounded-[10px] text-[13px] outline-none min-w-[240px]" style={input} placeholder="EAAG… (larga duración)" /></Field>
        <button type="submit" className="px-4 py-2 rounded-[10px] text-[13px] font-semibold text-white" style={btnPri}>Conectar página</button>
      </form>

      {pages.filter((p) => p.is_active).length > 0 && (
        <table className="w-full"><thead><tr>{["Página", "Page ID", ""].map((h) => <th key={h} className="text-left text-[11px] uppercase font-bold pb-2" style={{ color: "var(--faint)" }}>{h}</th>)}</tr></thead><tbody>
          {pages.filter((p) => p.is_active).map((p) => (
            <tr key={p.id}>
              <td className="py-2 text-[13px] font-semibold" style={{ borderTop: "1px solid var(--line)" }}>{p.page_name || "—"}</td>
              <td className="py-2 text-[12px] font-mono" style={{ borderTop: "1px solid var(--line)", color: "var(--muted)" }}>{p.page_id}</td>
              <td className="py-2 text-right" style={{ borderTop: "1px solid var(--line)" }}><button onClick={() => disconnect(p.id)} className="text-[12px] font-semibold" style={{ color: "var(--bad,#e34948)" }}>Desconectar</button></td>
            </tr>
          ))}
        </tbody></table>
      )}
    </Card>
  );
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "";

function LeadSources({ clientId }: { clientId: number }) {
  const [path, setPath] = useState<string | null>(null);
  const load = useCallback(() => { api<{ path: string }>(`/admin/clients/${clientId}/ingest`).then((r) => setPath(r.path)).catch(() => {}); }, [clientId]);
  useEffect(() => { load(); }, [load]);
  const url = path ? `${API_BASE}${path}` : "…";

  async function rotate() {
    if (!confirm("¿Rotar el token? Los orígenes ya configurados dejarán de funcionar hasta actualizar la URL.")) return;
    const r = await api<{ path: string }>(`/admin/clients/${clientId}/ingest/rotate`, { method: "POST" });
    setPath(r.path); toast("Token rotado");
  }

  const sources = [
    { t: "Formulario de cliente potencial de Meta", d: "Meta Lead Ads → n8n (nodo Meta Lead Ads) → POST a este webhook. El Lead ID y fbclid/fbc viajan en el payload." },
    { t: "Chatwoot (self-host)", d: "Webhook de Chatwoot (Conversation Created) → n8n → POST a este webhook. Reusa tu flujo chatwoot/whatsapp existente." },
    { t: "WordPress · Fluent Forms / Contact Form 7", d: "Instala el snippet JS (captura gclid/fbclid/fbc/fbp/utm en campos ocultos) y añade un webhook del formulario (o n8n form→lead) que haga POST aquí con esos campos." },
    { t: "Alta manual", d: "El botón \"+ Nuevo lead\" de arriba, o el detalle del lead." },
  ];

  return (
    <Card title="Fuentes de leads (ingesta)" right={<button onClick={rotate} className="text-[12px] font-semibold px-[10px] py-[5px] rounded-[8px]" style={{ border: "1px solid var(--line)", color: "var(--bad,#e34948)" }}>Rotar token</button>}>
      <div className="text-[12.5px] mb-2" style={{ color: "var(--muted)" }}>Todos los orígenes hacen <b>POST</b> a este webhook único del cliente (JSON con contacto + atribución):</div>
      <div className="flex items-center gap-2 mb-4 p-3 rounded-[10px]" style={{ background: "var(--bg)", border: "1px solid var(--line)" }}>
        <code className="flex-1 text-[12.5px] truncate">POST {url}</code>
        <button onClick={() => { navigator.clipboard.writeText(url); toast("URL copiada"); }} className="px-3 py-1 rounded-[8px] text-white text-[12px] font-semibold" style={btnPri}>Copiar</button>
      </div>
      <div className="grid gap-3" style={{ gridTemplateColumns: "1fr 1fr" }}>
        {sources.map((s) => (
          <div key={s.t} className="p-3 rounded-[10px]" style={{ border: "1px solid var(--line)" }}>
            <div className="font-semibold text-[13.5px] mb-1">{s.t}</div>
            <div className="text-[12.5px]" style={{ color: "var(--muted)" }}>{s.d}</div>
          </div>
        ))}
      </div>
      <div className="text-[12px] mt-3" style={{ color: "var(--faint)" }}>Campos aceptados: contact_name (req), email, phone, company_name, website, cargo, channel, description, answers, gclid, fbclid, fbc, fbp, utm_source, utm_medium, utm_campaign.</div>
    </Card>
  );
}

function NewLead({ clientId, onDone }: { clientId: number; onDone: () => void }) {
  const [f, setF] = useState({ contact_name: "", company_name: "", email: "", phone: "", channel: "Meta Ads" });
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!f.contact_name.trim()) return;
    try { await api(`/admin/clients/${clientId}/leads`, { method: "POST", body: JSON.stringify(f) }); toast("Lead creado ✓"); onDone(); }
    catch (err) { toast(err instanceof Error ? err.message.replace(/^API \d+: /, "").slice(0, 90) : "No se pudo crear"); }
  }
  return (
    <form onSubmit={submit} className="flex gap-3 flex-wrap items-end mb-4 pb-4" style={{ borderBottom: "1px solid var(--line)" }}>
      <Field label="Contacto"><input required value={f.contact_name} onChange={(e) => setF({ ...f, contact_name: e.target.value })} className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={input} /></Field>
      <Field label="Empresa"><input value={f.company_name} onChange={(e) => setF({ ...f, company_name: e.target.value })} className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={input} /></Field>
      <Field label="Correo"><input value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={input} /></Field>
      <Field label="Teléfono"><input value={f.phone} onChange={(e) => setF({ ...f, phone: e.target.value })} className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={input} /></Field>
      <Field label="Canal"><select value={f.channel} onChange={(e) => setF({ ...f, channel: e.target.value })} className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={input}><option>Meta Ads</option><option>Google Ads</option><option>WhatsApp</option><option>Orgánico</option></select></Field>
      <button type="submit" className="px-4 py-2 rounded-[10px] text-[13px] font-semibold text-white" style={btnPri}>Guardar</button>
    </form>
  );
}
function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <div className="flex flex-col gap-1"><label className="text-[11px] font-bold uppercase" style={{ color: "var(--faint)" }}>{label}</label>{children}</div>;
}

function ConfigEditor({ clientId }: { clientId: number }) {
  const [cfg, setCfg] = useState<Config | null>(null);
  const [q, setQ] = useState({ label: "", weight: 2, options: "Sí:2\nNo:0" });
  const [req, setReq] = useState({ label: "", type: "text" });

  const load = useCallback(() => { api<Config>(`/admin/clients/${clientId}/lead-config`).then(setCfg).catch(() => {}); }, [clientId]);
  useEffect(() => { load(); }, [load]);

  async function put(next: Config) {
    await api(`/admin/clients/${clientId}/lead-config`, { method: "PUT", body: JSON.stringify(next) });
    setCfg(next); toast("Config guardada ✓");
  }
  function addQuestion() {
    if (!cfg || !q.label.trim()) return;
    const options = q.options.split("\n").map((l) => l.trim()).filter(Boolean).map((l) => { const [lab, pts] = l.split(":"); return { value: slug(lab), label: lab.trim(), points: Number(pts ?? 0) }; });
    const next = { ...cfg, questions: [...cfg.questions, { key: slug(q.label), label: q.label.trim(), type: "select", section: "calificacion", weight: Number(q.weight), options }], max_score: (cfg.max_score ?? 0) + Number(q.weight) };
    put(next); setQ({ label: "", weight: 2, options: "Sí:2\nNo:0" });
  }
  function addReq() {
    if (!cfg || !req.label.trim()) return;
    const next = { ...cfg, info_fields: [...cfg.info_fields, { key: slug(req.label), label: req.label.trim(), type: req.type, section: "requerimiento" }] };
    put(next); setReq({ label: "", type: "text" });
  }
  function removeQ(key: string) {
    if (!cfg) return;
    const removed = cfg.questions.find((x) => x.key === key);
    put({ ...cfg, questions: cfg.questions.filter((x) => x.key !== key), max_score: (cfg.max_score ?? 0) - (removed?.weight ?? 0) });
  }
  function removeReq(key: string) { if (cfg) put({ ...cfg, info_fields: cfg.info_fields.filter((x) => x.key !== key) }); }

  if (!cfg) return null;
  return (
    <Card title={`Campos de calificación · máx ${cfg.max_score ?? 18}`}>
      <div className="grid gap-4" style={{ gridTemplateColumns: "1fr 1fr", alignItems: "start" }}>
        <div>
          <div className="text-[12px] font-bold uppercase mb-2" style={{ color: "var(--faint)" }}>Preguntas con puntaje</div>
          {cfg.questions.map((x) => (
            <div key={x.key} className="flex items-center justify-between text-[13px] py-2" style={{ borderTop: "1px solid var(--line)" }}>
              <span>{x.label} <span style={{ color: "var(--faint)" }}>(máx {x.weight})</span></span>
              <button onClick={() => removeQ(x.key)} style={{ color: "var(--bad,#e34948)" }}>✕</button>
            </div>
          ))}
          <div className="mt-3 flex flex-col gap-2 p-3 rounded-[10px]" style={{ background: "var(--bg)" }}>
            <input value={q.label} onChange={(e) => setQ({ ...q, label: e.target.value })} placeholder="Nueva pregunta (ej. ¿Usa la nube?)" className="px-3 py-2 rounded-[8px] text-[13px] outline-none" style={input} />
            <div className="flex gap-2 items-center"><span className="text-[12px]" style={{ color: "var(--muted)" }}>Peso máx</span><input type="number" value={q.weight} onChange={(e) => setQ({ ...q, weight: Number(e.target.value) })} className="w-[70px] px-2 py-1 rounded-[8px] text-[13px] outline-none" style={input} /></div>
            <textarea value={q.options} onChange={(e) => setQ({ ...q, options: e.target.value })} placeholder="Opción:puntos (una por línea)" rows={3} className="px-3 py-2 rounded-[8px] text-[13px] outline-none font-mono" style={input} />
            <button onClick={addQuestion} className="px-3 py-2 rounded-[8px] text-[13px] font-semibold text-white self-start" style={btnPri}>+ Agregar pregunta</button>
          </div>
        </div>
        <div>
          <div className="text-[12px] font-bold uppercase mb-2" style={{ color: "var(--faint)" }}>Detalles de requerimiento</div>
          {cfg.info_fields.map((x) => (
            <div key={x.key} className="flex items-center justify-between text-[13px] py-2" style={{ borderTop: "1px solid var(--line)" }}>
              <span>{x.label} <span style={{ color: "var(--faint)" }}>({x.type})</span></span>
              <button onClick={() => removeReq(x.key)} style={{ color: "var(--bad,#e34948)" }}>✕</button>
            </div>
          ))}
          <div className="mt-3 flex flex-col gap-2 p-3 rounded-[10px]" style={{ background: "var(--bg)" }}>
            <input value={req.label} onChange={(e) => setReq({ ...req, label: e.target.value })} placeholder="Nuevo detalle (ej. Región)" className="px-3 py-2 rounded-[8px] text-[13px] outline-none" style={input} />
            <select value={req.type} onChange={(e) => setReq({ ...req, type: e.target.value })} className="px-3 py-2 rounded-[8px] text-[13px] outline-none" style={input}><option value="text">Texto</option><option value="number">Número</option><option value="boolean">Sí/No</option></select>
            <button onClick={addReq} className="px-3 py-2 rounded-[8px] text-[13px] font-semibold text-white self-start" style={btnPri}>+ Agregar detalle</button>
          </div>
        </div>
      </div>
    </Card>
  );
}
