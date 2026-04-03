import type { LucideIcon } from 'lucide-react'
import { Terminal, FolderTree, MessageSquare, Settings } from 'lucide-react'

export interface AppDefinition {
  id: string
  label: string
  icon: LucideIcon
  componentKey: string
}

export const APP_REGISTRY: AppDefinition[] = [
  { id: 'terminal',  label: 'Terminal',  icon: Terminal,      componentKey: 'TerminalPanel'  },
  { id: 'files',     label: 'Files',     icon: FolderTree,    componentKey: 'FileTreePanel'  },
  { id: 'ai-chat',   label: 'AI Chat',   icon: MessageSquare, componentKey: 'AIChatPanel'    },
  { id: 'settings',  label: 'Settings',  icon: Settings,      componentKey: 'SettingsPanel'  },
]
