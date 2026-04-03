import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import React from 'react'
import { ThemeProvider, useTheme } from '../ThemeContext'

function TestConsumer(): JSX.Element {
  const { theme, toggleTheme } = useTheme()
  return (
    <div>
      <span data-testid="theme-value">{theme}</span>
      <button data-testid="theme-toggle" onClick={toggleTheme} type="button">
        toggle
      </button>
    </div>
  )
}

function renderWithProvider() {
  return render(
    <ThemeProvider>
      <TestConsumer />
    </ThemeProvider>,
  )
}

describe('ThemeContext', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.classList.remove('theme-light')
  })

  afterEach(() => {
    localStorage.clear()
    document.documentElement.classList.remove('theme-light')
    vi.restoreAllMocks()
  })

  it('defaults to dark — documentElement does NOT have theme-light class', () => {
    renderWithProvider()
    expect(document.documentElement.classList.contains('theme-light')).toBe(false)
    expect(screen.getByTestId('theme-value').textContent).toBe('dark')
  })

  it('toggleTheme() adds theme-light class to documentElement', () => {
    renderWithProvider()
    fireEvent.click(screen.getByTestId('theme-toggle'))
    expect(document.documentElement.classList.contains('theme-light')).toBe(true)
  })

  it('toggleTheme() a second time removes theme-light class', () => {
    renderWithProvider()
    fireEvent.click(screen.getByTestId('theme-toggle'))
    fireEvent.click(screen.getByTestId('theme-toggle'))
    expect(document.documentElement.classList.contains('theme-light')).toBe(false)
  })

  it('saves theme to localStorage["codevv-theme"] on toggle', () => {
    renderWithProvider()
    fireEvent.click(screen.getByTestId('theme-toggle'))
    expect(localStorage.getItem('codevv-theme')).toBe('light')
    fireEvent.click(screen.getByTestId('theme-toggle'))
    expect(localStorage.getItem('codevv-theme')).toBe('dark')
  })

  it('re-mount with localStorage "light" preset applies theme-light immediately', () => {
    localStorage.setItem('codevv-theme', 'light')
    renderWithProvider()
    expect(document.documentElement.classList.contains('theme-light')).toBe(true)
    expect(screen.getByTestId('theme-value').textContent).toBe('light')
  })
})
