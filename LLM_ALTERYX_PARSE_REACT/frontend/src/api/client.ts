import axios from 'axios'
import type {
  ChildrenResponse,
  SessionConfig,
  SequenceResponse,
  Step2Result,
  Step3Result,
  ToolDescription,
  UploadResponse,
} from './types'

const api = axios.create({ baseURL: '' }) // proxied via vite

// ------- Upload -------
export async function uploadFile(file: File): Promise<UploadResponse> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post<UploadResponse>('/api/upload', form)
  return data
}

// ------- Helpers -------
export async function getSequence(sessionId: string): Promise<SequenceResponse> {
  const { data } = await api.post<SequenceResponse>('/api/sequence', { session_id: sessionId })
  return data
}

export async function getChildren(sessionId: string, containerToolId: string): Promise<ChildrenResponse> {
  const { data } = await api.post<ChildrenResponse>('/api/children', {
    session_id: sessionId,
    container_tool_id: containerToolId,
  })
  return data
}

// ------- Advanced step 2 & 3 (plain JSON, no SSE) -------
export async function runStep2(
  sessionId: string,
  config: SessionConfig,
  toolIds: string[],
  extraInstructions: string,
  toolDescriptions: ToolDescription[],
  executionSequence: string,
): Promise<Step2Result> {
  const { data } = await api.post<Step2Result>('/api/convert/advanced/step2', {
    session_id: sessionId,
    config,
    tool_ids: toolIds,
    extra_instructions: extraInstructions,
    tool_descriptions: toolDescriptions,
    execution_sequence: executionSequence,
  }, { timeout: 300_000 })
  return data
}

export async function runStep3(
  sessionId: string,
  config: SessionConfig,
  toolIds: string[],
  extraInstructions: string,
  toolDescriptions: ToolDescription[],
  executionSequence: string,
  workflowDescription: string,
): Promise<Step3Result> {
  const { data } = await api.post<Step3Result>('/api/convert/advanced/step3', {
    session_id: sessionId,
    config,
    tool_ids: toolIds,
    extra_instructions: extraInstructions,
    tool_descriptions: toolDescriptions,
    execution_sequence: executionSequence,
    workflow_description: workflowDescription,
  }, { timeout: 300_000 })
  return data
}

// ------- SQL Advanced step 2 & 3 (plain JSON, no SSE) -------
export async function runSqlStep2(
  sessionId: string,
  config: SessionConfig,
  toolIds: string[],
  extraInstructions: string,
  toolDescriptions: ToolDescription[],
  executionSequence: string,
): Promise<import('./types').SqlStep2Result> {
  const { data } = await api.post('/api/convert/sql/advanced/step2', {
    session_id: sessionId,
    config,
    tool_ids: toolIds,
    extra_instructions: extraInstructions,
    tool_descriptions: toolDescriptions,
    execution_sequence: executionSequence,
  }, { timeout: 300_000 })
  return data
}

export async function runSqlStep3(
  sessionId: string,
  config: SessionConfig,
  toolIds: string[],
  extraInstructions: string,
  toolDescriptions: ToolDescription[],
  executionSequence: string,
  sqlStructureGuide: string,
): Promise<import('./types').SqlStep3Result> {
  const { data } = await api.post('/api/convert/sql/advanced/step3', {
    session_id: sessionId,
    config,
    tool_ids: toolIds,
    extra_instructions: extraInstructions,
    tool_descriptions: toolDescriptions,
    execution_sequence: executionSequence,
    sql_structure_guide: sqlStructureGuide,
  }, { timeout: 300_000 })
  return data
}

// ------- Fabric Advanced step 2 & 3 (plain JSON, no SSE) -------
export async function uploadFabricFile(file: File): Promise<import('./types').FabricUploadResponse> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post('/api/fabric/upload', form)
  return data
}

export async function runFabricStep2(
  sessionId: string,
  config: SessionConfig,
  activityNames: string[],
  extraInstructions: string,
  activityDescriptions: import('./types').FabricActivity[],
  executionSequence: string,
): Promise<import('./types').FabricStep2Result> {
  const { data } = await api.post('/api/fabric/advanced/step2', {
    session_id: sessionId,
    config,
    activity_names: activityNames,
    extra_instructions: extraInstructions,
    activity_descriptions: activityDescriptions,
    execution_sequence: executionSequence,
  }, { timeout: 300_000 })
  return data
}

export async function runFabricStep3(
  sessionId: string,
  config: SessionConfig,
  activityNames: string[],
  extraInstructions: string,
  activityDescriptions: import('./types').FabricActivity[],
  executionSequence: string,
  structureGuide: string,
): Promise<import('./types').FabricStep3Result> {
  const { data } = await api.post('/api/fabric/advanced/step3', {
    session_id: sessionId,
    config,
    activity_names: activityNames,
    extra_instructions: extraInstructions,
    activity_descriptions: activityDescriptions,
    execution_sequence: executionSequence,
    structure_guide: structureGuide,
  }, { timeout: 300_000 })
  return data
}

// ------- Models -------
export async function getModels(): Promise<string[]> {
  const { data } = await api.get<{ models: string[] }>('/api/models')
  return data.models
}

// ------- SSE streaming helper -------
// Direct conversion and Advanced step 1 use SSE (POST + ReadableStream).
export async function* streamPost<T>(
  url: string,
  body: unknown,
  signal?: AbortSignal,
): AsyncGenerator<
  | { type: 'progress'; value: number }
  | { type: 'message'; text: string }
  | { type: 'result'; data: T }
  | { type: 'error'; message: string }
  | { type: 'heartbeat' }
> {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(`API error ${response.status}: ${text}`)
  }

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const event = JSON.parse(line.slice(6))
          yield event
        } catch {
          // ignore malformed lines
        }
      }
    }
  }
}
