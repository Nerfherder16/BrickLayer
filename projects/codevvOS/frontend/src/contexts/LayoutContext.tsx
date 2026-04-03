import React, { createContext, useState } from 'react'
import type { DockviewApi } from 'dockview-react'

interface LayoutContextValue {
  dockviewApi: DockviewApi | null
  setDockviewApi: (api: DockviewApi | null) => void
}

export const LayoutContext = createContext<LayoutContextValue>({
  dockviewApi: null,
  setDockviewApi: () => undefined,
})

interface LayoutContextProviderProps {
  children: React.ReactNode
}

export function LayoutContextProvider({ children }: LayoutContextProviderProps): JSX.Element {
  const [dockviewApi, setDockviewApi] = useState<DockviewApi | null>(null)

  return (
    <LayoutContext.Provider value={{ dockviewApi, setDockviewApi }}>
      {children}
    </LayoutContext.Provider>
  )
}
