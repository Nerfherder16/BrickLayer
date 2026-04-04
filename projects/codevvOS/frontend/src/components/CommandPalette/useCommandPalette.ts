import { useState } from 'react'

export interface CommandPaletteControls {
  isOpen: boolean
  open: () => void
  close: () => void
  toggle: () => void
}

export function useCommandPalette(): CommandPaletteControls {
  const [isOpen, setIsOpen] = useState(false)

  return {
    isOpen,
    open: () => setIsOpen(true),
    close: () => setIsOpen(false),
    toggle: () => setIsOpen(v => !v),
  }
}
