# Memory Injection — Recall 2.0

How retrieved memories reach Claude's context window. This is the final mile — the part that determines whether Claude actually uses the memory or ignores it.

**Last updated**: 2026-03-16

---

## The Problem with Current Injection

Recall 1.0 injects memories as a text block prepended to the user prompt:

```
[MEMORY CONTEXT]
- memory 1 text here
- memory 2 text here
- memory 3 text here
[END MEMORY CONTEXT]

User: What's the Proxmox IP?
```

This works but is suboptimal:
- Claude processes the memory block before the actual question — low-relevance memories consume attention
- All memories get equal formatting weight — no signal about which ones are most activated
- No indication of recency, source, or reliability
- Memories that contradict each other are presented side by side with no flag

---

## Principles for Better Injection

### 1. Injection format should signal confidence and recency
The activation level from the Hopfield layer is a meaningful quantity. A memory with activation 0.95 is more reliably relevant than one with activation 0.30. The format should communicate this.

### 2. The most relevant memories should be closest to the actual question
Research on attention in transformer models suggests that content close to the query has higher influence on generation. Memory injection should front-load the highest-activation memories closest to the user's question, not at the top of the context.

### 3. Abstract memories and episodic memories should be distinguished
A schematic memory ("Tim's homelab services degrade under memory pressure") is different from an episodic one ("Got OOM error on casaclaude on March 15"). They serve different purposes and should be labeled.

### 4. Contradictions should be explicit
If the system has two memories that conflict, surface the conflict rather than hiding it.

### 5. Source transparency
Where did this memory come from? An edit the agent made yesterday is different from something stored six months ago in a different project context.

---

## Proposed Injection Format

This is an open question — see candidate formats below.

### Format A: Structured XML (current Recall 1.0 style, improved)

```xml
<recall>
  <working_set>
    <!-- High activation (>0.7), recent, behavioral -->
    <memory activation="0.92" last_used="2h_ago" source="session_summary" level="episodic">
      The Proxmox API returns 503 when the pve-cluster service is down, not when Proxmox itself is down.
    </memory>
    <memory activation="0.85" last_used="3d_ago" source="observe_edit" level="semantic">
      casaclaude is at 192.168.50.19, ollama host at 192.168.50.62.
    </memory>
  </working_set>
  <context>
    <!-- Medium activation (0.4-0.7), thematic -->
    <memory activation="0.55" last_used="12d_ago" level="schematic">
      Homelab services degrade under memory pressure before CPU pressure.
    </memory>
  </context>
  <contradictions>
    <conflict>Two memories disagree on the RTX 3090 IP. Recorded: 192.168.50.62 and 192.168.50.63.</conflict>
  </contradictions>
</recall>
```

**Pros**: Structured, parseable, Claude can reference specific sections
**Cons**: XML overhead in the context window

### Format B: Markdown with Activation Signals

```markdown
**RECALL** *(3 high-relevance, 1 contextual, 1 flag)*

▌ [0.92 | 2h ago] The Proxmox API returns 503 when pve-cluster is down, not Proxmox itself.
▌ [0.85 | 3d ago] casaclaude: 192.168.50.19 | ollama: 192.168.50.62

── context ──
▫ [0.55 | 12d ago] Homelab degrades under memory pressure before CPU.

⚠ Conflict: Two IPs recorded for RTX 3090 (192.168.50.62 vs 192.168.50.63)
```

**Pros**: Compact, human-readable, Claude can parse naturally
**Cons**: Less structured, activation numbers may not be meaningful to Claude

### Format C: No Formatting — Trust Claude to Weight

Simply inject the most relevant memories as natural sentences, ordered by activation, with a brief header:

```
Based on your context, these memories are most relevant:

The Proxmox API returns 503 when pve-cluster is down, not Proxmox itself. (high confidence, recently used)
casaclaude is 192.168.50.19. The Ollama host is 192.168.50.62. (high confidence)
Homelab services tend to degrade under memory pressure before showing CPU issues. (pattern, 12 days old)
```

**Pros**: Most natural, least token overhead
**Cons**: No explicit structure for Claude to reference, loses activation signal

---

## Injection Position

Where in the prompt does memory injection go?

### Option A: Top of Context (Recall 1.0 style)
Memory block → User message

Drawback: high-activation memories are maximally far from the user's actual question.

### Option B: Just Before the User Message (Proposed Default)
System prompt → ... → Memory injection → User message

Memory is closest to the question when injected. Higher attention weight.

### Option C: Inline Expansion
Don't inject as a block. Instead, expand mentions in the user's message with inline memory references.

```
User: "What's the IP for the ollama host?"
→ After injection: "What's the IP for the ollama host? [Note: ollama host is 192.168.50.62 (from memory)]"
```

Complex to implement, potentially most natural. Open question.

---

## What Memories Get Injected

**Budget**: Claude has a context window. Memory injection competes with the conversation itself.

Current Recall 1.0 injects top-K (configurable, usually 5-10) memories. But K is a fixed number, not a quality threshold.

Better approach:
```
Inject memories where:
  activation_level >= INJECTION_THRESHOLD (e.g., 0.30)
  AND memory.text tokens <= INJECTION_BUDGET
  AND total_injected <= MAX_INJECTION_MEMORIES
```

Order of injection:
1. Contradictions (always — Claude needs to know when the system is uncertain)
2. High-activation working set memories (activation >= 0.7)
3. Medium-activation contextual memories (0.3 <= activation < 0.7)
4. Abstract/schematic memories (if space remains)

---

## Hook Integration

The current hooks that handle injection:
- `recall-retrieve.js` (UserPromptSubmit) — queries before every prompt
- `observe-edit.js` (PostToolUse) — stores memories from edits
- `recall-session-summary.js` (Stop) — stores session summaries

Recall 2.0 hook requirements:
- Same events, same calling convention (backward compat per OD-07)
- New: inject activation levels and memory tiers, not just text
- New: surface contradiction flags
- New: support for the injection format TBD above

---

## Open Questions (High Priority)

1. **What injection format actually changes Claude's behavior?** This requires A/B testing — inject same memories in Format A vs Format B vs Format C, measure retrieval quality from Claude's responses.

2. **Does injection position (top vs bottom) matter?** Academic research on "lost in the middle" effects in LLMs suggests position matters. But Claude's architecture may handle this differently.

3. **Should injection be dynamic during a conversation?** Current model: inject once at UserPromptSubmit. Alternative: re-inject after each tool use as context evolves.

4. **What is the right injection budget?** Too few memories → misses. Too many → dilutes attention. What's the empirical sweet spot for this corpus and these tasks?

5. **Can we teach Claude to ask for more context?** If Claude knows Recall exists, it could request specific memories ("do you have anything about the Proxmox cluster setup?"). This turns passive injection into active retrieval.
