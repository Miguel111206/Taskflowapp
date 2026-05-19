import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const backendTarget = process.env.VITE_PROXY_TARGET || "http://127.0.0.1:8010";

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      "/login": backendTarget,
      "/register": backendTarget,
      "/tasks": backendTarget,
      "/users": backendTarget,
      "/me": backendTarget,
      "/refresh": backendTarget,
      "/admin": backendTarget,
      "/2fa": backendTarget,
      "/chatbot": backendTarget,
      "/public": backendTarget,
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.js",
  },
});
