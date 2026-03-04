// Shared types matching FastAPI Pydantic schemas

export interface SessionConfig {
  api_key: string
  code_generate_model: string
  reasoning_model: string
  code_combine_model: string
  temperature: number
}

// Upload
export interface UploadResponse {
  session_id: string
  filename: string
  node_count: number
  connection_count: number
  tool_types: string[]
}

// Sequence
export interface SequenceResponse {
  execution_sequence: string[]
  sequence_str: string
}

// Children
export interface ChildrenResponse {
  container_id: string
  child_tool_ids: string[]
}

// Tool description item
export interface ToolDescription {
  tool_id: string
  tool_type: string
  description: string
}

// Step 1 result (from SSE final event)
export interface Step1Result {
  descriptions: ToolDescription[]
  ordered_tool_ids: string[]
  execution_sequence: string
}

// Step 2 result
export interface Step2Result {
  workflow_description: string
  workflow_prompt: string
}

// Step 3 result
export interface Step3Result {
  final_python_code: string
  final_prompt: string
}

// Direct conversion result (from SSE final event)
export interface DirectConvertResult {
  final_script: string
  prompt_used: string
  model_info: {
    code_generate_model: string
    code_combine_model: string
    temperature: number
  }
  tool_ids: string[]
  ordered_tool_ids: string[]
}

// Fabric Upload response
export interface FabricUploadResponse {
  session_id: string
  filename: string
  pipeline_name: string
  activity_count: number
  activity_types: string[]
  activity_names: string[]
}

// Fabric activity description item
export interface FabricActivity {
  activity_name: string
  activity_type: string
  description: string
}

// Fabric Step 1 result (from SSE)
export interface FabricStep1Result {
  descriptions: FabricActivity[]
  activity_names: string[]
  execution_sequence: string
  pipeline_name: string
}

// Fabric Step 2 result
export interface FabricStep2Result {
  structure_guide: string
  structure_prompt: string
}

// Fabric Step 3 result
export interface FabricStep3Result {
  final_code: string
  final_prompt: string
}

// SQL Direct conversion result
export interface SqlDirectConvertResult {
  final_sql: string
  prompt_used: string
  tool_ids: string[]
  ordered_tool_ids: string[]
}

// SQL Advanced Step 2 result
export interface SqlStep2Result {
  sql_structure_guide: string
  sql_structure_prompt: string
}

// SQL Advanced Step 3 result
export interface SqlStep3Result {
  final_sql: string
  final_prompt: string
}

// SSE event shapes
export type SSEEvent =
  | { type: 'progress'; value: number }
  | { type: 'message'; text: string }
  | { type: 'heartbeat' }
  | { type: 'result'; data: unknown }
  | { type: 'error'; message: string }

// History item
export interface HistoryItem {
  id: string
  timestamp: string
  type: 'direct' | 'advanced'
  tool_ids: string
  extra_instructions: string
  model_info: string
  temperature: number
  // direct
  final_script?: string
  prompt_used?: string
  // advanced
  tool_descriptions?: ToolDescription[]
  workflow_description?: string
  workflow_prompt?: string
  final_python_code?: string
  final_prompt?: string
}
