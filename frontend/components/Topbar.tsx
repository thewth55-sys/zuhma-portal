"use client";

import { NotificationsBell } from "./NotificationsBell";

type Props = {
  impersonating?: string | null;
  onStopImpersonate?: () => void;
  showBell?: boolean;
  onOpenLead?: (clientId: number, leadCode: string) => void;
};

export function Topbar({ impersonating, onStopImpersonate, showBell = false, onOpenLead }: Props) {
  return (
    <div
      className="h-14 flex items-center gap-3 px-[30px] sticky top-0 z-[5]"
      style={{ borderBottom: "1px solid var(--line)", background: "var(--surface)" }}
    >
      <div className="flex-1" />
      {showBell && <NotificationsBell onOpenLead={onOpenLead} />}
      {impersonating ? (
        <span className="inline-flex items-center gap-[8px] text-[12px] font-semibold px-[11px] py-[5px] rounded-[20px]" style={{ background: "#fff7e6", color: "#8a6d1f", border: "1px solid #f6e2b4" }}>
          👁 Viendo como: {impersonating}
          {onStopImpersonate && (
            <button onClick={onStopImpersonate} className="font-bold" style={{ color: "#6b540f", textDecoration: "underline" }}>Salir</button>
          )}
        </span>
      ) : (
        <span className="inline-flex items-center gap-[6px] text-[12px] font-semibold px-[11px] py-[5px] rounded-[20px]" style={{ background: "#e7f7f0", color: "#0f7a54" }}>
          ● Cuenta activa
        </span>
      )}
    </div>
  );
}
