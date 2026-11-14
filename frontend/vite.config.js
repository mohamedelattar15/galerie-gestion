import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const frontendDirectory = dirname(fileURLToPath(import.meta.url));

export default defineConfig(({ command }) => ({
  base: command === "build" ? "/static/react/" : "/",
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:5000",
      "/health": "http://127.0.0.1:5000",
    },
  },
  build: {
    outDir: resolve(frontendDirectory, "../backend/static/react"),
    emptyOutDir: true,
    rollupOptions: {
      output: {
        entryFileNames: "app.js",
        chunkFileNames: "chunks/[name].js",
        assetFileNames: (asset) =>
          asset.name?.endsWith(".css") ? "app.css" : "assets/[name][extname]",
      },
    },
  },
}));
