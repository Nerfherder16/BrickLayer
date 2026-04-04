import React, { useEffect, useRef, useState } from 'react'
import { usePreviewStore } from '../../stores/previewStore'
import { ViewportToolbar } from '../Preview/ViewportToolbar'
import { ErrorOverlay } from '../Preview/ErrorOverlay'

/** Live preview panel — sandboxed iframe with viewport control and SSE auto-reload. */
export default function LivePreviewPanel(): JSX.Element {
  const { previewUrl, refresh } = usePreviewStore()
  const [viewport, setViewport] = useState<number>(1440)
  const [hasError, setHasError] = useState<boolean>(false)
  const iframeRef = useRef<HTMLIFrameElement>(null)

  // Listen for iframe load errors via DOM event listener
  useEffect(() => {
    const iframe = iframeRef.current
    if (!iframe) return

    function handleIframeError(): void {
      setHasError(true)
    }

    iframe.addEventListener('error', handleIframeError)
    return () => {
      iframe.removeEventListener('error', handleIframeError)
    }
  }, [])

  // Auto-reload via SSE
  useEffect(() => {
    const es = new EventSource('/api/events')
    es.addEventListener('preview-reload', () => {
      refresh()
    })
    return () => {
      es.close()
    }
  }, [refresh])

  function handleRetry(): void {
    setHasError(false)
    refresh()
  }

  function handleRefresh(): void {
    setHasError(false)
    refresh()
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        background: 'var(--color-bg)',
        overflow: 'hidden',
      }}
    >
      <ViewportToolbar
        onRefresh={handleRefresh}
        viewport={viewport}
        onViewportChange={setViewport}
        url={previewUrl}
      />

      <div
        style={{
          flex: 1,
          display: 'flex',
          justifyContent: 'center',
          overflow: 'auto',
          background: 'var(--color-bg-secondary)',
          position: 'relative',
        }}
      >
        <div
          data-testid="iframe-container"
          style={{
            width: `${viewport}px`,
            height: '100%',
            position: 'relative',
            flexShrink: 0,
          }}
        >
          <iframe
            ref={iframeRef}
            data-testid="live-preview-iframe"
            src={previewUrl}
            sandbox="allow-scripts allow-forms allow-popups"
            style={{
              width: '100%',
              height: '100%',
              border: 'none',
              display: 'block',
            }}
            title="Live Preview"
          />
          <ErrorOverlay visible={hasError} onRetry={handleRetry} />
        </div>
      </div>
    </div>
  )
}
