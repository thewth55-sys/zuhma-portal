"use client";

import { useState } from "react";

import { api } from "@/lib/api";
import { getSupabase } from "@/lib/supabase";

function Req({ ok, label }: { ok: boolean; label: string }) {
  return (
    <div className="flex items-center gap-2 text-[12.5px]" style={{ color: ok ? "var(--good,#1baf7a)" : "var(--faint)" }}>
      <span>{ok ? "✓" : "○"}</span> {label}
    </div>
  );
}
function toast(msg: string) {
  const t = document.createElement("div");
  t.textContent = msg;
  t.style.cssText = "position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:var(--brand-ink);color:#fff;padding:11px 20px;border-radius:12px;font-weight:600;font-size:13.5px;box-shadow:0 10px 30px rgba(0,0,0,.25);z-index:99";
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 2000);
}
const input = { border: "1px solid var(--line)" } as const;
const btnPri = { background: "var(--accent)" } as const;
function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-card p-[18px] mb-4 max-w-[560px]" style={{ background: "var(--surface)", border: "1px solid var(--line)", boxShadow: "0 1px 2px rgba(20,18,40,.04)" }}>
      <h2 className="text-[16px] m-0 mb-3 font-bold">{title}</h2>
      {children}
    </div>
  );
}

export function Profile({ email, fullName, onUpdated }: { email: string; fullName: string | null; onUpdated?: (name: string) => void }) {
  const [name, setName] = useState(fullName ?? "");
  const [savingName, setSavingName] = useState(false);

  const [pw, setPw] = useState("");
  const [pw2, setPw2] = useState("");
  const [show, setShow] = useState(false);
  const [savingPw, setSavingPw] = useState(false);
  const [pwError, setPwError] = useState<string | null>(null);

  const hasLen = pw.length >= 8;
  const hasLetter = /[A-Za-z]/.test(pw);
  const hasNumber = /[0-9]/.test(pw);
  const hasSpecial = /[^A-Za-z0-9]/.test(pw);
  const match = pw.length > 0 && pw === pw2;
  const pwValid = hasLen && hasLetter && hasNumber && hasSpecial && match;

  async function saveName(e: React.FormEvent) {
    e.preventDefault();
    setSavingName(true);
    try {
      await api("/me", { method: "PATCH", body: JSON.stringify({ full_name: name }) });
      toast("Datos actualizados ✓");
      onUpdated?.(name);
    } catch { toast("No se pudo guardar"); }
    finally { setSavingName(false); }
  }

  async function savePw(e: React.FormEvent) {
    e.preventDefault();
    setPwError(null);
    if (!pwValid) return;
    const supabase = getSupabase();
    if (!supabase) { setPwError("Supabase no configurado."); return; }
    setSavingPw(true);
    const { error } = await supabase.auth.updateUser({ password: pw });
    setSavingPw(false);
    if (error) setPwError(error.message);
    else { setPw(""); setPw2(""); toast("Contraseña actualizada ✓"); }
  }

  return (
    <div className="px-[30px] pt-[26px] pb-[60px] max-w-[1180px]">
      <h1 className="text-[27px] tracking-tight m-0 mb-[3px] font-bold">Mi perfil</h1>
      <p className="m-0 mb-[22px]" style={{ color: "var(--muted)" }}>Actualiza tus datos y tu contraseña.</p>

      <Card title="Datos de la cuenta">
        <form onSubmit={saveName} className="flex flex-col gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-[11px] font-bold uppercase" style={{ color: "var(--faint)" }}>Correo</label>
            <input value={email} disabled className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={{ ...input, background: "var(--bg)", color: "var(--muted)" }} />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[11px] font-bold uppercase" style={{ color: "var(--faint)" }}>Nombre</label>
            <input value={name} onChange={(e) => setName(e.target.value)} className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={input} placeholder="Tu nombre" />
          </div>
          <div><button type="submit" disabled={savingName} className="px-4 py-2 rounded-[10px] text-[13px] font-semibold text-white disabled:opacity-60" style={btnPri}>{savingName ? "Guardando…" : "Guardar datos"}</button></div>
        </form>
      </Card>

      <Card title="Cambiar contraseña">
        <form onSubmit={savePw} className="flex flex-col gap-3">
          <div className="relative">
            <input type={show ? "text" : "password"} value={pw} onChange={(e) => setPw(e.target.value)} placeholder="Nueva contraseña" className="w-full px-3 py-2 rounded-[10px] text-[13px] outline-none pr-16" style={input} />
            <button type="button" onClick={() => setShow((s) => !s)} className="absolute right-2 top-1/2 -translate-y-1/2 text-[12px] font-semibold" style={{ color: "var(--muted)" }}>{show ? "Ocultar" : "Ver"}</button>
          </div>
          <input type={show ? "text" : "password"} value={pw2} onChange={(e) => setPw2(e.target.value)} placeholder="Confirmar contraseña" className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={input} />
          <div className="grid gap-1">
            <Req ok={hasLen} label="Mínimo 8 caracteres" />
            <Req ok={hasLetter && hasNumber} label="Letras y números" />
            <Req ok={hasSpecial} label="Al menos un carácter especial" />
            <Req ok={match} label="Las contraseñas coinciden" />
          </div>
          {pwError && <div className="text-[12.5px]" style={{ color: "var(--bad,#e34948)" }}>{pwError}</div>}
          <div><button type="submit" disabled={!pwValid || savingPw} className="px-4 py-2 rounded-[10px] text-[13px] font-semibold text-white disabled:opacity-50" style={btnPri}>{savingPw ? "Guardando…" : "Actualizar contraseña"}</button></div>
        </form>
      </Card>
    </div>
  );
}
