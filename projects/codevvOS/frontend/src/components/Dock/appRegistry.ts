import type { LucideIcon } from 'lucide-react'
import { Terminal, FolderTree, MessageSquare, Settings, Monitor, Activity, Layers, Network } from 'lucide-react'

export interface AppDefinition {
  id: string
  label: string
  icon: LucideIcon
  componentKey: string
}

export const APP_REGISTRY: AppDefinition[] = [
  { id: 'terminal',        label: 'Terminal',        icon: Terminal,      componentKey: 'TerminalPanel'       },
  { id: 'files',           label: 'Files',           icon: FolderTree,    componentKey: 'FileTreePanel'       },
  { id: 'ai-chat',         label: 'AI Chat',         icon: MessageSquare, componentKey: 'AIChatPanel'         },
  { id: 'settings',        label: 'Settings',        icon: Settings,      componentKey: 'SettingsPanel'       },
  { id: 'live-preview',    label: 'Live Preview',    icon: Monitor,       componentKey: 'LivePreviewPanel'    },
  { id: 'sidecar-output',  label: 'Sidecar Output',  icon: Activity,      componentKey: 'SidecarOutputPanel'  },
  { id: 'artifacts',       label: 'Artifacts',       icon: Layers,        componentKey: 'ArtifactPanel'       },
  { id: 'knowledge-graph', label: 'Knowledge Graph', icon: Network,       componentKey: 'KnowledgeGraphPanel' },
]
