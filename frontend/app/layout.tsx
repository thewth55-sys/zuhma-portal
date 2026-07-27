import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Portal de Cliente · zühma+",
  description: "Portal de clientes de Zuhma — reportes, aprobaciones, facturación y soporte.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
