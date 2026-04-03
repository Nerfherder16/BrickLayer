import AnsiToHtml from 'ansi-to-html'

const converter = new AnsiToHtml({ escapeXML: true })

interface AnsiOutputProps {
  lines: string[]
}

/** Renders ANSI-escaped terminal output lines as colored HTML. */
export function AnsiOutput({ lines }: AnsiOutputProps): JSX.Element {
  return (
    <div data-testid="ansi-output" style={{ fontFamily: 'var(--font-mono, monospace)', fontSize: '13px', lineHeight: '1.5' }}>
      {lines.map((line, i) => (
        <div
          key={i}
          // eslint-disable-next-line react/no-danger
          dangerouslySetInnerHTML={{ __html: converter.toHtml(line) }}
        />
      ))}
    </div>
  )
}
