import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig({
    plugins: [react()],
    base: "/galaxy-audit-system/",
    server: {
        port: 4175
    }
});
