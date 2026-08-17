"use client";

import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";

type Client = { id: number; slug: string; name: string; plan: string | null; status: string; is_active: boolean; odoo_partner_id: number; users: number };
type Partner = { id: number; name: string; email: string | false; is_company: boolean };
type User = { id: number; email: string; full_name: string | null; role: string };
type Service = { id: number; metric: string; label: string; used: number; total: number; period: string };

function toast(msg: string) {
  const t = document.createElement("div");
  t.textContent = msg;
  t.style.cssText = "position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:var(--brand-ink);color:#fff;padding:11px 20px;border-radius:12px;font-weight:600;font-size:13.5px;box-shadow:0 10px 30px rgba(0,0,0,.25);z-index:99";
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 2200);
}
function Card({ title, right, children }: { title: string; right?: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="rounded-card p-[18px] mb-4" style={{ background: "var(--surface)", border: "1px solid var(--line)", boxShadow: "0 1px 2px rgba(20,18,40,.04)" }}>
      <div className="flex items-center justify-between mb-3"><h2 className="text-[16px] m-0 font-bold">{title}</h2>{right}</div>
      {children}
    </div>
  );
}
const input = { border: "1px solid var(--line)" } as const;
const btnPri = { background: "var(--accent)" } as const;

export function ClientesAdmin({ onImpersonate }: { onImpersonate: (id: number, name: string) => void }) {
  const [clients, setClients] = useState<Client[] | null>(null);
  const [openId, setOpenId] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);

  const load = useCallback(async () => {
    try { setClients(await api<Client[]>("/admin/clients")); }
    catch (e) { toast(e instanceof Error && e.message.includes("403") ? "Requiere rol admin" : "Error cargando clientes"); }
  }, []);
  useEffect(() => { load(); }, [load]);

  if (openId) {
    const c = clients?.find((x) => x.id === openId);
    return c ? <ClientDetail client={c} onBack={() => { setOpenId(null); load(); }} onImpersonate={onImpersonate} /> : null;
  }

  return (
    <div className="px-[30px] pt-[26px] pb-[60px] max-w-[1180px]">
      <div className="flex items-start justify-between mb-5">
        <div>
          <h1 className="text-[27px] tracking-tight m-0 mb-[3px] font-bold">Clientes</h1>
          <p className="m-0" style={{ color: "var(--muted)" }}>{clients?.length ?? 0} clientes · alta, servicios e invitaciones</p>
        </div>
        <button onClick={() => setCreating((v) => !v)} className="text-[13px] font-semibold px-[13px] py-[8px] rounded-[10px] text-white" style={btnPri}>+ Nuevo cliente</button>
      </div>

      {creating && <NewClientForm onCreated={() => { setCreating(false); load(); }} />}

      <Card title="Todos los clientes">
        <table className="w-full">
          <thead><tr>{["Cliente", "Plan", "Estado", "Usuarios", "Odoo", ""].map((h) => <th key={h} className="text-left text-[11px] uppercase font-bold pb-2" style={{ color: "var(--faint)" }}>{h}</th>)}</tr></thead>
          <tbody>
            {clients?.map((c) => (
              <tr key={c.id}>
                <td className="py-3 font-semibold text-[13.5px]" style={{ borderTop: "1px solid var(--line)" }}>{c.name}<div className="text-[12px] font-normal" style={{ color: "var(--faint)" }}>{c.slug}</div></td>
                <td className="py-3 text-[13px]" style={{ borderTop: "1px solid var(--line)" }}>{c.plan ?? "—"}</td>
                <td className="py-3" style={{ borderTop: "1px solid var(--line)" }}><span className="text-[12px] font-semibold px-[9px] py-[3px] rounded-[20px]" style={c.is_active ? { background: "#e7f7f0", color: "#0f7a54" } : { background: "#fdf3dd", color: "#8a6b16" }}>{c.status}</span></td>
                <td className="py-3 text-[13px]" style={{ borderTop: "1px solid var(--line)" }}>{c.users}</td>
                <td className="py-3 text-[12px] font-mono" style={{ borderTop: "1px solid var(--line)", color: "var(--muted)" }}>{c.odoo_partner_id || "—"}</td>
                <td className="py-3 text-right" style={{ borderTop: "1px solid var(--line)" }}>
                  <button onClick={() => setOpenId(c.id)} className="text-[12.5px] font-semibold px-[11px] py-[6px] rounded-[10px]" style={{ border: "1px solid var(--line)" }}>Gestionar →</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

function NewClientForm({ onCreated }: { onCreated: () => void }) {
  const [name, setName] = useState("");
  const [plan, setPlan] = useState("Growth B2B");
  const [partnerId, setPartnerId] = useState<number | null>(null);
  const [q, setQ] = useState("");
  const [results, setResults] = useState<Partner[]>([]);

  async function search(v: string) {
    setQ(v); setPartnerId(null);
    if (v.trim().length < 2) { setResults([]); return; }
    try { setResults(await api<Partner[]>(`/admin/odoo-partners?q=${encodeURIComponent(v)}`)); } catch { setResults([]); }
  }
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      await api("/admin/clients", { method: "POST", body: JSON.stringify({ name, plan_name: plan, odoo_partner_id: partnerId }) });
      toast("Cliente creado ✓");
      onCreated();
    } catch (e) { toast(e instanceof Error ? e.message : "No se pudo crear"); }
  }

  return (
    <Card title="Nuevo cliente">
      <form onSubmit={submit} className="flex flex-col gap-3">
        <div className="flex gap-3 flex-wrap">
          <div className="flex flex-col gap-1 flex-1 min-w-[220px]">
            <label className="text-[11px] font-bold uppercase" style={{ color: "var(--faint)" }}>Nombre del cliente</label>
            <input required value={name} onChange={(e) => setName(e.target.value)} className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={input} placeholder="Empresa Cliente S.A." />
          </div>
          <div className="flex flex-col gap-1 min-w-[180px]">
            <label className="text-[11px] font-bold uppercase" style={{ color: "var(--faint)" }}>Plan</label>
            <select value={plan} onChange={(e) => setPlan(e.target.value)} className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={input}>
              <option>Growth B2B</option><option>Growth</option><option>Lite</option><option>A demanda</option>
            </select>
          </div>
        </div>
        <div className="flex flex-col gap-1 relative">
          <label className="text-[11px] font-bold uppercase" style={{ color: "var(--faint)" }}>Vincular con partner de Odoo (opcional)</label>
          <input value={q} onChange={(e) => search(e.target.value)} className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={input} placeholder="Busca por nombre o correo…" />
          {results.length > 0 && !partnerId && (
            <div className="absolute top-full left-0 right-0 z-10 mt-1 rounded-[10px] overflow-hidden" style={{ background: "var(--surface)", border: "1px solid var(--line)", boxShadow: "0 10px 30px rgba(20,18,40,.12)" }}>
              {results.map((p) => (
                <div key={p.id} onClick={() => { setPartnerId(p.id); setQ(`${p.name} (id ${p.id})`); setResults([]); }} className="px-3 py-2 text-[13px] cursor-pointer hover:bg-[var(--bg)]" style={{ borderTop: "1px solid var(--line)" }}>
                  <b>{p.name}</b> {p.is_company ? "· empresa" : ""} <span style={{ color: "var(--faint)" }}>{p.email || ""} · id {p.id}</span>
                </div>
              ))}
            </div>
          )}
          {partnerId && <span className="text-[12px]" style={{ color: "var(--good,#1baf7a)" }}>Vinculado a partner id {partnerId}</span>}
        </div>
        <div><button type="submit" className="px-4 py-2 rounded-[10px] text-[13px] font-semibold text-white" style={btnPri}>Crear cliente</button></div>
      </form>
    </Card>
  );
}

function ClientDetail({ client, onBack, onImpersonate }: { client: Client; onBack: () => void; onImpersonate: (id: number, name: string) => void }) {
  const [plan, setPlan] = useState(client.plan ?? "Growth B2B");
  const [statusVal, setStatusVal] = useState(client.status);
  const [users, setUsers] = useState<User[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [invite, setInvite] = useState({ email: "", full_name: "" });
  const [inviteLink, setInviteLink] = useState<string | null>(null);
  const [svc, setSvc] = useState({ label: "", total: 0 });

  const load = useCallback(async () => {
    try {
      const [u, s] = await Promise.all([api<User[]>(`/admin/clients/${client.id}/users`), api<Service[]>(`/admin/clients/${client.id}/services`)]);
      setUsers(u); setServices(s);
    } catch { /* noop */ }
  }, [client.id]);
  useEffect(() => { load(); }, [load]);

  async function saveClient() {
    try { await api(`/admin/clients/${client.id}`, { method: "PATCH", body: JSON.stringify({ plan_name: plan, status: statusVal }) }); toast("Cliente actualizado ✓"); }
    catch { toast("No se pudo guardar"); }
  }
  async function sendInvite(e: React.FormEvent) {
    e.preventDefault();
    if (!invite.email.trim()) return;
    try {
      const r = await api<{ status: string; action_link: string | null; message?: string }>(`/admin/clients/${client.id}/invite`, { method: "POST", body: JSON.stringify(invite) });
      setInviteLink(r.action_link);
      setInvite({ email: "", full_name: "" });
      toast(r.status === "reassigned" ? (r.message ?? "Reasignado") : "Invitación creada ✓");
      load();
    } catch (e) { toast(e instanceof Error ? e.message.replace(/^API \d+: /, "") : "No se pudo invitar"); }
  }
  async function addService(e: React.FormEvent) {
    e.preventDefault();
    if (!svc.label.trim()) return;
    try {
      await api(`/admin/clients/${client.id}/services`, { method: "POST", body: JSON.stringify({ metric: svc.label.toLowerCase().replace(/\s+/g, "_"), label: svc.label, total: Number(svc.total) }) });
      setSvc({ label: "", total: 0 }); toast("Servicio agregado ✓"); load();
    } catch { toast("No se pudo agregar"); }
  }

  return (
    <div className="px-[30px] pt-[26px] pb-[60px] max-w-[1180px]">
      <button onClick={onBack} className="text-[13px] font-semibold mb-4" style={{ color: "var(--muted)" }}>← Volver a clientes</button>
      <div className="flex items-center justify-between mb-4">
        <div><h1 className="text-[24px] tracking-tight m-0 font-bold">{client.name}</h1><span className="text-[12px] font-mono" style={{ color: "var(--muted)" }}>{client.slug} · Odoo partner {client.odoo_partner_id || "—"}</span></div>
        <button onClick={() => onImpersonate(client.id, client.name)} className="text-[13px] font-semibold px-[13px] py-[8px] rounded-[10px]" style={{ border: "1px solid var(--line)", background: "var(--accent-soft)", color: "var(--accent)" }}>👁 Ver como cliente</button>
      </div>

      <Card title="Datos del cliente">
        <div className="flex gap-4 flex-wrap items-end">
          <div className="flex flex-col gap-1"><label className="text-[11px] font-bold uppercase" style={{ color: "var(--faint)" }}>Plan</label>
            <select value={plan} onChange={(e) => setPlan(e.target.value)} className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={input}><option>Growth B2B</option><option>Growth</option><option>Lite</option><option>A demanda</option></select></div>
          <div className="flex flex-col gap-1"><label className="text-[11px] font-bold uppercase" style={{ color: "var(--faint)" }}>Estado</label>
            <select value={statusVal} onChange={(e) => setStatusVal(e.target.value)} className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={input}><option value="active">active</option><option value="paused">paused</option><option value="churned">churned</option></select></div>
          <button onClick={saveClient} className="px-4 py-2 rounded-[10px] text-[13px] font-semibold text-white" style={btnPri}>Guardar</button>
        </div>
      </Card>

      <Card title="Usuarios e invitaciones">
        <form onSubmit={sendInvite} className="flex gap-3 flex-wrap items-end mb-4">
          <div className="flex flex-col gap-1 flex-1 min-w-[200px]"><label className="text-[11px] font-bold uppercase" style={{ color: "var(--faint)" }}>Correo a invitar</label>
            <input type="email" value={invite.email} onChange={(e) => setInvite({ ...invite, email: e.target.value })} className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={input} placeholder="contacto@cliente.com" /></div>
          <div className="flex flex-col gap-1 min-w-[160px]"><label className="text-[11px] font-bold uppercase" style={{ color: "var(--faint)" }}>Nombre</label>
            <input value={invite.full_name} onChange={(e) => setInvite({ ...invite, full_name: e.target.value })} className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={input} placeholder="Nombre del contacto" /></div>
          <button type="submit" className="px-4 py-2 rounded-[10px] text-[13px] font-semibold text-white" style={btnPri}>Invitar</button>
        </form>
        {inviteLink && (
          <div className="rounded-[10px] p-3 mb-4 text-[12.5px] flex items-center gap-2" style={{ background: "var(--accent-soft)", border: "1px solid #f8d3c8" }}>
            <span className="flex-1 truncate font-mono" style={{ color: "#a23c2f" }}>{inviteLink}</span>
            <button onClick={() => { navigator.clipboard.writeText(inviteLink); toast("Enlace copiado"); }} className="px-3 py-1 rounded-[8px] text-white text-[12px] font-semibold" style={btnPri}>Copiar enlace</button>
          </div>
        )}
        {users.length === 0 ? <div className="text-[13px]" style={{ color: "var(--muted)" }}>Sin usuarios todavía.</div> : (
          <table className="w-full"><tbody>
            {users.map((u) => (<tr key={u.id}><td className="py-2 text-[13px] font-semibold" style={{ borderTop: "1px solid var(--line)" }}>{u.full_name || "—"}</td><td className="py-2 text-[13px]" style={{ borderTop: "1px solid var(--line)" }}>{u.email}</td><td className="py-2 text-[12px]" style={{ borderTop: "1px solid var(--line)", color: "var(--muted)" }}>{u.role}</td></tr>))}
          </tbody></table>
        )}
      </Card>

      <Card title="Servicios / plan">
        <form onSubmit={addService} className="flex gap-3 flex-wrap items-end mb-4">
          <div className="flex flex-col gap-1 flex-1 min-w-[220px]"><label className="text-[11px] font-bold uppercase" style={{ color: "var(--faint)" }}>Servicio</label>
            <input value={svc.label} onChange={(e) => setSvc({ ...svc, label: e.target.value })} className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={input} placeholder="Publicaciones de contenido" /></div>
          <div className="flex flex-col gap-1 w-[120px]"><label className="text-[11px] font-bold uppercase" style={{ color: "var(--faint)" }}>Cupo (total)</label>
            <input type="number" value={svc.total} onChange={(e) => setSvc({ ...svc, total: Number(e.target.value) })} className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={input} /></div>
          <button type="submit" className="px-4 py-2 rounded-[10px] text-[13px] font-semibold text-white" style={btnPri}>+ Agregar servicio</button>
        </form>
        {services.length === 0 ? <div className="text-[13px]" style={{ color: "var(--muted)" }}>Sin servicios configurados.</div> : (
          <table className="w-full"><thead><tr>{["Servicio", "Consumo", "Periodo"].map((h) => <th key={h} className="text-left text-[11px] uppercase font-bold pb-2" style={{ color: "var(--faint)" }}>{h}</th>)}</tr></thead><tbody>
            {services.map((s) => (<tr key={s.id}><td className="py-2 text-[13px] font-semibold" style={{ borderTop: "1px solid var(--line)" }}>{s.label}</td><td className="py-2 text-[13px]" style={{ borderTop: "1px solid var(--line)" }}>{s.used} / {s.total}</td><td className="py-2 text-[12px]" style={{ borderTop: "1px solid var(--line)", color: "var(--muted)" }}>{s.period}</td></tr>))}
          </tbody></table>
        )}
      </Card>
    </div>
  );
}
