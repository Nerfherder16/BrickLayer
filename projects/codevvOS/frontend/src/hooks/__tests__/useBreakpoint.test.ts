import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, afterEach, vi } from 'vitest'
import { useBreakpoint } from '../useBreakpoint'

function setWidth(width: number): void {
  Object.defineProperty(window, 'innerWidth', {
    writable: true,
    configurable: true,
    value: width,
  })
}

describe('useBreakpoint', () => {
  const originalInnerWidth = window.innerWidth

  afterEach(() => {
    setWidth(originalInnerWidth)
    vi.clearAllTimers()
    vi.useRealTimers()
  })

  it('should return isMobile true and isDesktop false when innerWidth is 375', () => {
    setWidth(375)
    const { result } = renderHook(() => useBreakpoint())
    expect(result.current.isMobile).toBe(true)
    expect(result.current.isTablet).toBe(false)
    expect(result.current.isDesktop).toBe(false)
  })

  it('should return isDesktop true and isMobile false when innerWidth is 1280', () => {
    setWidth(1280)
    const { result } = renderHook(() => useBreakpoint())
    expect(result.current.isMobile).toBe(false)
    expect(result.current.isTablet).toBe(false)
    expect(result.current.isDesktop).toBe(true)
  })

  it('should return isTablet true when innerWidth is 900', () => {
    setWidth(900)
    const { result } = renderHook(() => useBreakpoint())
    expect(result.current.isMobile).toBe(false)
    expect(result.current.isTablet).toBe(true)
    expect(result.current.isDesktop).toBe(false)
  })

  it('should update breakpoint after resize with 150ms debounce', async () => {
    vi.useFakeTimers()
    setWidth(375)
    const { result } = renderHook(() => useBreakpoint())
    expect(result.current.isMobile).toBe(true)

    act(() => {
      setWidth(1280)
      window.dispatchEvent(new Event('resize'))
    })

    // Before debounce — still mobile
    expect(result.current.isMobile).toBe(true)

    await act(async () => {
      vi.advanceTimersByTime(150)
    })

    expect(result.current.isDesktop).toBe(true)
    expect(result.current.isMobile).toBe(false)
  })
})
