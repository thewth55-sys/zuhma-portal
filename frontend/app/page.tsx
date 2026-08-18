"use client";

import { useCallback, useEffect, useState } from "react";

import { LoginForm } from "@/components/LoginForm";
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

export default function Page() {
  const [state, setState] = useState<"loading" | "out" | "in">("loading");
  const [user, setUser] = useState<SessionUser | null>(null);

  const loadSession = useCallback(async () => {
    const supabase = getSupabase();
    if (!supabase) {
      setState("out");
      return;
    }
    const { data } = await supabase.auth.getSession();
    if (!data.session) {
      setState("out");
      return;
    }
    // Enriquecer con datos del BFF (rol + tenant). Tolerante a fallos en Fase 0.
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
      /* backend/tenant aún no disponible: seguimos con lo que hay */
    }
    setUser({
      email: data.session.user.email ?? "",
      full_name: (data.session.user.user_metadata?.full_name as string) ?? null,
      role,
      tenantName: tenantName || data.session.user.email || "Cliente",
      planLabel: planLabel || "Cuenta activa",
      enabledModules,
      permissions,
    });
    setState("in");
  }, []);

  useEffect(() => {
    loadSession();
  }, [loadSession]);

  const signOut = useCallback(async () => {
    await getSupabase()?.auth.signOut();
    setUser(null);
    setState("out");
  }, []);

  if (state === "loading") {
    return <div className="min-h-screen grid place-items-center" style={{ color: "var(--muted)" }}>Cargando…</div>;
  }

  if (state === "in" && user) {
    return <Shell user={user} onSignOut={signOut} />;
  }

  return (
    <div>
      <LoginForm onSignedIn={loadSession} />
      {!isSupabaseConfigured() && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2">
          <button
            onClick={() => {
              setUser(DEMO_USER);
              setState("in");
            }}
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
