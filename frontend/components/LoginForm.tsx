"use client";

import { useState } from "react";

import { getSupabase, isSupabaseConfigured } from "@/lib/supabase";

export function LoginForm({ onSignedIn }: { onSignedIn: () => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const configured = isSupabaseConfigured();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const supabase = getSupabase();
    if (!supabase) {
      setError("Supabase aún no está configurado. Falta NEXT_PUBLIC_SUPABASE_URL / ANON_KEY.");
      return;
    }
    setLoading(true);
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    setLoading(false);
    if (error) setError(error.message);
    else onSignedIn();
  }

  return (
    <div className="min-h-screen grid place-items-center px-4" style={{ background: "var(--bg)" }}>
      <div className="w-full max-w-[380px] rounded-card p-7" style={{ background: "var(--surface)", border: "1px solid var(--line)", boxShadow: "0 8px 24px rgba(20,18,40,.05)" }}>
        <div className="flex items-center gap-2 font-extrabold text-[22px] tracking-tight mb-1">
          <span className="w-7 h-7 rounded-lg grid place-items-center text-white text-[15px]" style={{ background: "linear-gradient(135deg,var(--accent),var(--accent-2))" }}>
            z
          </span>
          zühma<span style={{ color: "var(--accent-2)" }}>+</span>
        </div>
        <p className="mt-0 mb-5 text-[13.5px]" style={{ color: "var(--muted)" }}>
          Portal de clientes · inicia sesión
        </p>

        {!configured && (
          <div className="mb-4 text-[12.5px] p-3 rounded-[10px]" style={{ background: "#fff7e6", color: "#8a6d1f", border: "1px solid #f6e2b4" }}>
            Supabase pendiente de configurar. Añade las llaves a <code>frontend/.env.local</code> para habilitar el login.
          </div>
        )}

        <form onSubmit={submit} className="flex flex-col gap-3">
          <input
            type="email"
            required
            placeholder="tu@correo.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="px-3 py-[10px] rounded-[10px] text-[14px] outline-none"
            style={{ border: "1px solid var(--line)" }}
          />
          <input
            type="password"
            required
            placeholder="Contraseña"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="px-3 py-[10px] rounded-[10px] text-[14px] outline-none"
            style={{ border: "1px solid var(--line)" }}
          />
          {error && <div className="text-[12.5px]" style={{ color: "var(--bad, #e34948)" }}>{error}</div>}
          <button
            type="submit"
            disabled={loading}
            className="mt-1 px-[14px] py-[10px] rounded-[10px] font-semibold text-[14px] text-white disabled:opacity-60"
            style={{ background: "var(--accent)" }}
          >
            {loading ? "Entrando…" : "Entrar"}
          </button>
        </form>
      </div>
    </div>
  );
}
