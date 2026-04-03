import { StateField, RangeSetBuilder } from '@codemirror/state'
import { Decoration, DecorationSet, EditorView } from '@codemirror/view'
import type { Extension } from '@codemirror/state'

// ---------------------------------------------------------------------------
// Line diff helpers
// ---------------------------------------------------------------------------

export interface DiffLine {
  /** 0-based index into the NEW document's lines. */
  lineIndex: number
  type: 'added' | 'removed'
}

/**
 * Compute a simple line-level diff between originalDoc and newDoc.
 *
 * Strategy: lines present in newDoc but not in originalDoc → added;
 * lines present in originalDoc but not in newDoc → removed (annotated at
 * their original position, mapped to line 0 in the new doc for display).
 */
export function computeDiffLines(originalDoc: string, newDoc: string): DiffLine[] {
  const origLines = originalDoc.split('\n')
  const newLines = newDoc.split('\n')

  const origSet = new Set(origLines)
  const newSet = new Set(newLines)

  const result: DiffLine[] = []

  newLines.forEach((line, idx) => {
    if (!origSet.has(line)) {
      result.push({ lineIndex: idx, type: 'added' })
    }
  })

  origLines.forEach((line, idx) => {
    if (!newSet.has(line)) {
      result.push({ lineIndex: idx, type: 'removed' })
    }
  })

  return result
}

// ---------------------------------------------------------------------------
// CM6 extension
// ---------------------------------------------------------------------------

const addedLineMark = Decoration.mark({ class: 'cm-line-added' })
const removedLineMark = Decoration.mark({ class: 'cm-line-removed' })

function buildDecorations(view: EditorView, diffs: DiffLine[]): DecorationSet {
  const builder = new RangeSetBuilder<Decoration>()
  const doc = view.state.doc

  // Sort by line index so builder.add() is called in order
  const sorted = [...diffs].sort((a, b) => a.lineIndex - b.lineIndex)

  for (const diff of sorted) {
    const lineNum = diff.lineIndex + 1 // CM6 lines are 1-based
    if (lineNum < 1 || lineNum > doc.lines) continue
    const line = doc.line(lineNum)
    const mark = diff.type === 'added' ? addedLineMark : removedLineMark
    builder.add(line.from, line.to, mark)
  }

  return builder.finish()
}

/**
 * Returns a CM6 Extension that decorates diff lines between originalDoc and
 * newDoc. Added lines get class `cm-line-added`; removed lines get
 * `cm-line-removed`.
 */
export function diffDecorationsExtension(originalDoc: string, newDoc: string): Extension {
  const diffs = computeDiffLines(originalDoc, newDoc)

  return StateField.define<DecorationSet>({
    create(state) {
      const mockView = { state } as unknown as EditorView
      return buildDecorations(mockView, diffs)
    },
    update(decorations, _tr) {
      return decorations
    },
    provide: (f) => EditorView.decorations.from(f),
  })
}
