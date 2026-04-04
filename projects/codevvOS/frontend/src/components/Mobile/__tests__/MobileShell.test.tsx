import React from 'react'
import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, fireEvent, cleanup } from '@testing-library/react'

vi.mock('@/components/Panels/WelcomePanel', () => ({
  default: () => <div data-testid="welcome-panel">Welcome Panel</div>,
}))

vi.mock('@/components/Mobile/ComingSoonPanel', () => ({
  default: ({ label }: { label: string }) => (
    <div data-testid={`coming-soon-${label.toLowerCase().replace(/\s+/g, '-')}`}>
      Coming in Phase 3
    </div>
  ),
}))

const { default: MobileShell } = await import('../MobileShell')

afterEach(() => {
  cleanup()
})

describe('MobileShell', () => {
  it('should render 5 tab buttons', () => {
    render(<MobileShell />)
    const tabs = screen.getAllByRole('tab')
    expect(tabs.length).toBeGreaterThanOrEqual(5)
  })

  it('should show Dashboard (WelcomePanel) as active by default', () => {
    render(<MobileShell />)
    expect(screen.getByTestId('welcome-panel')).toBeDefined()
  })

  it('should show Files coming-soon content when Files tab is clicked', () => {
    render(<MobileShell />)
    fireEvent.click(screen.getByText('Files'))
    expect(screen.getByTestId('coming-soon-files')).toBeDefined()
  })

  it('should show Terminal coming-soon content when Terminal tab is clicked', () => {
    render(<MobileShell />)
    fireEvent.click(screen.getByText('Terminal'))
    expect(screen.getByTestId('coming-soon-terminal')).toBeDefined()
  })

  it('should have tab bar with position fixed style', () => {
    render(<MobileShell />)
    const tabBar = screen.getByRole('tablist')
    expect(tabBar.style.position).toBe('fixed')
  })

  it('should have panel content area with calc() height', () => {
    render(<MobileShell />)
    const content = screen.getByTestId('panel-content')
    expect(content.getAttribute('style')).toContain('calc(')
  })
})
