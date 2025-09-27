import path from "node:path";
import { TanStackRouterVite } from "@tanstack/router-vite-plugin";
import react from "@vitejs/plugin-react-swc";
import { defineConfig } from "vite";

export default defineConfig(({ mode, command }) => {
	const isDev = mode === "development" || command === "serve";

	return {
		resolve: {
			alias: {
				"@": path.resolve(__dirname, "./src"),
			},
		},
		plugins: [react(), TanStackRouterVite()],
		preview: {
			port: 80,
			strictPort: true,
		},
		server: {
			port: 80,
			strictPort: true,
			host: true,
			origin: "http://0.0.0.0:80",
			...(isDev ? { allowedHosts: true } : {}),
		},
	};
});
