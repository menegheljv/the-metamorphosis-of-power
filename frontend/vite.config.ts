import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Um unico bundle (assets/study-charts.js + .css) com nome fixo: scripts/build_pages_site.py
// injeta essas duas tags no estudo publicado (PT e EN).
export default defineConfig({
  plugins: [react()],
  base: "./",
  build: {
    chunkSizeWarningLimit: 800,
    rollupOptions: {
      input: { "study-charts": "src/study.tsx" },
      output: {
        entryFileNames: "assets/[name].js",
        chunkFileNames: "assets/[name].js",
        assetFileNames: "assets/[name][extname]",
      },
    },
  },
});
