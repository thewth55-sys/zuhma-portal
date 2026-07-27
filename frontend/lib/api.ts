"use client";

import { getSupabase } from "./supabase";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

/**
 * Cliente del BFF. Adjunta el JWT de Supabase en Authorization.
 * `impersonateTenantId` (solo admin) viaja como cabecera y queda auditado en el backend.
 */
export async function api<T = unknown>(
  path: string,
  opts: RequestInit & { impersonateTenantId?: number } = {},
): Promise<T> {
  const supabase = getSupabase();
  let token: string | undefined;
  if (supabase) {
    const { data } = await supabase.auth.getSession();
    token = data.session?.access_token;
  }

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(opts.headers as Record<string, string> | undefined),
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (opts.impersonateTenantId) headers["X-Impersonate-Tenant"] = String(opts.impersonateTenantId);

  const res = await fetch(`${BASE}${path}`, { ...opts, headers });
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}
