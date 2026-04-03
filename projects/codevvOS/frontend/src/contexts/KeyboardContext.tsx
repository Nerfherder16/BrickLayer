import React, { createContext, useContext } from 'react'
import { registerShortcut, unregisterShortcut, getShortcuts } from '@/hooks/useKeyboardShortcuts'

interface KeyboardContextValue {
  registerShortcut: typeof registerShortcut
  unregisterShortcut: typeof unregisterShortcut
  getShortcuts: typeof getShortcuts
}

const KeyboardContext = createContext<KeyboardContextValue>({
  registerShortcut,
  unregisterShortcut,
  getShortcuts,
})

interface KeyboardProviderProps {
  children: React.ReactNode
}

export function KeyboardProvider({ children }: KeyboardProviderProps): JSX.Element {
  return (
    <KeyboardContext.Provider value={{ registerShortcut, unregisterShortcut, getShortcuts }}>
      {children}
    </KeyboardContext.Provider>
  )
}

/** Access the keyboard shortcut registry from any component. */
export function useKeyboardContext(): KeyboardContextValue {
  return useContext(KeyboardContext)
}
