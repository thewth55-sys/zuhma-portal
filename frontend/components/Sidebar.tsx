"use client";

import { Icon } from "./Icon";
import { NAV_ADMIN, NAV_CLIENTE, type NavItem } from "@/lib/nav";

type Props = {
  mode: "cliente" | "admin";
  route: string;
  onNavigate: (k: string) => void;
  tenantName: string;
  planLabel: string;
  userInitials: string;
  userName: string;
  onSignOut: () => void;
  enabledModules?: string[] | null;
};

export function Sidebar({ mode, route, onNavigate, tenantName, planLabel, userInitials, userName, onSignOut, enabledModules }: Props) {
  const isC = mode === "cliente";
  // En vista cliente, solo mostrar los módulos habilitados (null = todos).
  const items: NavItem[] =
    isC && Array.isArray(enabledModules)
      ? NAV_CLIENTE.filter((it) => enabledModules.includes(it.k))
      : isC
      ? NAV_CLIENTE
      : NAV_ADMIN;

  return (
    <aside className="w-[248px] flex-none flex flex-col sticky top-0 h-screen text-white" style={{ background: "var(--brand-ink)" }}>
      <div className="flex items-center gap-2 px-[22px] pt-5 pb-[14px] font-extrabold text-[20px] tracking-tight">
        <span
          className="w-[26px] h-[26px] rounded-lg grid place-items-center text-[15px]"
          style={{ background: "linear-gradient(135deg,var(--accent),var(--accent-2))", boxShadow: "0 4px 12px rgba(242,97,82,.5)" }}
        >
          z
        </span>
        zühma<span style={{ color: "var(--accent-2)" }}>+</span>
      </div>

      <div className="mx-[14px] mb-[10px] mt-[6px] px-3 py-[11px] rounded-xl flex gap-[10px] items-center" style={{ background: "rgba(255,255,255,.06)" }}>
        <div className="w-9 h-9 rounded-[9px] grid place-items-center font-bold flex-none" style={{ background: "var(--accent)" }}>
          {isC ? userInitials : "z"}
        </div>
        <div>
          <div className="font-bold text-[13.5px] leading-tight">{isC ? tenantName : "zühma+"}</div>
          <div className="text-[11.5px] mt-[2px] flex items-center gap-[5px]" style={{ color: "#b9b5d6" }}>
            <span className="inline-block w-[7px] h-[7px] rounded-full" style={{ background: "var(--good, #1baf7a)" }} />
            {isC ? planLabel : "Panel de administración"}
          </div>
        </div>
      </div>

      <nav className="px-3 py-[6px] overflow-y-auto flex-1">
        {items.map((it) => {
          const active = it.k === route;
          return (
            <div
              key={it.k}
              onClick={() => onNavigate(it.k)}
              className="flex items-center gap-[11px] px-3 py-[9px] rounded-[10px] font-medium cursor-pointer mb-[2px] text-[14px]"
              style={
                active
                  ? { background: "var(--accent)", color: "#fff", boxShadow: "0 6px 16px rgba(242,97,82,.35)" }
                  : { color: "#c9c6e0" }
              }
            >
              <Icon name={it.i} className="zi flex-none" />
              <span>{it.t}</span>
              {it.badge ? (
                <span
                  className="ml-auto text-[11px] font-bold px-2 py-[1px] rounded-[20px]"
                  style={{ background: active ? "rgba(255,255,255,.25)" : "var(--accent-2)", color: "#fff" }}
                >
                  {it.badge}
                </span>
              ) : null}
            </div>
          );
        })}
      </nav>

      <div className="px-4 py-3 flex gap-[10px] items-center text-[12.5px]" style={{ borderTop: "1px solid rgba(255,255,255,.08)", color: "#b9b5d6" }}>
        <div className="w-[30px] h-[30px] rounded-lg grid place-items-center font-bold text-white" style={{ background: "rgba(255,255,255,.12)" }}>
          {userInitials}
        </div>
        <div>
          {userName}
          <br />
          <span className="cursor-pointer" style={{ color: "var(--faint)" }} onClick={onSignOut}>
            Cerrar sesión
          </span>
        </div>
      </div>
    </aside>
  );
}
