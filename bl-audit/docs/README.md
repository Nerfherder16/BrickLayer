# Project Docs

Place supporting documents here that ground the research agents in authoritative project knowledge.

The `question-designer` agent reads everything in this folder as **Tier 1 (ground truth)** —
treated as more authoritative than Claude-generated files (findings, analysis, simulation notes).

## What belongs here

- Architecture decision records (ADRs)
- Design specs and technical briefs
- Regulatory opinions or legal memos
- Investor/stakeholder documents that define the system's constraints
- Anything the human wrote or reviewed and considers authoritative

## What does NOT belong here

- Claude-generated analysis files (put those in `findings/`)
- Simulation outputs or run logs
- Draft documents or notes you haven't validated

## Naming convention

No strict convention required. The agent reads all `.md`, `.txt`, and `.pdf` files in this
folder. Descriptive filenames help: `regulatory-classification-memo.md`, `system-design-spec.md`.

## Note on authority

Documents in `docs/` outrank findings and Claude-generated files but are outranked by
`project-brief.md` (if present) and Recall canon anchors. See `program.md` for the full
source authority hierarchy.
