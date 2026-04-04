import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import React from 'react'

// Mock the notification store
vi.mock('../../../stores/notificationStore', () => ({
  useNotificationStore: vi.fn(),
}))

// Mock useNotifications hook
vi.mock('../../../hooks/useNotifications', () => ({
  useNotifications: vi.fn(),
}))

// Mock framer-motion to avoid animation complexity in tests
vi.mock('framer-motion', () => ({
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  motion: {
    div: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement> & { children?: React.ReactNode }) => (
      <div {...props}>{children}</div>
    ),
  },
}))

import NotificationCenter from '../NotificationCenter'
import { useNotifications } from '../../../hooks/useNotifications'

const mockUseNotifications = vi.mocked(useNotifications)

function makeDefaultState(overrides = {}) {
  return {
    items: [],
    unread_count: 0,
    loading: false,
    fetchRecent: vi.fn(),
    markRead: vi.fn(),
    addToast: vi.fn(),
    ...overrides,
  }
}

describe('NotificationCenter', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUseNotifications.mockReturnValue(makeDefaultState())
  })

  it('renders the notification bell button', () => {
    render(<NotificationCenter />)
    expect(screen.getByTestId('notification-bell')).toBeTruthy()
  })

  it('shows unread badge with count when unread_count > 0', () => {
    mockUseNotifications.mockReturnValue(makeDefaultState({ unread_count: 3 }))
    render(<NotificationCenter />)
    expect(screen.getByText('3')).toBeTruthy()
  })

  it('does not show badge when unread_count is 0', () => {
    mockUseNotifications.mockReturnValue(makeDefaultState({ unread_count: 0 }))
    render(<NotificationCenter />)
    expect(screen.queryByTestId('unread-badge')).toBeNull()
  })

  it('opens dropdown when bell is clicked', () => {
    render(<NotificationCenter />)
    expect(screen.queryByTestId('notification-dropdown')).toBeNull()
    fireEvent.click(screen.getByTestId('notification-bell'))
    expect(screen.getByTestId('notification-dropdown')).toBeTruthy()
  })

  it('lists notification items in dropdown', () => {
    const items = [
      {
        id: '1',
        tenant_id: 'tenant-1',
        user_id: 'user-1',
        type: 'info',
        title: 'Hello World',
        body: 'Some message',
        read: false,
        created_at: '2026-04-03T10:00:00Z',
      },
    ]
    mockUseNotifications.mockReturnValue(makeDefaultState({ items, unread_count: 1 }))
    render(<NotificationCenter />)
    fireEvent.click(screen.getByTestId('notification-bell'))
    expect(screen.getByText('Hello World')).toBeTruthy()
  })

  it('closes dropdown when bell is clicked again', () => {
    render(<NotificationCenter />)
    fireEvent.click(screen.getByTestId('notification-bell'))
    expect(screen.getByTestId('notification-dropdown')).toBeTruthy()
    fireEvent.click(screen.getByTestId('notification-bell'))
    expect(screen.queryByTestId('notification-dropdown')).toBeNull()
  })
})
