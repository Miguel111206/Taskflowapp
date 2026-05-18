import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      "/login": "http://backend:8010",
      "/register": "http://backend:8010",
      "/tasks": "http://backend:8010",
      "/users": "http://backend:8010",
      "/me": "http://backend:8010",
      "/refresh": "http://backend:8010",
      "/admin": "http://backend:8010",
      "/2fa": "http://backend:8010",
      "/chatbot": "http://backend:8010",
      "/public": "http://backend:8010",
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.js",
  },
});
