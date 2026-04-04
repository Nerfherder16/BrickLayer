---
name: codevvos-component
description: >-
  Create or modify a CodeVV OS frontend component. Enforces the project's
  component patterns: dockview panels, xterm terminal shells, CodeMirror
  editors, zustand state slices, Framer Motion animations. Use when building
  new UI panels, dock items, shell integrations, or editor extensions for
  codevvOS.
tools: Read, Write, Edit, Glob, Grep, Bash, LSP
---

# CodeVV OS Component Guide

You are building a component for the CodeVV OS frontend — a boot-to-browser OS
that runs in kiosk-mode Chromium. Components must follow established patterns
for panels, terminals, editors, and state management.

## Project Location

```
/home/nerfherder/Dev/Bricklayer2.0/projects/codevvOS/frontend/
```

## Component Categories

| Category | Location | Key Dependencies |
|----------|----------|-----------------|
| Dock items | `src/components/Dock/` | lucide-react icons |
| Panels | `src/components/Panels/` | dockview-react |
| Shell/Terminal | `src/components/Shell/` | @xterm/xterm, @xterm/addon-* |
| Editor | `src/components/Editor/` | @codemirror/* |
| Graph | `src/components/Graph/` | Custom graph renderer |
| Artifacts | `src/components/Artifacts/` | ansi-to-html |

## Patterns

### New Panel Component

```tsx
import { IDockviewPanelProps } from 'dockview-react';

interface MyPanelProps {
  // panel-specific props
}

export function MyPanel({ params }: IDockviewPanelProps<MyPanelProps>) {
  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* content */}
    </div>
  );
}
```

### Zustand State Slice

```tsx
// State lives in src/store/ or co-located
import { create } from 'zustand';

interface MySlice {
  value: string;
  setValue: (v: string) => void;
}

export const useMyStore = create<MySlice>((set) => ({
  value: '',
  setValue: (value) => set({ value }),
}));
```

### Framer Motion Animation

```tsx
import { motion } from 'framer-motion';

// Panel slide-in
<motion.div
  initial={{ opacity: 0, y: 8 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.15 }}
>
```

### Notifications (sonner)

```tsx
import { toast } from 'sonner';
toast.success('Action completed');
toast.error('Something went wrong');
```

## Style Rules

- **Tailwind only** — no inline styles, no CSS modules
- **Dark-first** — assume dark background (`bg-gray-900`, `bg-neutral-900`)
- **Design tokens** — never hardcode hex colors
- **lucide-react** for all icons (size 16 for compact UI, 20 for prominent)
- **No class-variance-authority (cva)** unless the component has 3+ variants

## Checklist Before Completing

```bash
cd /home/nerfherder/Dev/Bricklayer2.0/projects/codevvOS/frontend

# Type check
npx tsc --noEmit 2>&1 | head -30

# Lint
npx eslint src/components/YourComponent --format compact

# Tests
npx vitest run --reporter=dot
```
