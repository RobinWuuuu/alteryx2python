import axios from 'axios'

type SurfaceOptions = {
  title: string
  scope: string
  action: string
  popup?: boolean
  fileName?: string
  extraDetails?: string
}

function detailToString(detail: unknown): string {
  if (!detail) return ''
  if (typeof detail === 'string') return detail
  try {
    return JSON.stringify(detail, null, 2)
  } catch {
    return String(detail)
  }
}

function likelyCauses(scope: string): string[] {
  if (scope.includes('upload')) {
    return [
      'The selected file is very large or expensive to parse.',
      'Security software blocked or slowed the local backend while processing the file.',
      'The shared app folder is incomplete or was copied partially.',
    ]
  }
  if (scope.includes('models')) {
    return [
      'The API key is invalid or lacks permission to list models.',
      'The local backend is running, but the OpenAI request failed.',
      'A network proxy or SSL policy blocked the OpenAI call.',
    ]
  }
  if (scope.includes('workflow')) {
    return [
      'The uploaded session expired or was cleared after a restart.',
      'The workflow data could not be loaded from the backend.',
    ]
  }
  if (scope.includes('convert') || scope.includes('step')) {
    return [
      'The selected model timed out or returned an upstream error.',
      'The workflow is too large for the current model or token budget.',
      'The local backend hit an unexpected runtime error during generation.',
    ]
  }
  return [
    'The local backend stopped responding.',
    'The app folder is incomplete or blocked by security software.',
  ]
}

async function getSupportLogPath(): Promise<string | null> {
  try {
    return await window.electronAPI?.getSupportLogPath?.() ?? null
  } catch {
    return null
  }
}

function formatBaseMessage(err: unknown): {
  inlineMessage: string
  technicalDetail: string
} {
  if (axios.isAxiosError(err)) {
    const responseDetail = detailToString(err.response?.data?.detail)

    if (err.code === 'ECONNABORTED') {
      return {
        inlineMessage: 'The request timed out before the app finished processing it.',
        technicalDetail: responseDetail || err.message,
      }
    }

    if (err.response) {
      return {
        inlineMessage: responseDetail || `The backend returned HTTP ${err.response.status}.`,
        technicalDetail: `HTTP ${err.response.status}${responseDetail ? `\n${responseDetail}` : ''}`,
      }
    }

    if (err.request || err.message === 'Network Error') {
      return {
        inlineMessage: 'The desktop backend did not return a response.',
        technicalDetail: err.message,
      }
    }
  }

  if (err instanceof Error) {
    return {
      inlineMessage: err.message,
      technicalDetail: err.stack || err.message,
    }
  }

  return {
    inlineMessage: String(err),
    technicalDetail: String(err),
  }
}

export async function surfaceAppError(err: unknown, options: SurfaceOptions): Promise<string> {
  const base = formatBaseMessage(err)
  const logPath = await getSupportLogPath()
  const detail = [
    `Action: ${options.action}`,
    options.fileName ? `File: ${options.fileName}` : '',
    base.technicalDetail ? `Technical detail:\n${base.technicalDetail}` : '',
    options.extraDetails ? `Extra detail:\n${options.extraDetails}` : '',
    `Likely causes:\n- ${likelyCauses(options.scope).join('\n- ')}`,
    logPath ? `Support log:\n${logPath}` : '',
  ]
    .filter(Boolean)
    .join('\n\n')

  try {
    await window.electronAPI?.logDiagnostic?.({
      level: 'ERROR',
      scope: options.scope,
      message: `${options.title}: ${base.inlineMessage}`,
      details: detail,
    })
  } catch {
    // best effort only
  }

  if (options.popup !== false) {
    if (window.electronAPI?.showErrorDialog) {
      await window.electronAPI.showErrorDialog({
        title: options.title,
        message: base.inlineMessage,
        detail,
        level: 'ERROR',
        scope: options.scope,
      })
    } else {
      console.error(`${options.title}: ${base.inlineMessage}\n\n${detail}`)
    }
  }

  return base.inlineMessage
}

export async function surfaceMessageError(
  message: string,
  options: Omit<SurfaceOptions, 'action'> & { action?: string },
): Promise<string> {
  return surfaceAppError(new Error(message), {
    ...options,
    action: options.action ?? options.title,
  })
}
