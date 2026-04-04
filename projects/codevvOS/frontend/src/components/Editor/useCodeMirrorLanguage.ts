import type { Extension } from '@codemirror/state'
import { javascript } from '@codemirror/lang-javascript'
import { python } from '@codemirror/lang-python'

/** Returns the appropriate CM6 LanguageSupport for the given language string. */
export function useCodeMirrorLanguage(language?: string): Extension {
  if (language === 'javascript') return javascript({ typescript: false })
  if (language === 'typescript') return javascript({ typescript: true })
  if (language === 'python') return python()
  return []
}
