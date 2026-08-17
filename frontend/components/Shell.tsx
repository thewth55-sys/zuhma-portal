"use client";

import { useState } from "react";

import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { LiveChat } from "./LiveChat";
import { SectionPlaceholder } from "./SectionPlaceholder";
import { LeadsView } from "./LeadsView";

export type SessionUser = {
  email: string;
  full_name: string | null;
  role: "client" | "zuhma_member" | "admin";
  tenantName: string;
  planLabel: string;
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
  const [mode, setMode] = useState<"cliente" | "admin">("cliente");
  const [route, setRoute] = useState("inicio");

  const name = user.full_name || user.email;

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
      />
      <div className="flex-1 min-w-0">
        <Topbar
          mode={mode}
          canSwitch={canSwitch}
          onMode={(m) => {
            setMode(m);
            setRoute(m === "cliente" ? "inicio" : "dash");
          }}
        />
        {mode === "cliente" && route === "leads" ? (
          <LeadsView />
        ) : (
          <SectionPlaceholder route={route} mode={mode} />
        )}
      </div>
      <LiveChat />
    </div>
  );
}
