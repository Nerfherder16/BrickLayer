import { useEffect, useRef, useCallback } from 'react'

export interface IframeSandboxProps {
  compiled: string
  title: string
  onError: (msg: string) => void
}

function buildSrcdoc(compiled: string, nonce: string): string {
  return [
    '<!DOCTYPE html>',
    '<html><head>',
    `<meta http-equiv="Content-Security-Policy" content="script-src 'nonce-${nonce}'">`,
    '</head><body>',
    `<script nonce="${nonce}">`,
    compiled,
    '</script></body></html>',
  ].join('\n')
}

/** Sandboxed iframe that runs compiled artifact JS with a per-mount nonce. */
export function IframeSandbox({ compiled, title, onError }: IframeSandboxProps): JSX.Element {
  const nonceRef = useRef<string>(crypto.randomUUID())

  const handleMessage = useCallback(
    (event: MessageEvent): void => {
      if (
        event.data &&
        typeof event.data === 'object' &&
        event.data.type === 'error' &&
        typeof event.data.message === 'string'
      ) {
        onError(event.data.message as string)
      }
    },
    [onError],
  )

  useEffect(() => {
    window.addEventListener('message', handleMessage)
    return () => {
      window.removeEventListener('message', handleMessage)
    }
  }, [handleMessage])

  return (
    <iframe
      data-testid="artifact-iframe"
      sandbox="allow-scripts"
      srcDoc={buildSrcdoc(compiled, nonceRef.current)}
      title={title}
      style={{ width: '100%', height: '100%', border: 'none' }}
    />
  )
}
