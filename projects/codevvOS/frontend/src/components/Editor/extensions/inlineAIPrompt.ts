import { StateField, StateEffect } from '@codemirror/state'
import { Decoration, DecorationSet, EditorView, WidgetType, keymap } from '@codemirror/view'
import type { Extension } from '@codemirror/state'

// ---------------------------------------------------------------------------
// State shape
// ---------------------------------------------------------------------------

interface InlinePromptState {
  active: boolean
  prompt: string
  originalDoc: string
  newDoc: string | null
  /** Cursor position where the widget should appear. */
  cursorPos: number
}

const initialState: InlinePromptState = {
  active: false,
  prompt: '',
  originalDoc: '',
  newDoc: null,
  cursorPos: 0,
}

// ---------------------------------------------------------------------------
// State effects (commands sent into the StateField)
// ---------------------------------------------------------------------------

export const openEffect = StateEffect.define<{ cursorPos: number; originalDoc: string }>()
export const closeEffect = StateEffect.define<void>()
export const setNewDocEffect = StateEffect.define<string>()

// ---------------------------------------------------------------------------
// StateField
// ---------------------------------------------------------------------------

export const inlinePromptField = StateField.define<InlinePromptState>({
  create() {
    return { ...initialState }
  },
  update(state, tr) {
    for (const effect of tr.effects) {
      if (effect.is(openEffect)) {
        return {
          ...state,
          active: true,
          cursorPos: effect.value.cursorPos,
          originalDoc: effect.value.originalDoc,
          newDoc: null,
          prompt: '',
        }
      }
      if (effect.is(closeEffect)) {
        return { ...initialState }
      }
      if (effect.is(setNewDocEffect)) {
        return { ...state, newDoc: effect.value }
      }
    }
    return state
  },
})

// ---------------------------------------------------------------------------
// Widget renderer (DOM only — React component is rendered via portal)
// ---------------------------------------------------------------------------

class InlinePromptWidgetType extends WidgetType {
  constructor(
    private readonly view: EditorView,
    private readonly cursorPos: number,
  ) {
    super()
  }

  toDOM(): HTMLElement {
    const container = document.createElement('div')
    container.style.cssText =
      'display:inline-block;vertical-align:top;padding:2px 0;width:100%'

    // We fire a custom event so CodeMirrorEditor can mount the React widget
    const event = new CustomEvent('inline-prompt-open', {
      bubbles: true,
      detail: { container, cursorPos: this.cursorPos, view: this.view },
    })
    // Defer so the DOM node is attached first
    queueMicrotask(() => container.dispatchEvent(event))
    return container
  }

  ignoreEvent(): boolean {
    return false
  }
}

// ---------------------------------------------------------------------------
// Decoration StateField — builds widget decoration when active
// ---------------------------------------------------------------------------

const decorationField = StateField.define<DecorationSet>({
  create() {
    return Decoration.none
  },
  update(decorations, tr) {
    const promptState = tr.state.field(inlinePromptField)
    if (!promptState.active) return Decoration.none

    const widget = Decoration.widget({
      widget: new InlinePromptWidgetType(
        tr.state as unknown as EditorView,
        promptState.cursorPos,
      ),
      side: 1,
    })
    return Decoration.set([widget.range(promptState.cursorPos)])
  },
  provide: (f) => EditorView.decorations.from(f),
})

// ---------------------------------------------------------------------------
// Keymap action
// ---------------------------------------------------------------------------

/** Opens the inline prompt at the current cursor position. */
export function openInlinePrompt(view: EditorView): boolean {
  const cursorPos = view.state.selection.main.head
  const originalDoc = view.state.doc.toString()
  view.dispatch({
    effects: openEffect.of({ cursorPos, originalDoc }),
  })
  return true
}

// ---------------------------------------------------------------------------
// Public extension factory
// ---------------------------------------------------------------------------

/** Returns the CM6 extensions enabling Cmd+K inline AI prompt. */
export function inlineAIPromptExtension(): Extension[] {
  return [
    inlinePromptField,
    decorationField,
    keymap.of([{ key: 'Mod-k', run: openInlinePrompt }]),
  ]
}
