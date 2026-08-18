"use client";

import { useCallback, useEffect, useState } from "react";

import { LoginForm } from "@/components/LoginForm";
import { SetPassword } from "@/components/SetPassword";
import { OtpVerify } from "@/components/OtpVerify";
import { Shell, type SessionUser } from "@/components/Shell";
import { getSupabase, isSupabaseConfigured } from "@/lib/supabase";
import { api } from "@/lib/api";

const DEMO_USER: SessionUser = {
  email: "demo@zuhma.online",
  full_name: "Vista demo",
  role: "admin",
  tenantName: "Nextcore Consulting",
  planLabel: "Growth B2B · Activo",
  enabledModules: null,
  permissions: ["manage_clients", "manage_leads", "upload_content", "manage_tasks", "manage_billing", "manage_team"],
};

type Flow = "loading" | "out" | "setpw" | "mfa" | "in";

function readHashType(): string | null {
  if (typeof window === "undefined") return null;
  return new URLSearchParams(window.location.hash.replace(/^#/, "")).get("type");
}

export default function Page() {
  const [flow, setFlow] = useState<Flow>("loading");
  const [user, setUser] = useState<SessionUser | null>(null);
  const [hashType] = useState<string | null>(readHashType);

  // Carga los datos del usuario y entra a la app (asume 2FA ya resuelto).
  const loadApp = useCallback(async () => {
    const supabase = getSupabase();
    const email = supabase ? (await supabase.auth.getSession()).data.session?.user.email ?? "" : "";
    let role: SessionUser["role"] = "client";
    let tenantName = "";
    let planLabel = "";
    let enabledModules: string[] | null = null;
    let permissions: string[] = [];
    try {
      const me = await api<{ role: SessionUser["role"]; permissions: string[] }>("/me");
      role = me.role;
      permissions = me.permissions ?? [];
      const t = await api<{ name: string; plan: string | null; enabled_modules: string[] | null }>("/me/tenant");
      tenantName = t.name;
      planLabel = t.plan ? `${t.plan} · Activo` : "Activo";
      enabledModules = t.enabled_modules ?? null;
    } catch {
      /* backend/tenant aún no disponible */
    }
    setUser({
      email,
      full_name: null,
      role,
      tenantName: tenantName || email || "Cliente",
      planLabel: planLabel || "Cuenta activa",
      enabledModules,
      permissions,
    });
    setFlow("in");
  }, []);

  const checkFlow = useCallback(async () => {
    const supabase = getSupabase();
    if (!supabase) { setFlow("out"); return; }
    const { data } = await supabase.auth.getSession();
    if (!data.session) { setFlow("out"); return; }
    // Activación por invitación / recuperación → crear contraseña primero.
    if (hashType === "invite" || hashType === "recovery") { setFlow("setpw"); return; }
    // 2FA obligatorio por sesión.
    try {
      const s = await api<{ mfa_required: boolean }>("/auth/status");
      if (s.mfa_required) { setFlow("mfa"); return; }
    } catch {
      /* si /auth/status falla, intentamos cargar de todos modos */
    }
    await loadApp();
  }, [hashType, loadApp]);

  useEffect(() => { checkFlow(); }, [checkFlow]);

  const signOut = useCallback(async () => {
    await getSupabase()?.auth.signOut();
    setUser(null);
    setFlow("out");
  }, []);

  if (flow === "loading") {
    return <div className="min-h-screen grid place-items-center" style={{ color: "var(--muted)" }}>Cargando…</div>;
  }
  if (flow === "setpw") {
    return <SetPassword onDone={() => setFlow("mfa")} />;
  }
  if (flow === "mfa") {
    return <OtpVerify onVerified={loadApp} onCancel={() => setFlow("out")} />;
  }
  if (flow === "in" && user) {
    return <Shell user={user} onSignOut={signOut} />;
  }

  return (
    <div>
      <LoginForm onSignedIn={checkFlow} />
      {!isSupabaseConfigured() && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2">
          <button
            onClick={() => { setUser(DEMO_USER); setFlow("in"); }}
            className="px-4 py-2 rounded-[10px] text-[13px] font-semibold text-white"
            style={{ background: "var(--brand-ink)" }}
          >
            Ver demo del portal (sin login)
          </button>
        </div>
      )}
    </div>
  );
}
