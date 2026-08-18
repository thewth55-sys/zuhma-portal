"use client";

import { Fragment, useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";

type Member = { id: number; email: string; full_name: string | null; role: string; active: boolean; permissions: string[]; managed_client_ids: number[] | null };
type ClientLite = { id: number; name: string };

const PERM_LABELS: Record<string, string> = {
  manage_clients: "Gestionar clientes",
  manage_leads: "Gestionar leads y conversiones",
  upload_content: "Subir contenido",
  manage_tasks: "Tareas",
  manage_billing: "Facturación",
  manage_team: "Gestionar equipo",
};

function toast(msg: string) {
  const t = document.createElement("div");
  t.textContent = msg;
  t.style.cssText = "position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:var(--brand-ink);color:#fff;padding:11px 20px;border-radius:12px;font-weight:600;font-size:13.5px;box-shadow:0 10px 30px rgba(0,0,0,.25);z-index:99";
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 2200);
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

export function AdminTeam({ isAdmin = false }: { isAdmin?: boolean }) {
  const [members, setMembers] = useState<Member[] | null>(null);
  const [perms, setPerms] = useState<string[]>([]);
  const [clients, setClients] = useState<ClientLite[]>([]);
  const [inviting, setInviting] = useState(false);
  const [openId, setOpenId] = useState<number | null>(null);

  const load = useCallback(async () => {
    try {
      const [m, p, c] = await Promise.all([
        api<Member[]>("/admin/team"),
        api<{ permissions: string[] }>("/admin/team/permissions"),
        api<ClientLite[]>("/admin/team/clients"),
      ]);
      setMembers(m); setPerms(p.permissions); setClients(c);
    } catch (e) { toast(e instanceof Error && e.message.includes("403") ? "Requiere permiso 'Gestionar equipo'" : "Error cargando equipo"); }
  }, []);
  useEffect(() => { load(); }, [load]);

  return (
    <div className="px-[30px] pt-[26px] pb-[60px] max-w-[1180px]">
      <div className="flex items-start justify-between mb-5">
        <div>
          <h1 className="text-[27px] tracking-tight m-0 mb-[3px] font-bold">Equipo</h1>
          <p className="m-0" style={{ color: "var(--muted)" }}>Usuarios internos de Zuhma · permisos y clientes asignados</p>
        </div>
        <button onClick={() => setInviting((v) => !v)} className="text-[13px] font-semibold px-[13px] py-[8px] rounded-[10px] text-white" style={btnPri}>+ Invitar miembro</button>
      </div>

      {inviting && <InviteForm perms={perms} clients={clients} onDone={() => { setInviting(false); load(); }} />}

      <Card title="Miembros del equipo">
        <table className="w-full">
          <thead><tr>{["Miembro", "Rol", "Permisos", "Clientes", "Estado", ""].map((h) => <th key={h} className="text-left text-[11px] uppercase font-bold pb-2" style={{ color: "var(--faint)" }}>{h}</th>)}</tr></thead>
          <tbody>
            {members?.map((m) => (
              <Fragment key={m.id}>
                <tr>
                  <td className="py-3" style={{ borderTop: "1px solid var(--line)" }}><div className="font-semibold text-[13.5px]">{m.full_name || "—"}</div><div className="text-[12px]" style={{ color: "var(--faint)" }}>{m.email}</div></td>
                  <td className="py-3 text-[13px]" style={{ borderTop: "1px solid var(--line)" }}>{m.role === "admin" ? "Admin" : "Miembro"}</td>
                  <td className="py-3 text-[12px]" style={{ borderTop: "1px solid var(--line)", color: "var(--muted)" }}>{m.role === "admin" ? "Todos" : `${m.permissions.length}`}</td>
                  <td className="py-3 text-[12px]" style={{ borderTop: "1px solid var(--line)", color: "var(--muted)" }}>{m.role === "admin" || m.managed_client_ids === null ? "Todos" : `${m.managed_client_ids.length}`}</td>
                  <td className="py-3" style={{ borderTop: "1px solid var(--line)" }}><span className="text-[12px] font-semibold px-[9px] py-[3px] rounded-[20px]" style={m.active ? { background: "#e7f7f0", color: "#0f7a54" } : { background: "#fde8e7", color: "#b23a3a" }}>{m.active ? "Activo" : "Inactivo"}</span></td>
                  <td className="py-3 text-right" style={{ borderTop: "1px solid var(--line)" }}><button onClick={() => setOpenId(openId === m.id ? null : m.id)} className="text-[12.5px] font-semibold px-[11px] py-[6px] rounded-[10px]" style={input as object}>Editar</button></td>
                </tr>
                {openId === m.id && (
                  <tr><td colSpan={6} style={{ borderTop: "1px solid var(--line)", background: "var(--bg)" }}>
                    <MemberEditor member={m} perms={perms} clients={clients} isAdmin={isAdmin} onSaved={() => { setOpenId(null); load(); }} />
                  </td></tr>
                )}
              </Fragment>
            ))}
            {members && members.length === 0 && <tr><td colSpan={6} className="py-6 text-center text-[13px]" style={{ color: "var(--muted)" }}>Solo estás tú. Invita a tu equipo.</td></tr>}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

function PermGrid({ perms, selected, onToggle }: { perms: string[]; selected: string[]; onToggle: (p: string) => void }) {
  return (
    <div className="grid gap-2" style={{ gridTemplateColumns: "repeat(2,1fr)" }}>
      {perms.map((p) => (
        <label key={p} className="flex items-center gap-2 text-[13px] px-3 py-2 rounded-[10px] cursor-pointer" style={{ border: "1px solid var(--line)" }}>
          <input type="checkbox" checked={selected.includes(p)} onChange={() => onToggle(p)} /> {PERM_LABELS[p] ?? p}
        </label>
      ))}
    </div>
  );
}

function ClientAccess({ clients, allClients, ids, onAll, onToggle }: { clients: ClientLite[]; allClients: boolean; ids: number[]; onAll: (v: boolean) => void; onToggle: (id: number) => void }) {
  return (
    <div>
      <label className="flex items-center gap-2 text-[13px] mb-2 cursor-pointer"><input type="checkbox" checked={allClients} onChange={(e) => onAll(e.target.checked)} /> <b>Acceso a todos los clientes</b></label>
      {!allClients && (
        <div className="grid gap-2" style={{ gridTemplateColumns: "repeat(3,1fr)" }}>
          {clients.map((c) => (
            <label key={c.id} className="flex items-center gap-2 text-[13px] px-3 py-2 rounded-[10px] cursor-pointer" style={{ border: "1px solid var(--line)" }}>
              <input type="checkbox" checked={ids.includes(c.id)} onChange={() => onToggle(c.id)} /> {c.name}
            </label>
          ))}
        </div>
      )}
    </div>
  );
}

function InviteForm({ perms, clients, onDone }: { perms: string[]; clients: ClientLite[]; onDone: () => void }) {
  const [f, setF] = useState({ email: "", full_name: "", role: "zuhma_member" });
  const [sel, setSel] = useState<string[]>(["manage_leads"]);
  const [allClients, setAllClients] = useState(true);
  const [ids, setIds] = useState<number[]>([]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!f.email.trim()) return;
    try {
      const r = await api<{ email_sent?: boolean; action_link?: string | null }>("/admin/team/invite", {
        method: "POST",
        body: JSON.stringify({ ...f, permissions: f.role === "admin" ? [] : sel, managed_client_ids: f.role === "admin" || allClients ? null : ids }),
      });
      toast(r.email_sent ? "Invitación enviada por correo ✓" : "Miembro creado" + (r.action_link ? " · comparte el enlace" : ""));
      onDone();
    } catch (err) { toast(err instanceof Error ? err.message.replace(/^API \d+: /, "").slice(0, 90) : "No se pudo invitar"); }
  }

  return (
    <Card title="Invitar miembro">
      <form onSubmit={submit} className="flex flex-col gap-4">
        <div className="flex gap-3 flex-wrap">
          <div className="flex flex-col gap-1 flex-1 min-w-[220px]"><label className="text-[11px] font-bold uppercase" style={{ color: "var(--faint)" }}>Correo</label>
            <input type="email" required value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={input} placeholder="miembro@zuhma.com" /></div>
          <div className="flex flex-col gap-1 min-w-[160px]"><label className="text-[11px] font-bold uppercase" style={{ color: "var(--faint)" }}>Nombre</label>
            <input value={f.full_name} onChange={(e) => setF({ ...f, full_name: e.target.value })} className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={input} /></div>
          <div className="flex flex-col gap-1 min-w-[150px]"><label className="text-[11px] font-bold uppercase" style={{ color: "var(--faint)" }}>Rol</label>
            <select value={f.role} onChange={(e) => setF({ ...f, role: e.target.value })} className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={input}><option value="zuhma_member">Miembro</option><option value="admin">Admin (todo)</option></select></div>
        </div>
        {f.role !== "admin" && (
          <>
            <div><div className="text-[11px] font-bold uppercase mb-2" style={{ color: "var(--faint)" }}>Permisos</div><PermGrid perms={perms} selected={sel} onToggle={(p) => setSel((s) => s.includes(p) ? s.filter((x) => x !== p) : [...s, p])} /></div>
            <div><div className="text-[11px] font-bold uppercase mb-2" style={{ color: "var(--faint)" }}>Clientes asignados</div><ClientAccess clients={clients} allClients={allClients} ids={ids} onAll={setAllClients} onToggle={(id) => setIds((s) => s.includes(id) ? s.filter((x) => x !== id) : [...s, id])} /></div>
          </>
        )}
        <div><button type="submit" className="px-4 py-2 rounded-[10px] text-[13px] font-semibold text-white" style={btnPri}>Enviar invitación</button></div>
      </form>
    </Card>
  );
}

function MemberEditor({ member, perms, clients, isAdmin, onSaved }: { member: Member; perms: string[]; clients: ClientLite[]; isAdmin: boolean; onSaved: () => void }) {
  const [sel, setSel] = useState<string[]>(member.permissions);
  const [allClients, setAllClients] = useState(member.managed_client_ids === null);
  const [ids, setIds] = useState<number[]>(member.managed_client_ids ?? []);
  const [role, setRole] = useState(member.role);

  async function save() {
    try {
      await api(`/admin/team/${member.id}`, { method: "PATCH", body: JSON.stringify({ role, permissions: role === "admin" ? [] : sel, managed_client_ids: role === "admin" || allClients ? null : ids }) });
      toast("Guardado ✓"); onSaved();
    } catch { toast("No se pudo guardar"); }
  }
  async function toggleActive() {
    try { await api(`/admin/team/${member.id}`, { method: "PATCH", body: JSON.stringify({ active: !member.active }) }); toast(member.active ? "Desactivado" : "Activado"); onSaved(); }
    catch (e) { toast(e instanceof Error ? e.message.replace(/^API \d+: /, "") : "Error"); }
  }
  async function remove() {
    if (!confirm(`¿Eliminar definitivamente a ${member.email}? Esta acción no se puede deshacer.`)) return;
    try { await api(`/admin/team/${member.id}`, { method: "DELETE" }); toast("Usuario eliminado"); onSaved(); }
    catch (e) { toast(e instanceof Error ? e.message.replace(/^API \d+: /, "") : "No se pudo eliminar"); }
  }

  return (
    <div className="p-4 flex flex-col gap-4">
      <div className="flex gap-3 items-center">
        <span className="text-[11px] font-bold uppercase" style={{ color: "var(--faint)" }}>Rol</span>
        <select value={role} onChange={(e) => setRole(e.target.value)} className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={input}><option value="zuhma_member">Miembro</option><option value="admin">Admin (todo)</option></select>
      </div>
      {role !== "admin" && (
        <>
          <div><div className="text-[11px] font-bold uppercase mb-2" style={{ color: "var(--faint)" }}>Permisos</div><PermGrid perms={perms} selected={sel} onToggle={(p) => setSel((s) => s.includes(p) ? s.filter((x) => x !== p) : [...s, p])} /></div>
          <div><div className="text-[11px] font-bold uppercase mb-2" style={{ color: "var(--faint)" }}>Clientes asignados</div><ClientAccess clients={clients} allClients={allClients} ids={ids} onAll={setAllClients} onToggle={(id) => setIds((s) => s.includes(id) ? s.filter((x) => x !== id) : [...s, id])} /></div>
        </>
      )}
      <div className="flex gap-2">
        <button onClick={save} className="px-4 py-2 rounded-[10px] text-[13px] font-semibold text-white" style={btnPri}>Guardar</button>
        <button onClick={toggleActive} className="px-4 py-2 rounded-[10px] text-[13px] font-semibold" style={{ border: "1px solid var(--line)", color: member.active ? "var(--bad,#e34948)" : "var(--good,#1baf7a)" }}>{member.active ? "Desactivar" : "Activar"}</button>
        {isAdmin && (
          <button onClick={remove} className="px-4 py-2 rounded-[10px] text-[13px] font-semibold text-white ml-auto" style={{ background: "var(--bad,#e34948)" }}>Eliminar usuario</button>
        )}
      </div>
    </div>
  );
}
