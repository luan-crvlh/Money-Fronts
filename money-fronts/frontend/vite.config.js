import { defineConfig } from "vite";

// Configuração mínima exigida pelo Tauri v2 (DAS seção 2):
// - porta fixa em dev (1420 é a convenção Tauri, aqui usamos 5173 do Vite
//   por simplicidade, refletido em tauri.conf.json -> devUrl).
// - impede que o Vite abra o navegador automaticamente (o Tauri controla a janela).
export default defineConfig({
  clearScreen: false,
  server: {
    port: 5173,
    strictPort: true,
    open: false,
  },
  envPrefix: ["VITE_", "TAURI_"],
  build: {
    outDir: "dist",
    target: process.env.TAURI_ENV_PLATFORM === "windows" ? "chrome105" : "safari13",
    minify: !process.env.TAURI_ENV_DEBUG ? "esbuild" : false,
    sourcemap: !!process.env.TAURI_ENV_DEBUG,
  },
});
