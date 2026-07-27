import { NAV_ADMIN, NAV_CLIENTE } from "@/lib/nav";

const PHASE: Record<string, string> = {
  inicio: "Fase 1", plan: "Fase 1", soporte: "Fase 1", archivos: "Fase 1", reportes: "Fase 1",
  leads: "Fase 2", aprob: "Fase 2",
  atrib: "Fase 3", plane: "Fase 3",
  perfil: "Fase 1",
  dash: "Fase 4", clientes: "Fase 4", contenido: "Fase 4", tareas: "Fase 4",
  factadmin: "Fase 4", equipo: "Fase 4", activ: "Fase 4", config: "Fase 4",
};

const SOURCE: Record<string, string> = {
  inicio: "Panel + Odoo", plan: "Odoo · Facturación", soporte: "Odoo · Helpdesk",
  archivos: "Odoo · Documentos", reportes: "Panel + Ads", leads: "Lead Hub (stub)",
  aprob: "Panel", atrib: "Lead Hub (stub)", plane: "Odoo · Proyecto", perfil: "Panel",
};

export function SectionPlaceholder({ route, mode }: { route: string; mode: "cliente" | "admin" }) {
  const items = mode === "cliente" ? NAV_CLIENTE : NAV_ADMIN;
  const item = items.find((i) => i.k === route);
  const title = item?.t ?? "Sección";
  const phase = PHASE[route] ?? "próxima fase";
  const source = SOURCE[route];

  return (
    <div className="px-[30px] pt-[26px] pb-[60px] max-w-[1180px]">
      <h1 className="text-[27px] tracking-tight m-0 mb-[3px] font-bold">{title}</h1>
      <p className="m-0 mb-[22px]" style={{ color: "var(--muted)" }}>
        Andamiaje listo (Fase 0). Esta vista se implementa en <b>{phase}</b>
        {source ? (
          <>
            {" "}
            · origen de datos: <b>{source}</b>
          </>
        ) : null}
        .
      </p>
      <div
        className="p-10 text-center rounded-card"
        style={{ color: "var(--muted)", border: "1px dashed var(--line)", background: "var(--surface)" }}
      >
        Contenido de <b>{title}</b> en construcción.
        <br />
        La estructura, la marca y la navegación ya funcionan.
      </div>
    </div>
  );
}
