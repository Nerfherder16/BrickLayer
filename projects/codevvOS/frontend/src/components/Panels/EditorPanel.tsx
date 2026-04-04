import CodeMirrorEditor from '../Editor/CodeMirrorEditor'

const useCodeMirror = true // feature flag — default true

interface EditorPanelProps {
  value?: string
  onChange?: (value: string) => void
  language?: 'javascript' | 'typescript' | 'python' | 'plain'
  readOnly?: boolean
}

/** Editor panel — renders CodeMirrorEditor or Monaco based on feature flag. */
export default function EditorPanel({
  value = '',
  onChange,
  language,
  readOnly = false,
}: EditorPanelProps): JSX.Element {
  const handleChange = (newValue: string): void => {
    onChange?.(newValue)
  }

  if (useCodeMirror) {
    return (
      <CodeMirrorEditor
        value={value}
        onChange={handleChange}
        language={language}
        readOnly={readOnly}
      />
    )
  }

  // Monaco fallback (feature flag = false)
  return <div data-testid="monaco-editor" style={{ height: '100%' }} />
}
