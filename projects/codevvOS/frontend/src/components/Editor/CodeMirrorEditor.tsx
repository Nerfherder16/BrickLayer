import { useEffect, useRef } from 'react'
import { EditorView } from '@codemirror/view'
import { EditorState, Compartment } from '@codemirror/state'
import { oneDark } from '@codemirror/theme-one-dark'
import { useCodeMirrorLanguage } from './useCodeMirrorLanguage'

export interface CodeMirrorEditorProps {
  value: string
  onChange: (value: string) => void
  language?: 'javascript' | 'typescript' | 'python' | 'plain'
  readOnly?: boolean
}

/** CodeMirror 6 editor component with language detection, dark theme, and controlled value. */
export default function CodeMirrorEditor({
  value,
  onChange,
  language,
  readOnly = false,
}: CodeMirrorEditorProps): JSX.Element {
  const containerRef = useRef<HTMLDivElement>(null)
  const viewRef = useRef<EditorView | null>(null)
  const languageExtension = useCodeMirrorLanguage(language)
  const languageCompartment = useRef(new Compartment())

  useEffect(() => {
    if (containerRef.current === null) return

    const startState = EditorState.create({
      doc: value,
      extensions: [
        oneDark,
        languageCompartment.current.of(languageExtension),
        EditorView.updateListener.of((update) => {
          if (update.docChanged) {
            onChange(update.state.doc.toString())
          }
        }),
        EditorView.editable.of(!readOnly),
      ],
    })

    const view = new EditorView({
      state: startState,
      parent: containerRef.current,
    })

    viewRef.current = view

    return () => {
      view.destroy()
      viewRef.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Sync external value changes into the editor without re-mounting
  useEffect(() => {
    const view = viewRef.current
    if (!view) return
    const current = view.state.doc.toString()
    if (current !== value) {
      view.dispatch({
        changes: { from: 0, to: current.length, insert: value },
      })
    }
  }, [value])

  // Swap language extension when `language` prop changes
  useEffect(() => {
    const view = viewRef.current
    if (!view) return
    view.dispatch({
      effects: languageCompartment.current.reconfigure(languageExtension),
    })
  }, [languageExtension])

  return <div ref={containerRef} data-testid="codemirror-editor" style={{ height: '100%' }} />
}
