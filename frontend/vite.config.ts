import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Puerto propio de la app de comisiones para no colisionar con otros
    // proyectos (p.ej. el de contratos/proformas que usa el 5173).
    // strictPort: si está ocupado, falla en vez de saltar a otro puerto en
    // silencio (que es lo que provocaba ver la app equivocada).
    port: 5180,
    strictPort: true,
    host: true,
    // Permite servir la app a través de un túnel (cloudflare/ngrok) sin que
    // Vite bloquee el dominio externo.
    allowedHosts: true,
    // Proxy interno: las llamadas a /api se reenvían al backend FastAPI.
    // Así un único enlace (el del túnel) sirve web + backend, sin que el
    // navegador del visitante tenga que alcanzar su propio localhost:8000.
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
