import { useState } from 'react'
import { Bell } from 'lucide-react'
import { AnimatePresence, motion } from 'framer-motion'
import { useNotifications } from '../../hooks/useNotifications'
import type { NotificationItem } from '../../stores/notificationStore'

export default function NotificationCenter(): JSX.Element {
  const [open, setOpen] = useState(false)
  const { items, unread_count, markRead } = useNotifications()

  function handleMarkAllRead(): void {
    const unread = items.filter((n) => !n.read)
    for (const n of unread) {
      void markRead(n.id)
    }
  }

  return (
    <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
      <button
        type="button"
        aria-label={`Notifications${unread_count > 0 ? `, ${unread_count} unread` : ''}`}
        data-testid="notification-bell"
        onClick={() => { setOpen((prev) => !prev) }}
        style={{
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          padding: '8px',
          display: 'flex',
          alignItems: 'center',
          position: 'relative',
          color: 'var(--color-text-secondary)',
        }}
      >
        <Bell size={20} />
        {unread_count > 0 && (
          <span
            data-testid="unread-badge"
            style={{
              position: 'absolute',
              top: '2px',
              right: '2px',
              minWidth: '16px',
              height: '16px',
              borderRadius: '8px',
              background: 'var(--color-accent, #6b66f8)',
              color: 'var(--color-text-on-accent, #fff)',
              fontSize: '10px',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '0 3px',
              lineHeight: 1,
            }}
          >
            {unread_count}
          </span>
        )}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            data-testid="notification-dropdown"
            initial={{ opacity: 0, y: -8, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            style={{
              position: 'absolute',
              bottom: '52px',
              right: 0,
              width: '320px',
              maxHeight: '400px',
              overflowY: 'auto',
              background: 'var(--color-surface-elevated, #1e1e2e)',
              border: '1px solid var(--color-border, rgba(255,255,255,0.08))',
              borderRadius: '8px',
              boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
              zIndex: 1000,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 12px 8px',
                borderBottom: '1px solid var(--color-border, rgba(255,255,255,0.08))',
              }}
            >
              <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text, #cdd6f4)' }}>
                Notifications
              </span>
              {unread_count > 0 && (
                <button
                  type="button"
                  onClick={handleMarkAllRead}
                  style={{
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    fontSize: '11px',
                    color: 'var(--color-accent, #6b66f8)',
                    padding: '2px 4px',
                  }}
                >
                  Mark all read
                </button>
              )}
            </div>

            {items.length === 0 ? (
              <div
                style={{
                  padding: '24px 12px',
                  textAlign: 'center',
                  fontSize: '13px',
                  color: 'var(--color-text-muted, #6c7086)',
                }}
              >
                No notifications
              </div>
            ) : (
              items.map((n) => <NotificationRow key={n.id} item={n} onMarkRead={markRead} />)
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

interface NotificationRowProps {
  item: NotificationItem
  onMarkRead: (id: string) => Promise<void>
}

function NotificationRow({ item, onMarkRead }: NotificationRowProps): JSX.Element {
  return (
    <div
      onClick={() => { if (!item.read) void onMarkRead(item.id) }}
      style={{
        padding: '10px 12px',
        borderBottom: '1px solid var(--color-border, rgba(255,255,255,0.05))',
        cursor: item.read ? 'default' : 'pointer',
        background: item.read ? 'transparent' : 'var(--color-surface-highlight, rgba(107,102,248,0.06))',
        opacity: item.read ? 0.6 : 1,
      }}
    >
      <div
        style={{
          fontSize: '13px',
          fontWeight: item.read ? 400 : 600,
          color: 'var(--color-text, #cdd6f4)',
          marginBottom: item.body ? '2px' : 0,
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
        }}
      >
        {item.title}
      </div>
      {item.body && (
        <div
          style={{
            fontSize: '12px',
            color: 'var(--color-text-muted, #6c7086)',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
          }}
        >
          {item.body}
        </div>
      )}
    </div>
  )
}
