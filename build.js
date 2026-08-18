/**
 * build.js — Vercel pre-build script
 *
 * Replaces the `__API_BASE_URL__` placeholder in frontend/index.html
 * with the actual Render backend URL set via the VITE_API_BASE_URL
 * environment variable in Vercel's project settings.
 *
 * Usage:
 *   VITE_API_BASE_URL=https://your-app.onrender.com node build.js
 */

const fs = require('fs');
const path = require('path');

const API_BASE_URL = process.env.VITE_API_BASE_URL || '';

if (!API_BASE_URL) {
  console.warn(
    '[build.js] WARNING: VITE_API_BASE_URL is not set. ' +
    'The frontend will fall back to same-origin (fine if served from the backend, ' +
    'but NOT correct when deployed on Vercel separately).'
  );
}

const indexPath = path.join(__dirname, 'frontend', 'index.html');
let html = fs.readFileSync(indexPath, 'utf-8');

const replaced = html.replace(/__API_BASE_URL__/g, API_BASE_URL);
fs.writeFileSync(indexPath, replaced, 'utf-8');

console.log(`[build.js] Injected API_BASE_URL="${API_BASE_URL}" into frontend/index.html`);
