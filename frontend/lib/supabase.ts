"use client";

import { createClient, type SupabaseClient } from "@supabase/supabase-js";

// Cliente de navegador. Si las llaves aún no están (Supabase lo entrega Oswaldo),
// devolvemos null y la UI muestra un aviso en vez de romperse.
let _client: SupabaseClient | null | undefined;

export function getSupabase(): SupabaseClient | null {
  if (_client !== undefined) return _client;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anon = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  // Persistencia por defecto de Supabase (localStorage): sobrevive recargas de forma
  // confiable. El "Recordar en este equipo" se maneja en el arranque (ver page.tsx),
  // sin tocar el almacenamiento del token.
  _client = url && anon
    ? createClient(url, anon, {
        auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
      })
    : null;
  return _client;
}

export const isSupabaseConfigured = () =>
  Boolean(process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY);
