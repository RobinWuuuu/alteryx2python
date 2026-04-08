const { contextBridge, ipcRenderer, shell } = require('electron');

const portArg = process.argv.find((a) => a.startsWith('--backend-port='));
const backendPort = portArg ? parseInt(portArg.split('=')[1], 10) : 9721;

contextBridge.exposeInMainWorld('electronAPI', {
  isElectron: true,
  backendPort,
  platform: process.platform,
  openExternal: (url) => shell.openExternal(url),
  getSupportLogPath: () => ipcRenderer.invoke('support:get-log-path'),
  logDiagnostic: (payload) => ipcRenderer.invoke('support:log', payload),
  showErrorDialog: (payload) => ipcRenderer.invoke('support:show-error-dialog', payload),
});
