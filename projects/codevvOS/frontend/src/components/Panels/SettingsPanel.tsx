import { useState } from 'react'
import type { IDockviewPanelProps } from 'dockview-react'
import { JsonForms } from '@jsonforms/react'
import { vanillaRenderers } from '@jsonforms/vanilla-renderers'
import { useSettings } from '../../hooks/useSettings'
import { useAuth } from '../../hooks/useAuth'
import './SettingsPanel.css'

export default function SettingsPanel(_props: IDockviewPanelProps): JSX.Element {
  const settings = useSettings()
  const auth = useAuth()
  const [localData, setLocalData] = useState<unknown>(null)

  // Keep localData in sync when settings.data changes (initial load)
  const effectiveData = localData !== null ? localData : settings.data

  const isAdmin = (auth as { user?: { role?: string } }).user?.role === 'admin'

  return (
    <div data-testid="settings-panel" className="settings-panel">
      {settings.loading && (
        <div data-testid="settings-loading" className="settings-panel__loading">
          Loading settings…
        </div>
      )}

      {!settings.loading && settings.error && (
        <div data-testid="settings-error" className="settings-panel__error">
          {settings.error}
        </div>
      )}

      {!settings.loading && !settings.error && settings.schema && (
        <>
          <div className="settings-panel__content">
            <JsonForms
              schema={settings.schema}
              data={effectiveData}
              renderers={vanillaRenderers}
              onChange={({ data }) => setLocalData(data)}
            />

            {isAdmin && (
              <div className="settings-panel__admin-section">
                <div className="settings-panel__admin-label">Admin</div>
              </div>
            )}
          </div>

          <div className="settings-panel__footer">
            <button
              data-testid="settings-save-button"
              className="settings-panel__save-btn"
              disabled={settings.saving}
              onClick={() => void settings.save(effectiveData)}
            >
              {settings.saving ? 'Saving…' : 'Save'}
            </button>
          </div>
        </>
      )}
    </div>
  )
}
