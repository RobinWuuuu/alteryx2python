const { app, BrowserWindow, dialog, ipcMain } = require('electron');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const http = require('http');
const net = require('net');

const PREFERRED_PORT = 9721;
const isDev = !app.isPackaged;

let mainWindow = null;
let backendProcess = null;
let resolvedPort = PREFERRED_PORT;
let supportLogPath = null;
let appIsQuitting = false;

function getSupportLogPath() {
  if (supportLogPath) return supportLogPath;
  return path.join(app.getPath('userData'), 'debug.log');
}

function normalizeDetails(details) {
  if (!details) return '';
  if (typeof details === 'string') return details;
  try {
    return JSON.stringify(details, null, 2);
  } catch {
    return String(details);
  }
}

function appendSupportLog(level, scope, message, details = '') {
  try {
    const logPath = getSupportLogPath();
    fs.mkdirSync(path.dirname(logPath), { recursive: true });
    const timestamp = new Date().toISOString();
    const body = [
      `[${timestamp}] [${level}] [${scope}] ${message}`,
      details ? `${normalizeDetails(details)}\n` : '',
    ]
      .filter(Boolean)
      .join('\n');
    fs.appendFileSync(logPath, `${body}\n`, 'utf8');
  } catch (err) {
    console.error('[support-log] Failed to write:', err);
  }
}

function withSupportLogHint(message) {
  return `${message}\n\nSupport log:\n${getSupportLogPath()}`;
}

function findFreePort(startPort) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.listen(startPort, '127.0.0.1', () => {
      const port = server.address().port;
      server.close(() => resolve(port));
    });
    server.on('error', () => {
      resolve(findFreePort(startPort + 1));
    });
  });
}

function getBackendDir() {
  if (isDev) return null;
  return path.join(process.resourcesPath, 'backend', 'api');
}

function getBackendPath() {
  const dir = getBackendDir();
  if (!dir) return null;
  const binaryName = process.platform === 'win32' ? 'api.exe' : 'api';
  return path.join(dir, binaryName);
}

/** Last backend stderr lines for error dialogs (PyInstaller / uvicorn failures). */
let backendStderrTail = '';

function appendStderrTail(chunk) {
  backendStderrTail = (backendStderrTail + chunk.toString()).slice(-4000);
}

ipcMain.handle('support:get-log-path', () => {
  return getSupportLogPath();
});

ipcMain.handle('support:log', (_event, payload = {}) => {
  appendSupportLog(
    payload.level || 'INFO',
    payload.scope || 'renderer',
    payload.message || 'Renderer event',
    payload.details || ''
  );
  return { logPath: getSupportLogPath() };
});

ipcMain.handle('support:show-error-dialog', async (_event, payload = {}) => {
  const title = payload.title || 'Application Error';
  const message = payload.message || 'An unexpected error occurred.';
  const detail = [payload.detail, `Support log:\n${getSupportLogPath()}`]
    .filter(Boolean)
    .join('\n\n');

  appendSupportLog(
    payload.level || 'ERROR',
    payload.scope || 'renderer-dialog',
    `${title}: ${message}`,
    detail
  );

  await dialog.showMessageBox(mainWindow ?? undefined, {
    type: 'error',
    title,
    message,
    detail,
    buttons: ['OK'],
  });

  return { logPath: getSupportLogPath() };
});

function spawnBackend(port) {
  const exePath = getBackendPath();
  if (!exePath) return null;

  const backendDir = path.dirname(exePath);
  const internalDir = path.join(backendDir, '_internal');
  if (!fs.existsSync(exePath)) {
    const hasInternal = fs.existsSync(internalDir);
    console.error(`[main] Backend launcher missing: ${exePath}`);
    appendSupportLog('ERROR', 'backend:start', 'Backend launcher missing', {
      exePath,
      internalDir,
      hasInternal,
    });
    return {
      error: hasInternal
        ? withSupportLogHint('The API launcher (api.exe or api) is missing next to the _internal folder. Reinstall the full app or rebuild — do not copy only _internal.')
        : withSupportLogHint('The Python backend bundle is missing or incomplete under resources/backend/api/. Reinstall the full application folder.'),
    };
  }
  if (!fs.existsSync(internalDir)) {
    console.error(`[main] Backend _internal missing: ${internalDir}`);
    appendSupportLog('ERROR', 'backend:start', 'Backend _internal folder missing', {
      exePath,
      internalDir,
    });
    return {
      error:
        withSupportLogHint('The backend dependencies folder (_internal) is missing. Reinstall the complete app build; PyInstaller onedir needs both the launcher and _internal.'),
    };
  }

  backendStderrTail = '';
  console.log(`[main] Starting backend on port ${port}`);
  console.log(`[main] Backend cwd: ${backendDir}`);
  appendSupportLog('INFO', 'backend:start', `Starting backend on port ${port}`, {
    exePath,
    backendDir,
  });
  const proc = spawn(exePath, [], {
    cwd: backendDir,
    env: {
      ...process.env,
      BACKEND_PORT: String(port),
      APP_SUPPORT_LOG_PATH: getSupportLogPath(),
    },
    stdio: 'pipe',
    ...(process.platform === 'win32' ? { windowsHide: true } : {}),
  });

  proc.stdout.on('data', (data) => {
    const text = data.toString().trim();
    console.log(`[backend] ${text}`);
    if (text) appendSupportLog('INFO', 'backend:stdout', text);
  });
  proc.stderr.on('data', (data) => {
    appendStderrTail(data);
    const text = data.toString().trim();
    console.error(`[backend] ${text}`);
    if (text) appendSupportLog('ERROR', 'backend:stderr', text);
  });
  proc.on('error', (err) => {
    console.error('[backend] Failed to start:', err);
    appendSupportLog('ERROR', 'backend:spawn', 'Failed to start backend process', err.stack || err.message);
  });
  proc.on('exit', (code) => {
    console.log(`[backend] exited with code ${code}`);
    appendSupportLog('ERROR', 'backend:exit', `Backend exited with code ${code}`, backendStderrTail);
    if (!appIsQuitting && code !== 0) {
      dialog.showErrorBox(
        'Backend Stopped',
        withSupportLogHint(
          'The local backend stopped while the app was open. Uploads and conversions will fail until the app is restarted.'
        )
      );
    }
    backendProcess = null;
  });

  return { proc };
}

function pollHealth(port, retries = 60, interval = 500) {
  return new Promise((resolve, reject) => {
    let attempts = 0;
    const check = () => {
      const req = http.get(`http://127.0.0.1:${port}/api/health`, (res) => {
        if (res.statusCode === 200) {
          resolve();
        } else {
          retry();
        }
      });
      req.on('error', retry);
      req.setTimeout(2000, () => { req.destroy(); retry(); });
    };

    const retry = () => {
      attempts++;
      if (attempts >= retries) {
        reject(new Error(`Backend did not respond after ${retries} attempts`));
      } else {
        setTimeout(check, interval);
      }
    };

    check();
  });
}

function createWindow(port) {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    title: 'Pipeline Conversion Engine',
    icon: path.join(__dirname, 'icon.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
      additionalArguments: [`--backend-port=${port}`],
    },
    show: false,
    backgroundColor: '#0a0a0f',
  });

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  if (isDev) {
    mainWindow.loadURL('http://localhost:5200');
    mainWindow.webContents.openDevTools({ mode: 'detach' });
  } else {
    const frontendPath = path.join(process.resourcesPath, 'frontend', 'index.html');
    mainWindow.loadFile(frontendPath);
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function killBackend() {
  if (!backendProcess) return;
  try {
    if (process.platform === 'win32') {
      spawn('taskkill', ['/pid', String(backendProcess.pid), '/f', '/t'], { windowsHide: true });
    } else {
      backendProcess.kill('SIGTERM');
    }
  } catch (e) {
    console.error('[backend] kill error:', e);
    appendSupportLog('ERROR', 'backend:kill', 'Failed to stop backend process cleanly', e.stack || e.message);
  }
  backendProcess = null;
}

process.on('uncaughtException', (err) => {
  appendSupportLog('ERROR', 'main:uncaughtException', err.message, err.stack || '');
  if (app.isReady()) {
    dialog.showErrorBox(
      'Unexpected App Error',
      withSupportLogHint(`The desktop app hit an unexpected internal error.\n\n${err.message}`)
    );
  }
});

process.on('unhandledRejection', (reason) => {
  const message = reason instanceof Error ? reason.message : String(reason);
  const detail = reason instanceof Error ? reason.stack || '' : '';
  appendSupportLog('ERROR', 'main:unhandledRejection', message, detail);
});

app.whenReady().then(async () => {
  supportLogPath = getSupportLogPath();
  appendSupportLog('INFO', 'app:start', 'Desktop app starting', {
    platform: process.platform,
    electron: process.versions.electron,
    chrome: process.versions.chrome,
    node: process.versions.node,
    packaged: app.isPackaged,
  });
  if (!isDev) {
    resolvedPort = await findFreePort(PREFERRED_PORT);
    console.log(`[main] Resolved free port: ${resolvedPort}`);
    appendSupportLog('INFO', 'backend:port', `Resolved backend port ${resolvedPort}`);

    const started = spawnBackend(resolvedPort);
    if (started && started.error) {
      dialog.showErrorBox('Backend Error', started.error);
      app.quit();
      return;
    }
    if (started && started.proc) {
      backendProcess = started.proc;
    }

    try {
      await pollHealth(resolvedPort);
      console.log('[main] Backend is ready');
    } catch (err) {
      console.error('[main] Backend failed to start:', err);
      const hint = backendStderrTail.trim()
        ? `\n\n--- Backend log (tail) ---\n${backendStderrTail.trim().slice(-1500)}`
        : '';
      dialog.showErrorBox(
        'Backend Error',
        withSupportLogHint(
          'The Python backend did not become ready (health check timed out). Try a full reinstall, allow the app in antivirus, and avoid OneDrive-only copies.'
        ) +
          hint
      );
      app.quit();
      return;
    }

    const indexPath = path.join(process.resourcesPath, 'frontend', 'index.html');
    if (!fs.existsSync(indexPath)) {
      dialog.showErrorBox(
        'Installation Error',
        withSupportLogHint(`Frontend bundle missing:\n${indexPath}\n\nUse the complete app folder or .app bundle, not a partial copy.`)
      );
      app.quit();
      return;
    }
  }

  createWindow(resolvedPort);
});

app.on('window-all-closed', () => {
  appIsQuitting = true;
  killBackend();
  app.quit();
});

app.on('before-quit', () => {
  appIsQuitting = true;
  appendSupportLog('INFO', 'app:quit', 'Desktop app shutting down');
  killBackend();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow(resolvedPort);
  }
});
