"use client";

type Props = {
  mode: "cliente" | "admin";
  onMode: (m: "cliente" | "admin") => void;
  canSwitch: boolean;
  impersonating?: string | null;
  onStopImpersonate?: () => void;
};

export function Topbar({ mode, onMode, canSwitch, impersonating, onStopImpersonate }: Props) {
  return (
    <div
      className="h-14 flex items-center gap-3 px-[30px] sticky top-0 z-[5]"
      style={{ borderBottom: "1px solid var(--line)", background: "var(--surface)" }}
    >
      {canSwitch && (
        <div className="flex rounded-[10px] p-[3px] text-[12.5px] font-semibold" style={{ background: "var(--bg)", border: "1px solid var(--line)" }}>
          <button
            onClick={() => onMode("cliente")}
            className="px-[14px] py-[6px] rounded-[7px] font-semibold"
            style={mode === "cliente" ? { background: "var(--surface)", color: "var(--ink)", boxShadow: "0 1px 2px rgba(20,18,40,.06)" } : { color: "var(--muted)", background: "transparent" }}
          >
            Vista cliente
          </button>
          <button
            onClick={() => onMode("admin")}
            className="px-[14px] py-[6px] rounded-[7px] font-semibold"
            style={mode === "admin" ? { background: "var(--surface)", color: "var(--ink)", boxShadow: "0 1px 2px rgba(20,18,40,.06)" } : { color: "var(--muted)", background: "transparent" }}
          >
            Vista admin
          </button>
        </div>
      )}
      <div className="flex-1" />
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
