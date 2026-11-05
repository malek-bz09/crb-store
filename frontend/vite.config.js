import react, { reactCompilerPreset } from '@vitejs/plugin-react'
import babel from '@rolldown/plugin-babel'
import { defineConfig } from 'vite'
import { brand } from './src/data/brand.js'

// Fill the %BRAND_...% placeholders in index.html from src/data/brand.js
function brandHtml() {
  const values = {
    BRAND_TITLE: `${brand.shortName} · ${brand.clubName}`,
    BRAND_MARK: brand.mark,
    BRAND_THEME_COLOR: brand.themeColor,
  }
  return {
    name: 'brand-html',
    transformIndexHtml: (html) =>
      html.replace(/%(BRAND_[A-Z_]+)%/g, (match, key) => values[key] ?? match),
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    brandHtml(),
    react(),
    babel({ presets: [reactCompilerPreset()] })
  ],
  server: {
    // Send /api/... requests to the FastAPI backend (see backend/), so the browser
    // sees one site and we don't need CORS
    proxy: {
      '/api': process.env.API_URL ?? 'http://localhost:8000',
    },
  },
})
