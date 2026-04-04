import { create } from 'zustand'

export interface Artifact {
  id: string
  title: string
  jsx: string
  compiled: string | null
}

interface ArtifactState {
  artifacts: Artifact[]
  activeArtifactId: string | null

  addArtifact: (artifact: Artifact) => void
  setActiveArtifact: (id: string) => void
  getActiveArtifact: () => Artifact | null
}

export const useArtifactStore = create<ArtifactState>((set, get) => ({
  artifacts: [],
  activeArtifactId: null,

  addArtifact(artifact: Artifact): void {
    set((state) => {
      const exists = state.artifacts.some((a) => a.id === artifact.id)
      if (exists) return state
      return { artifacts: [...state.artifacts, artifact] }
    })
  },

  setActiveArtifact(id: string): void {
    set({ activeArtifactId: id })
  },

  getActiveArtifact(): Artifact | null {
    const { artifacts, activeArtifactId } = get()
    return artifacts.find((a) => a.id === activeArtifactId) ?? null
  },
}))
