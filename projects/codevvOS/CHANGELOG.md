# CodeVV OS — Changelog

All notable changes to this project will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Added
- Project brief defining CodeVV OS as a boot-to-browser development OS
- Architecture document covering system layers, kiosk boot chain, network topology, and Proxmox resource allocation
- Server build hardware specification ($14,332 parts list with Threadripper PRO 9975WX)
- CLAUDE.md session context for Claude Code agents
- questions.md research question bank (25 questions across 5 domains)

---

## [Phase 4] — 2026-04-03

### Added
- **Notifications backend** — FastAPI `GET /api/notifications` and `PATCH /api/notifications/{id}/read` endpoints, Alembic migration `003_notifications`, `Notification` model with Row-Level Security
- **Notification store + Sonner** — Zustand `notificationStore`, `useNotifications` hook, `NotificationCenter` dock component, `<Toaster />` integrated in `App.tsx` via Sonner (zero-dependency toast library)
- **Settings Panel** — `SettingsPanel.tsx` with JsonForms auto-render from Pydantic-generated JSON Schema, `useSettings` hook for `GET/PUT /api/settings/user`
- **Keyboard Shortcut Registry** — `useKeyboardShortcuts.ts` with context-aware dispatch, `KeyboardContext` provider for global shortcut resolution
- **Command Palette** — `Cmd+Shift+K` global shortcut opens fuzzy-search palette over `APP_REGISTRY` and registered keyboard shortcuts
- **Theme Toggle** — `ThemeContext.tsx`, dark/light CSS class swap on document root, `localStorage` persistence across sessions
- **PWA support** — `vite-plugin-pwa`, web app manifest, app icons, `NetworkFirst` caching strategy for `/api/*` routes

146 frontend tests passing. `tsc` clean.
