import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5181,
    proxy: {
      "/login": "http://127.0.0.1:8010",
      "/register": "http://127.0.0.1:8010",
      "/tasks": "http://127.0.0.1:8010",
      "/users": "http://127.0.0.1:8010",
      "/me": "http://127.0.0.1:8010",
      "/refresh": "http://127.0.0.1:8010",
      "/admin": "http://127.0.0.1:8010",
      "/2fa": "http://127.0.0.1:8010",
      "/chatbot": "http://127.0.0.1:8010",
      "/public": "http://127.0.0.1:8010",
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.js",
  },
});
