import { renderHook, act, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useSettings } from '../useSettings'
import * as settingsApi from '../../api/settings'

vi.mock('../../api/settings')

const mockFetchSchema = vi.mocked(settingsApi.fetchSchema)
const mockFetchUserSettings = vi.mocked(settingsApi.fetchUserSettings)
const mockSaveUserSettings = vi.mocked(settingsApi.saveUserSettings)

const MOCK_SCHEMA = {
  type: 'object',
  properties: {
    theme: { type: 'string', enum: ['dark', 'light'] },
  },
}

const MOCK_DATA = { theme: 'dark' }

beforeEach(() => {
  vi.clearAllMocks()
})

describe('useSettings', () => {
  it('should have loading true and schema null on initial render', () => {
    mockFetchSchema.mockResolvedValue(MOCK_SCHEMA)
    mockFetchUserSettings.mockResolvedValue(MOCK_DATA)
    const { result } = renderHook(() => useSettings())
    expect(result.current.loading).toBe(true)
    expect(result.current.schema).toBeNull()
  })

  it('should populate schema and data after fetch resolves', async () => {
    mockFetchSchema.mockResolvedValue(MOCK_SCHEMA)
    mockFetchUserSettings.mockResolvedValue(MOCK_DATA)
    const { result } = renderHook(() => useSettings())
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.schema).toEqual(MOCK_SCHEMA)
    expect(result.current.data).toEqual(MOCK_DATA)
    expect(result.current.error).toBeNull()
  })

  it('should set error when fetchSchema throws', async () => {
    mockFetchSchema.mockRejectedValue(new Error('Schema fetch failed'))
    mockFetchUserSettings.mockResolvedValue(MOCK_DATA)
    const { result } = renderHook(() => useSettings())
    await waitFor(() => expect(result.current.loading).toBe(false))
    expect(result.current.error).toBe('Schema fetch failed')
    expect(result.current.schema).toBeNull()
  })

  it('should call saveUserSettings with data and update state on save', async () => {
    mockFetchSchema.mockResolvedValue(MOCK_SCHEMA)
    mockFetchUserSettings.mockResolvedValue(MOCK_DATA)
    const updatedData = { theme: 'light' }
    mockSaveUserSettings.mockResolvedValue(updatedData)

    const { result } = renderHook(() => useSettings())
    await waitFor(() => expect(result.current.loading).toBe(false))

    await act(async () => {
      await result.current.save(updatedData)
    })

    expect(mockSaveUserSettings).toHaveBeenCalledWith(updatedData)
    expect(result.current.data).toEqual(updatedData)
    expect(result.current.saving).toBe(false)
  })

  it('should set saving true while save is in progress', async () => {
    mockFetchSchema.mockResolvedValue(MOCK_SCHEMA)
    mockFetchUserSettings.mockResolvedValue(MOCK_DATA)

    let resolveSave!: (v: unknown) => void
    mockSaveUserSettings.mockReturnValue(new Promise((r) => { resolveSave = r }))

    const { result } = renderHook(() => useSettings())
    await waitFor(() => expect(result.current.loading).toBe(false))

    act(() => {
      void result.current.save({ theme: 'light' })
    })

    expect(result.current.saving).toBe(true)
    resolveSave({ theme: 'light' })
  })

  it('should set error on save failure', async () => {
    mockFetchSchema.mockResolvedValue(MOCK_SCHEMA)
    mockFetchUserSettings.mockResolvedValue(MOCK_DATA)
    mockSaveUserSettings.mockRejectedValue(new Error('Save failed'))

    const { result } = renderHook(() => useSettings())
    await waitFor(() => expect(result.current.loading).toBe(false))

    await act(async () => {
      await result.current.save({ theme: 'light' })
    })

    expect(result.current.error).toBe('Save failed')
    expect(result.current.saving).toBe(false)
  })
})
