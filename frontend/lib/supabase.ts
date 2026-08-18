"use client";

import { createClient, type SupabaseClient } from "@supabase/supabase-js";

// Cliente de navegador. Si las llaves aún no están (Supabase lo entrega Oswaldo),
// devolvemos null y la UI muestra un aviso en vez de romperse.
let _client: SupabaseClient | null | undefined;

// "Recordar en este equipo": si está activo, la sesión vive en localStorage (persiste
// entre reinicios del navegador); si no, en sessionStorage (se borra al cerrar el navegador).
function rememberStorage() {
  if (typeof window === "undefined") return undefined;
  return {
    getItem: (k: string) => window.localStorage.getItem(k) ?? window.sessionStorage.getItem(k),
    setItem: (k: string, v: string) => {
      const remember = window.localStorage.getItem("zuhma_remember") !== "0";
      const store = remember ? window.localStorage : window.sessionStorage;
      const other = remember ? window.sessionStorage : window.localStorage;
      store.setItem(k, v);
      other.removeItem(k);
    },
    removeItem: (k: string) => {
      window.localStorage.removeItem(k);
      window.sessionStorage.removeItem(k);
    },
  };
}

export function getSupabase(): SupabaseClient | null {
  if (_client !== undefined) return _client;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anon = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  _client = url && anon
    ? createClient(url, anon, {
        auth: { storage: rememberStorage(), persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
      })
    : null;
  return _client;
}

export const isSupabaseConfigured = () =>
  Boolean(process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY);
