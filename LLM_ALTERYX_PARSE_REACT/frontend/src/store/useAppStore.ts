import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type {
  FabricUploadResponse,
  HistoryItem,
  SessionConfig,
  Step1Result,
  Step2Result,
  Step3Result,
} from '../api/types'

// ------- Sub-state shapes -------

interface UploadState {
  sessionId: string | null
  filename: string | null
  nodeCount: number
  connectionCount: number
  toolTypes: string[]
}

interface DirectState {
  status: 'idle' | 'running' | 'done' | 'error'
  progress: number
  message: string
  result: { finalScript: string; promptUsed: string } | null
  error: string | null
}

interface AdvancedStep1State {
  status: 'idle' | 'running' | 'done' | 'error'
  progress: number
  message: string
  result: Step1Result | null
  error: string | null
}

interface AdvancedStep2State {
  status: 'idle' | 'running' | 'done' | 'error'
  result: Step2Result | null
  error: string | null
}

interface AdvancedStep3State {
  status: 'idle' | 'running' | 'done' | 'error'
  result: Step3Result | null
  error: string | null
}

// ------- Full store -------

interface AppStore {
  // Upload / session
  upload: UploadState
  setUpload: (u: UploadState) => void
  clearUpload: () => void

  // Sidebar config
  config: SessionConfig
  setConfig: (partial: Partial<SessionConfig>) => void

  // Tool input
  toolIdsRaw: string
  setToolIdsRaw: (v: string) => void
  extraInstructions: string
  setExtraInstructions: (v: string) => void

  // Helpers
  sequenceStr: string
  setSequenceStr: (v: string) => void
  childToolIds: string[]
  setChildToolIds: (v: string[]) => void

  // Direct conversion
  direct: DirectState
  setDirect: (partial: Partial<DirectState>) => void
  resetDirect: () => void

  // Advanced conversion
  adv1: AdvancedStep1State
  setAdv1: (partial: Partial<AdvancedStep1State>) => void
  resetAdv1: () => void

  adv2: AdvancedStep2State
  setAdv2: (partial: Partial<AdvancedStep2State>) => void
  resetAdv2: () => void

  adv3: AdvancedStep3State
  setAdv3: (partial: Partial<AdvancedStep3State>) => void
  resetAdv3: () => void

  resetAdvanced: () => void

  // Fabric upload
  fabricUpload: FabricUploadResponse | null
  setFabricUpload: (u: FabricUploadResponse | null) => void

  // History (persisted)
  history: HistoryItem[]
  addHistory: (item: HistoryItem) => void
  deleteHistory: (id: string) => void
  clearHistory: () => void
}

const defaultUpload: UploadState = {
  sessionId: null,
  filename: null,
  nodeCount: 0,
  connectionCount: 0,
  toolTypes: [],
}

const defaultDirect: DirectState = {
  status: 'idle',
  progress: 0,
  message: '',
  result: null,
  error: null,
}

const defaultAdv1: AdvancedStep1State = {
  status: 'idle',
  progress: 0,
  message: '',
  result: null,
  error: null,
}

const defaultAdv2: AdvancedStep2State = { status: 'idle', result: null, error: null }
const defaultAdv3: AdvancedStep3State = { status: 'idle', result: null, error: null }

export const useAppStore = create<AppStore>()(
  persist(
    (set) => ({
      upload: defaultUpload,
      setUpload: (u) => set({ upload: u }),
      clearUpload: () => set({ upload: defaultUpload }),

      config: {
        api_key: '',
        code_generate_model: 'gpt-4.1',
        reasoning_model: 'gpt-4.1',
        code_combine_model: 'gpt-5.1-codex',
        temperature: 0.0,
      },
      setConfig: (partial) =>
        set((s) => ({ config: { ...s.config, ...partial } })),

      toolIdsRaw: '',
      setToolIdsRaw: (v) => set({ toolIdsRaw: v }),
      extraInstructions: '',
      setExtraInstructions: (v) => set({ extraInstructions: v }),

      sequenceStr: '',
      setSequenceStr: (v) => set({ sequenceStr: v }),
      childToolIds: [],
      setChildToolIds: (v) => set({ childToolIds: v }),

      direct: defaultDirect,
      setDirect: (partial) => set((s) => ({ direct: { ...s.direct, ...partial } })),
      resetDirect: () => set({ direct: defaultDirect }),

      adv1: defaultAdv1,
      setAdv1: (partial) => set((s) => ({ adv1: { ...s.adv1, ...partial } })),
      resetAdv1: () => set({ adv1: defaultAdv1 }),

      adv2: defaultAdv2,
      setAdv2: (partial) => set((s) => ({ adv2: { ...s.adv2, ...partial } })),
      resetAdv2: () => set({ adv2: defaultAdv2 }),

      adv3: defaultAdv3,
      setAdv3: (partial) => set((s) => ({ adv3: { ...s.adv3, ...partial } })),
      resetAdv3: () => set({ adv3: defaultAdv3 }),

      resetAdvanced: () =>
        set({ adv1: defaultAdv1, adv2: defaultAdv2, adv3: defaultAdv3 }),

      fabricUpload: null,
      setFabricUpload: (u) => set({ fabricUpload: u }),

      history: [],
      addHistory: (item) =>
        set((s) => ({ history: [item, ...s.history].slice(0, 100) })),
      deleteHistory: (id) =>
        set((s) => ({ history: s.history.filter((h) => h.id !== id) })),
      clearHistory: () => set({ history: [] }),
    }),
    {
      name: 'alteryx-converter-store',
      // Only persist history and config (not session state or running jobs)
      partialize: (s) => ({
        history: s.history,
        config: { ...s.config, api_key: '' }, // never persist API key
      }),
    },
  ),
)

// Convenience selector for parsed tool IDs
export function parsedToolIds(raw: string): string[] {
  return raw
    .replace(/["'[\]]/g, '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
}
