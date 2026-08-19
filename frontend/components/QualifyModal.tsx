"use client";

import { useState } from "react";

export type QualifyPayload = { status: string; comment: string; value?: number; revenue?: number };

// Modal de calificación con requisitos por etapa:
//  - "discarded" (Perdido)  → comentario obligatorio (motivo).
//  - "potential" (Ganado)   → comentario + valor del lead + revenue, todos obligatorios.
export function QualifyModal({
  kind,
  leadName,
  onCancel,
  onSubmit,
}: {
  kind: "potential" | "discarded";
  leadName: string;
  onCancel: () => void;
  onSubmit: (payload: QualifyPayload) => Promise<void>;
}) {
  const won = kind === "potential";
  const [comment, setComment] = useState("");
  const [value, setValue] = useState("");
  const [revenue, setRevenue] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const input = { border: "1px solid var(--line)", background: "var(--surface)" } as const;

  async function submit() {
    setErr(null);
    if (!comment.trim()) { setErr(won ? "Agrega un comentario del cierre." : "Agrega el motivo por el que se pierde."); return; }
    let payload: QualifyPayload = { status: kind, comment: comment.trim() };
    if (won) {
      const v = Number(value), r = Number(revenue);
      if (!value.trim() || Number.isNaN(v) || v < 0) { setErr("Indica el valor del lead (número ≥ 0)."); return; }
      if (!revenue.trim() || Number.isNaN(r) || r < 0) { setErr("Indica el revenue del lead (número ≥ 0)."); return; }
      payload = { ...payload, value: Math.round(v), revenue: Math.round(r) };
    }
    setBusy(true);
    try { await onSubmit(payload); }
    catch (e) { setErr(e instanceof Error ? e.message.replace(/^API \d+: /, "") : "No se pudo guardar"); setBusy(false); }
  }

  return (
    <div onClick={onCancel} className="fixed inset-0 z-[100] grid place-items-center p-4" style={{ background: "rgba(20,18,40,.45)" }}>
      <div onClick={(e) => e.stopPropagation()} className="w-full max-w-[440px] rounded-[16px] p-[22px]" style={{ background: "var(--surface)", border: "1px solid var(--line)", boxShadow: "0 24px 60px rgba(20,18,40,.3)" }}>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-[18px]">{won ? "🏆" : "🗑️"}</span>
          <h3 className="text-[17px] font-bold m-0">{won ? "Marcar como Ganado" : "Marcar como Perdido"}</h3>
        </div>
        <p className="text-[12.5px] mb-4" style={{ color: "var(--muted)" }}>{leadName}</p>

        {won && (
          <div className="flex gap-3 mb-3">
            <div className="flex-1 flex flex-col gap-1">
              <label className="text-[11px] font-bold uppercase" style={{ color: "var(--faint)" }}>Valor del lead *</label>
              <input value={value} onChange={(e) => setValue(e.target.value)} type="number" min={0} inputMode="numeric" placeholder="0" className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={input} />
            </div>
            <div className="flex-1 flex flex-col gap-1">
              <label className="text-[11px] font-bold uppercase" style={{ color: "var(--faint)" }}>Revenue *</label>
              <input value={revenue} onChange={(e) => setRevenue(e.target.value)} type="number" min={0} inputMode="numeric" placeholder="0" className="px-3 py-2 rounded-[10px] text-[13px] outline-none" style={input} />
            </div>
          </div>
        )}

        <div className="flex flex-col gap-1 mb-2">
          <label className="text-[11px] font-bold uppercase" style={{ color: "var(--faint)" }}>{won ? "Comentario del cierre *" : "Motivo de la pérdida *"}</label>
          <textarea value={comment} onChange={(e) => setComment(e.target.value)} rows={3} placeholder={won ? "¿Cómo se cerró? Detalles del acuerdo…" : "¿Por qué se descarta este lead?"} className="px-3 py-2 rounded-[10px] text-[13px] outline-none resize-none" style={input} />
        </div>

        {err && <div className="text-[12.5px] mb-2" style={{ color: "var(--bad,#e34948)" }}>{err}</div>}

        <div className="flex gap-2 justify-end mt-3">
          <button onClick={onCancel} disabled={busy} className="px-4 py-2 rounded-[10px] text-[13px] font-semibold" style={{ border: "1px solid var(--line)" }}>Cancelar</button>
          <button onClick={submit} disabled={busy} className="px-4 py-2 rounded-[10px] text-[13px] font-semibold text-white disabled:opacity-60" style={{ background: won ? "var(--good,#1baf7a)" : "var(--bad,#e34948)" }}>
            {busy ? "Guardando…" : won ? "Confirmar Ganado" : "Confirmar Perdido"}
          </button>
        </div>
      </div>
    </div>
  );
}
