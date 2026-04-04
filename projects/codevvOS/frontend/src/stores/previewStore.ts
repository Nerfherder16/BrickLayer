import { create } from 'zustand'

interface PreviewState {
  previewPort: number
  refreshCount: number
  previewUrl: string
  setPort: (port: number) => void
  refresh: () => void
}

function buildUrl(port: number, refreshCount: number): string {
  return `http://localhost:${port}?_r=${refreshCount}`
}

export const usePreviewStore = create<PreviewState>((set, get) => ({
  previewPort: 5173,
  refreshCount: 0,
  previewUrl: buildUrl(5173, 0),

  setPort(port: number): void {
    set({ previewPort: port, previewUrl: buildUrl(port, get().refreshCount) })
  },

  refresh(): void {
    const count = get().refreshCount + 1
    set({ refreshCount: count, previewUrl: buildUrl(get().previewPort, count) })
  },
}))
