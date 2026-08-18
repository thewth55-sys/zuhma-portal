"use client";

import { useEffect, useRef } from "react";

const SCRIPT_ID = "cf-turnstile-script";

/** Widget de Cloudflare Turnstile. Llama onToken con el token (o "" si expira/falla). */
export function Turnstile({ siteKey, onToken }: { siteKey: string; onToken: (t: string) => void }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!siteKey) return;
    let cancelled = false;

    function render() {
      const w = window as unknown as { turnstile?: { render: (el: HTMLElement, opts: object) => void } };
      if (cancelled || !w.turnstile || !ref.current || ref.current.hasChildNodes()) return;
      w.turnstile.render(ref.current, {
        sitekey: siteKey,
        callback: (token: string) => onToken(token),
        "expired-callback": () => onToken(""),
        "error-callback": () => onToken(""),
      });
    }

    if (!document.getElementById(SCRIPT_ID)) {
      const s = document.createElement("script");
      s.id = SCRIPT_ID;
      s.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
      s.async = true;
      s.onload = render;
      document.head.appendChild(s);
    } else {
      render();
    }
    return () => { cancelled = true; };
  }, [siteKey, onToken]);

  if (!siteKey) return null;
  return <div ref={ref} className="my-1" />;
}
