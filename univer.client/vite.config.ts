import { defineConfig } from "vite"
import { svelte } from "@sveltejs/vite-plugin-svelte"
import { VitePWA } from "vite-plugin-pwa"
import legacy from "@vitejs/plugin-legacy"

import path from "node:path"
import manifest from "./src/manifest.js"

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [
        svelte(),
        VitePWA({
            manifest,
            srcDir: "src",
            filename: "sw.ts",
            strategies: "injectManifest",
            includeAssets: ["images/*.png", "images/*.svg", "favicon.ico", "robots.txt"],
            injectManifest: {
                globPatterns: ["**/*.{js,css,html,ico,png,svg,woff,woff2}"],
            },
        }),
        legacy({
            targets: ["defaults", "not IE 11"],
        }),
    ],
    resolve: {
        alias: {
            $lib: path.resolve("./src/lib"),
            $api: path.resolve("./src/api"),
        },
    },
})
