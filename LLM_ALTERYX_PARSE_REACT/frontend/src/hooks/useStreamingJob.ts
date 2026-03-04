import { useCallback, useRef } from 'react'
import { streamPost } from '../api/client'

/**
 * Generic hook for calling an SSE POST endpoint.
 * Returns a `run` function; progress/result updates are emitted via callbacks.
 */
export function useStreamingJob<T>() {
  const abortRef = useRef<AbortController | null>(null)

  const run = useCallback(
    async (
      url: string,
      body: unknown,
      callbacks: {
        onProgress?: (value: number, message: string) => void
        onResult: (data: T) => void
        onError: (message: string) => void
      },
    ) => {
      // Cancel any previous run
      abortRef.current?.abort()
      const controller = new AbortController()
      abortRef.current = controller

      try {
        for await (const event of streamPost<T>(url, body, controller.signal)) {
          if (controller.signal.aborted) break

          if (event.type === 'progress') {
            callbacks.onProgress?.(event.value, '')
          } else if (event.type === 'message') {
            callbacks.onProgress?.(NaN, event.text)
          } else if (event.type === 'result') {
            callbacks.onResult(event.data as T)
          } else if (event.type === 'error') {
            callbacks.onError(event.message)
          }
          // heartbeat: ignore
        }
      } catch (err: unknown) {
        if (!controller.signal.aborted) {
          callbacks.onError(err instanceof Error ? err.message : String(err))
        }
      }
    },
    [],
  )

  const cancel = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
  }, [])

  return { run, cancel }
}
