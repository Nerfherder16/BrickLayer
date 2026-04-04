import { useEffect } from 'react'
import { useNotificationStore } from '../stores/notificationStore'
import type { NotificationItem } from '../stores/notificationStore'

const POLL_INTERVAL_MS = 30_000

interface UseNotificationsReturn {
  items: NotificationItem[]
  unread_count: number
  loading: boolean
  fetchRecent: () => Promise<void>
  markRead: (id: string) => Promise<void>
  addToast: (notification: NotificationItem) => void
}

export function useNotifications(): UseNotificationsReturn {
  const { items, unread_count, loading, fetchRecent, markRead, addToast } = useNotificationStore()

  useEffect(() => {
    void fetchRecent()
    const interval = setInterval(() => { void fetchRecent() }, POLL_INTERVAL_MS)
    return () => { clearInterval(interval) }
  }, [fetchRecent])

  return { items, unread_count, loading, fetchRecent, markRead, addToast }
}
