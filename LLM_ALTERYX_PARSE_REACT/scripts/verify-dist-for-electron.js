/**
 * Ensures PyInstaller + Vite outputs exist before electron-builder packs them.
 * Run from repo root: node scripts/verify-dist-for-electron.js
 */
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const backendDir = path.join(root, 'dist-backend', 'api');
const launcher = path.join(
  backendDir,
  process.platform === 'win32' ? 'api.exe' : 'api'
);
const internal = path.join(backendDir, '_internal');
const indexHtml = path.join(root, 'frontend', 'dist', 'index.html');

let failed = false;

function need(p, label) {
  if (!fs.existsSync(p)) {
    console.error(`[verify] Missing ${label}: ${p}`);
    failed = true;
    return false;
  }
  return true;
}

need(backendDir, 'backend output folder');
if (fs.existsSync(backendDir)) {
  need(launcher, 'PyInstaller launcher (api.exe or api next to _internal)');
  need(internal, 'PyInstaller _internal bundle');
}
need(indexHtml, 'frontend build (index.html)');

if (failed) {
  console.error(
    '\n[verify] Run build-backend (.bat/.sh) and build-frontend first.\n' +
      'If launcher is missing but _internal exists, your last Electron pack used a bad ' +
      'extraResources filter — rebuild Electron after pulling the latest package.json.\n'
  );
  process.exit(1);
}

console.log('[verify] dist-backend/api launcher + _internal and frontend/dist/index.html OK');
