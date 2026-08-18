// Navegación del portal (espejo del prototipo). Las badges son de muestra en Fase 0.

export type NavItem = { k: string; t: string; i: IconName; badge?: number };

export const NAV_CLIENTE: NavItem[] = [
  { k: "inicio", t: "Inicio", i: "home" },
  { k: "leads", t: "Bandeja de leads", i: "inbox", badge: 2 },
  { k: "reportes", t: "Reportes", i: "chart" },
  { k: "atrib", t: "Atribución", i: "target" },
  { k: "aprob", t: "Aprobaciones", i: "check", badge: 3 },
  { k: "plan", t: "Plan y facturación", i: "card" },
  { k: "plane", t: "Planeación", i: "cal" },
  { k: "archivos", t: "Archivos", i: "folder" },
  { k: "soporte", t: "Soporte", i: "life" },
  { k: "perfil", t: "Mi perfil", i: "user" },
];

export const NAV_ADMIN: NavItem[] = [
  { k: "dash", t: "Dashboard", i: "grid" },
  { k: "clientes", t: "Clientes", i: "users" },
  { k: "adminleads", t: "Leads", i: "inbox" },
  { k: "contenido", t: "Contenido", i: "upload" },
  { k: "tareas", t: "Tareas", i: "tasks" },
  { k: "factadmin", t: "Facturación", i: "card" },
  { k: "equipo", t: "Equipo", i: "user" },
  { k: "activ", t: "Actividad", i: "bolt" },
  { k: "config", t: "Configuración", i: "gear" },
];

// Subconjunto de iconos usados por la navegación (paths del prototipo).
export const ICONS = {
  home: '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/>',
  chart: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
  check: '<path d="M9 11l3 3 8-8"/><path d="M20 12v7H4V5h11"/>',
  card: '<rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/>',
  life: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3.5"/><path d="M5 5l3.5 3.5M15.5 15.5 19 19M19 5l-3.5 3.5M8.5 15.5 5 19"/>',
  cal: '<rect x="3" y="4" width="18" height="17" rx="2"/><path d="M3 9h18M8 2v4M16 2v4"/>',
  folder: '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/>',
  users: '<circle cx="9" cy="8" r="3.5"/><path d="M2 20c0-3.5 3-5 7-5s7 1.5 7 5"/><path d="M16 5a3.5 3.5 0 0 1 0 7"/>',
  grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  upload: '<path d="M12 16V4M7 9l5-5 5 5"/><path d="M4 20h16"/>',
  tasks: '<path d="M9 6h11M9 12h11M9 18h11"/><path d="M4 6l1 1 2-2M4 12l1 1 2-2M4 18l1 1 2-2"/>',
  gear: '<circle cx="12" cy="12" r="3.2"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2"/>',
  bolt: '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
  target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.6"/>',
  inbox: '<path d="M3 12l3-7h12l3 7v7H3z"/><path d="M3 12h5l1.5 2.5h5L21 12"/>',
  chat: '<path d="M4 5h16a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H9l-4 4V6a1 1 0 0 1 1-1z"/><path d="M8 10h8M8 13h5"/>',
  send: '<path d="M22 2 11 13"/><path d="M22 2 15 22l-4-9-9-4z"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/>',
  phone: '<path d="M4 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L16 12.5l5 2v4a2 2 0 0 1-2 2A17 17 0 0 1 2 5a2 2 0 0 1 2-1z"/>',
  mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
} as const;

export type IconName = keyof typeof ICONS;
