"use client";

import { useCallback, useEffect, useState } from "react";

import { api } from "@/lib/api";
import { getSupabase } from "@/lib/supabase";

export function OtpVerify({ onVerified, onCancel }: { onVerified: () => void; onCancel: () => void }) {
  const [email, setEmail] = useState<string>("");
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>("Enviando código a tu correo…");
  const [busy, setBusy] = useState(false);

  const send = useCallback(async () => {
    setError(null);
    try {
      const r = await api<{ sent: boolean; email?: string; cooldown?: boolean; already_verified?: boolean }>("/auth/otp/send", { method: "POST" });
      if (r.already_verified) { onVerified(); return; }
      if (r.email) setEmail(r.email);
      setInfo(r.sent ? `Enviamos un código a ${r.email ?? "tu correo"}.` : r.cooldown ? "Espera unos segundos para reenviar." : "Revisa tu correo.");
    } catch (e) {
      setError(e instanceof Error ? e.message.replace(/^API \d+: /, "") : "No se pudo enviar el código.");
      setInfo(null);
    }
  }, [onVerified]);

  useEffect(() => { send(); }, [send]);

  async function verify(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (code.trim().length < 6) return;
    setBusy(true);
    try {
      await api("/auth/otp/verify", { method: "POST", body: JSON.stringify({ code: code.trim() }) });
      onVerified();
    } catch (err) {
      setError(err instanceof Error ? err.message.replace(/^API \d+: /, "") : "Código incorrecto.");
    } finally {
      setBusy(false);
    }
  }

  async function cancel() {
    await getSupabase()?.auth.signOut();
    onCancel();
  }

  return (
    <div className="min-h-screen grid place-items-center px-4" style={{ background: "var(--bg)" }}>
      <div className="w-full max-w-[400px] rounded-card p-7" style={{ background: "var(--surface)", border: "1px solid var(--line)", boxShadow: "0 8px 24px rgba(20,18,40,.05)" }}>
        <div className="flex items-center gap-2 font-extrabold text-[22px] tracking-tight mb-1">
          <span className="w-7 h-7 rounded-lg grid place-items-center text-white text-[15px]" style={{ background: "linear-gradient(135deg,var(--accent),var(--accent-2))" }}>z</span>
          zühma<span style={{ color: "var(--accent-2)" }}>+</span>
        </div>
        <h1 className="text-[18px] font-bold mt-3 mb-1">Verificación en dos pasos</h1>
        <p className="mt-0 mb-4 text-[13px]" style={{ color: "var(--muted)" }}>{info ?? "Ingresa el código de 6 dígitos que enviamos a tu correo."}</p>

        <form onSubmit={verify} className="flex flex-col gap-3">
          <input value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))} inputMode="numeric" placeholder="••••••" className="px-3 py-3 rounded-[10px] text-[22px] tracking-[10px] text-center outline-none font-mono" style={{ border: "1px solid var(--line)" }} />
          {error && <div className="text-[12.5px]" style={{ color: "var(--bad,#e34948)" }}>{error}</div>}
          <button type="submit" disabled={busy || code.length < 6} className="px-[14px] py-[10px] rounded-[10px] font-semibold text-[14px] text-white disabled:opacity-50" style={{ background: "var(--accent)" }}>
            {busy ? "Verificando…" : "Verificar y entrar"}
          </button>
        </form>

        <div className="flex items-center justify-between mt-4 text-[12.5px]">
          <button onClick={send} className="font-semibold" style={{ color: "var(--accent)" }}>Reenviar código</button>
          <button onClick={cancel} style={{ color: "var(--muted)" }}>Cerrar sesión</button>
        </div>
      </div>
    </div>
  );
}
