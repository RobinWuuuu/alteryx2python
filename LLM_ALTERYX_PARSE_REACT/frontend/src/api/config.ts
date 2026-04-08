declare global {
  interface Window {
    electronAPI?: {
      isElectron: boolean;
      backendPort: number;
      platform: string;
      openExternal: (url: string) => void;
      getSupportLogPath: () => Promise<string>;
      logDiagnostic: (payload: {
        level?: 'INFO' | 'WARN' | 'ERROR';
        scope?: string;
        message: string;
        details?: string;
      }) => Promise<{ logPath: string }>;
      showErrorDialog: (payload: {
        title: string;
        message: string;
        detail?: string;
        level?: 'INFO' | 'WARN' | 'ERROR';
        scope?: string;
      }) => Promise<{ logPath: string }>;
    };
  }
}

export function getApiBase(): string {
  if (window.electronAPI?.isElectron) {
    return `http://127.0.0.1:${window.electronAPI.backendPort}`;
  }
  return '';
}
