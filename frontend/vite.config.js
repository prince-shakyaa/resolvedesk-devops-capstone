import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In local dev the Vite server proxies /api to the FastAPI backend.
// In Docker/Kubernetes the same job is done by Nginx (see nginx/default.conf.template).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
  build: {
    outDir: "dist",
    sourcemap: false,
  },
});
