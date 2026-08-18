"use client";

import { useState } from "react";

import { getSupabase } from "@/lib/supabase";

function Req({ ok, label }: { ok: boolean; label: string }) {
  return (
    <div className="flex items-center gap-2 text-[12.5px]" style={{ color: ok ? "var(--good,#1baf7a)" : "var(--faint)" }}>
      <span>{ok ? "✓" : "○"}</span> {label}
    </div>
  );
}

export function SetPassword({ onDone }: { onDone: () => void }) {
  const [pw, setPw] = useState("");
  const [pw2, setPw2] = useState("");
  const [show, setShow] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const hasLen = pw.length >= 8;
  const hasLetter = /[A-Za-z]/.test(pw);
  const hasNumber = /[0-9]/.test(pw);
  const hasSpecial = /[^A-Za-z0-9]/.test(pw);
  const match = pw.length > 0 && pw === pw2;
  const valid = hasLen && hasLetter && hasNumber && hasSpecial && match;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!valid) return;
    const supabase = getSupabase();
    if (!supabase) { setError("Supabase no configurado."); return; }
    setSaving(true);
    const { error } = await supabase.auth.updateUser({ password: pw });
    setSaving(false);
    if (error) setError(error.message);
    else onDone();
  }

  return (
    <div className="min-h-screen grid place-items-center px-4" style={{ background: "var(--bg)" }}>
      <div className="w-full max-w-[400px] rounded-card p-7" style={{ background: "var(--surface)", border: "1px solid var(--line)", boxShadow: "0 8px 24px rgba(20,18,40,.05)" }}>
        <div className="flex items-center gap-2 font-extrabold text-[22px] tracking-tight mb-1">
          <span className="w-7 h-7 rounded-lg grid place-items-center text-white text-[15px]" style={{ background: "linear-gradient(135deg,var(--accent),var(--accent-2))" }}>z</span>
          zühma<span style={{ color: "var(--accent-2)" }}>+</span>
        </div>
        <h1 className="text-[18px] font-bold mt-3 mb-1">Crea tu contraseña</h1>
        <p className="mt-0 mb-5 text-[13px]" style={{ color: "var(--muted)" }}>Activa tu cuenta definiendo una contraseña segura.</p>

        <form onSubmit={submit} className="flex flex-col gap-3">
          <div className="relative">
            <input type={show ? "text" : "password"} value={pw} onChange={(e) => setPw(e.target.value)} placeholder="Contraseña" className="w-full px-3 py-[10px] rounded-[10px] text-[14px] outline-none pr-16" style={{ border: "1px solid var(--line)" }} />
            <button type="button" onClick={() => setShow((s) => !s)} className="absolute right-2 top-1/2 -translate-y-1/2 text-[12px] font-semibold" style={{ color: "var(--muted)" }}>{show ? "Ocultar" : "Ver"}</button>
          </div>
          <input type={show ? "text" : "password"} value={pw2} onChange={(e) => setPw2(e.target.value)} placeholder="Confirmar contraseña" className="px-3 py-[10px] rounded-[10px] text-[14px] outline-none" style={{ border: "1px solid var(--line)" }} />

          <div className="grid gap-1 mt-1">
            <Req ok={hasLen} label="Mínimo 8 caracteres" />
            <Req ok={hasLetter && hasNumber} label="Letras y números" />
            <Req ok={hasSpecial} label="Al menos un carácter especial (!@#$…)" />
            <Req ok={match} label="Las contraseñas coinciden" />
          </div>

          {error && <div className="text-[12.5px]" style={{ color: "var(--bad,#e34948)" }}>{error}</div>}
          <button type="submit" disabled={!valid || saving} className="mt-1 px-[14px] py-[10px] rounded-[10px] font-semibold text-[14px] text-white disabled:opacity-50" style={{ background: "var(--accent)" }}>
            {saving ? "Guardando…" : "Crear contraseña y continuar"}
          </button>
        </form>
      </div>
    </div>
  );
}
