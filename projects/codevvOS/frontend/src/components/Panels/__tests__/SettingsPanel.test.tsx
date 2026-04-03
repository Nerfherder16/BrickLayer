import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import SettingsPanel from '../SettingsPanel'
import * as useSettingsModule from '../../../hooks/useSettings'

vi.mock('../../../hooks/useSettings')
vi.mock('../../../hooks/useAuth', () => ({
  useAuth: () => ({ isAuthenticated: true, token: 'test', user: null }),
}))
vi.mock('@jsonforms/react', () => ({
  JsonForms: ({ schema }: { schema: unknown }) =>
    schema ? React.createElement('form', { role: 'form', 'data-testid': 'jsonforms-form' }) : null,
}))
vi.mock('@jsonforms/vanilla-renderers', () => ({
  vanillaRenderers: [],
}))

const mockSave = vi.fn()

function makeHookReturn(
  overrides: Partial<ReturnType<typeof useSettingsModule.useSettings>> = {},
): ReturnType<typeof useSettingsModule.useSettings> {
  return {
    schema: null,
    uiSchema: null,
    data: {},
    loading: false,
    saving: false,
    error: null,
    save: mockSave,
    ...overrides,
  }
}

function renderPanel() {
  const AnyPanel = SettingsPanel as React.FC
  return render(<AnyPanel />)
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('SettingsPanel', () => {
  it('should render container with data-testid="settings-panel"', () => {
    vi.mocked(useSettingsModule.useSettings).mockReturnValue(makeHookReturn())
    renderPanel()
    expect(screen.getByTestId('settings-panel')).toBeDefined()
  })

  it('should show data-testid="settings-loading" when loading is true', () => {
    vi.mocked(useSettingsModule.useSettings).mockReturnValue(
      makeHookReturn({ loading: true }),
    )
    renderPanel()
    expect(screen.getByTestId('settings-loading')).toBeDefined()
  })

  it('should not show loading spinner when loading is false', () => {
    vi.mocked(useSettingsModule.useSettings).mockReturnValue(makeHookReturn({ loading: false }))
    renderPanel()
    expect(screen.queryByTestId('settings-loading')).toBeNull()
  })

  it('should render JsonForms form element when schema is loaded', () => {
    vi.mocked(useSettingsModule.useSettings).mockReturnValue(
      makeHookReturn({
        loading: false,
        schema: { type: 'object', properties: {} },
        data: {},
      }),
    )
    renderPanel()
    expect(screen.getByRole('form')).toBeDefined()
  })

  it('should not render JsonForms when schema is null', () => {
    vi.mocked(useSettingsModule.useSettings).mockReturnValue(
      makeHookReturn({ loading: false, schema: null }),
    )
    renderPanel()
    expect(screen.queryByRole('form')).toBeNull()
  })

  it('should show data-testid="settings-error" when error is set', () => {
    vi.mocked(useSettingsModule.useSettings).mockReturnValue(
      makeHookReturn({ error: 'Failed to load settings' }),
    )
    renderPanel()
    expect(screen.getByTestId('settings-error')).toBeDefined()
    expect(screen.getByText(/Failed to load settings/)).toBeDefined()
  })

  it('should call save when save button is clicked', async () => {
    mockSave.mockResolvedValue(undefined)
    vi.mocked(useSettingsModule.useSettings).mockReturnValue(
      makeHookReturn({
        schema: { type: 'object', properties: {} },
        data: { theme: 'dark' },
      }),
    )
    renderPanel()
    fireEvent.click(screen.getByTestId('settings-save-button'))
    await waitFor(() => expect(mockSave).toHaveBeenCalledWith({ theme: 'dark' }))
  })

  it('should show saving state on save button while saving', () => {
    vi.mocked(useSettingsModule.useSettings).mockReturnValue(
      makeHookReturn({
        schema: { type: 'object', properties: {} },
        data: {},
        saving: true,
      }),
    )
    renderPanel()
    const btn = screen.getByTestId('settings-save-button')
    expect(btn.hasAttribute('disabled')).toBe(true)
  })
})
