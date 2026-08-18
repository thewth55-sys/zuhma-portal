"use client";

import { useState } from "react";

import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { LiveChat } from "./LiveChat";
import { SectionPlaceholder } from "./SectionPlaceholder";
import { LeadsView } from "./LeadsView";
import { ClientesAdmin } from "./ClientesAdmin";
import { AdminLeads } from "./AdminLeads";
import { AdminDashboard } from "./AdminDashboard";
import { AdminTeam } from "./AdminTeam";
import { Profile } from "./Profile";
import { setImpersonation, api } from "@/lib/api";

export type SessionUser = {
  email: string;
  full_name: string | null;
  role: "client" | "zuhma_member" | "admin";
  tenantName: string;
  planLabel: string;
  enabledModules: string[] | null;
  permissions: string[];
};

function initials(nameOrEmail: string): string {
  const base = nameOrEmail.trim();
  if (!base) return "·";
  const parts = base.split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return base.slice(0, 2).toUpperCase();
}

export function Shell({ user, onSignOut }: { user: SessionUser; onSignOut: () => void }) {
  const canSwitch = user.role === "admin" || user.role === "zuhma_member";
  // El equipo Zuhma aterriza en el panel admin; el cliente en su Inicio.
  const [mode, setMode] = useState<"cliente" | "admin">(canSwitch ? "admin" : "cliente");
  const [route, setRoute] = useState(canSwitch ? "dash" : "inicio");
  const [impersonating, setImpersonatingState] = useState<{ id: number; name: string } | null>(null);
  const [clientModules, setClientModules] = useState<string[] | null>(user.enabledModules ?? null);

  const name = user.full_name || user.email;

  async function startImpersonate(id: number, tenantName: string) {
    setImpersonation(id);
    setImpersonatingState({ id, name: tenantName });
    setMode("cliente");
    setRoute("inicio");
    // Trae los módulos habilitados del cliente suplantado.
    try {
      const t = await api<{ enabled_modules: string[] | null }>("/me/tenant");
      setClientModules(t.enabled_modules ?? null);
    } catch { setClientModules(null); }
  }
  function stopImpersonate() {
    setImpersonation(null);
    setImpersonatingState(null);
    setClientModules(user.enabledModules ?? null);
    setMode("admin");
    setRoute("clientes");
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar
        mode={mode}
        route={route}
        onNavigate={setRoute}
        tenantName={user.tenantName}
        planLabel={user.planLabel}
        userInitials={initials(name)}
        userName={name}
        onSignOut={onSignOut}
        enabledModules={clientModules}
        permissions={user.permissions}
      />
      <div className="flex-1 min-w-0">
        <Topbar impersonating={impersonating?.name ?? null} onStopImpersonate={stopImpersonate} />
        {mode === "cliente" && route === "leads" ? (
          <LeadsView canEdit={canSwitch && !impersonating} />
        ) : mode === "admin" && route === "dash" ? (
          <AdminDashboard onOpenClients={() => setRoute("clientes")} onOpenLeads={() => setRoute("adminleads")} />
        ) : mode === "admin" && route === "clientes" ? (
          <ClientesAdmin onImpersonate={startImpersonate} />
        ) : mode === "admin" && route === "adminleads" ? (
          <AdminLeads isAdmin={user.role === "admin"} />
        ) : mode === "admin" && route === "equipo" ? (
          <AdminTeam isAdmin={user.role === "admin"} />
        ) : (mode === "cliente" && route === "perfil") || (mode === "admin" && route === "miperfil") ? (
          <Profile email={user.email} fullName={user.full_name} />
        ) : (
          <SectionPlaceholder route={route} mode={mode} />
        )}
      </div>
      <LiveChat />
    </div>
  );
}
