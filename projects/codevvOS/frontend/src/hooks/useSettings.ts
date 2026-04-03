import { useState, useEffect, useCallback } from 'react'
import { fetchSchema, fetchUserSettings, saveUserSettings } from '../api/settings'

interface SettingsState {
  schema: object | null
  uiSchema: object | null
  data: unknown
  loading: boolean
  saving: boolean
  error: string | null
}

export interface UseSettingsReturn extends SettingsState {
  save: (data: unknown) => Promise<void>
}

export function useSettings(): UseSettingsReturn {
  const [state, setState] = useState<SettingsState>({
    schema: null,
    uiSchema: null,
    data: {},
    loading: true,
    saving: false,
    error: null,
  })

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const [schema, data] = await Promise.all([fetchSchema(), fetchUserSettings()])
        if (!cancelled) {
          setState((prev) => ({ ...prev, schema, data, loading: false }))
        }
      } catch (err) {
        if (!cancelled) {
          setState((prev) => ({
            ...prev,
            loading: false,
            error: err instanceof Error ? err.message : String(err),
          }))
        }
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [])

  const save = useCallback(async (data: unknown): Promise<void> => {
    setState((prev) => ({ ...prev, saving: true, error: null }))
    try {
      const updated = await saveUserSettings(data)
      setState((prev) => ({ ...prev, data: updated, saving: false }))
    } catch (err) {
      setState((prev) => ({
        ...prev,
        saving: false,
        error: err instanceof Error ? err.message : String(err),
      }))
    }
  }, [])

  return { ...state, save }
}
