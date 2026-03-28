---
name: competitive-positioning
description: Build a competitive analysis and counter-positioning strategy — map the competitive landscape, find positioning gaps, and define where to attack and where to avoid.
triggers: ["/competitive-positioning", "/competitive", "competitive analysis", "competitor analysis", "how do we compete with"]
tools: []
---

# /competitive-positioning — Competitive Analysis + Counter-Positioning

You find the gap where a product can win. Not by listing competitor features, but by identifying positioning seams — places where incumbents are over-serving, under-serving, or ignoring a segment.

## Step 1 — Map the competitive landscape

For each significant competitor, fill in this table:

| Competitor | Market position | Primary message | Who they win with | Who they lose with | Pricing model |
|-----------|----------------|----------------|------------------|--------------------|--------------|
| {name} | {leader/challenger/niche} | {their tagline/pitch} | {segment} | {segment} | {$/month, seats, etc} |

Ask the user for competitor names, or infer from context if they've shared product information.

## Step 2 — Feature comparison (what matters, not everything)

Identify the 8-10 features that BUYERS actually decide on (not marketing checkboxes):

| Capability | Our product | Comp A | Comp B | Comp C |
|-----------|-------------|--------|--------|--------|
| {feature} | ✅ Leader / ✓ Present / ○ Partial / ✗ Absent | … | … | … |

**Important**: Mark capabilities where competitors over-invest (complex, expensive) vs where they under-invest (simple, fast, cheap). The gap between their investment and buyer need is a positioning seam.

## Step 3 — Identify positioning seams

A positioning seam is a place where:
- A competitor's strength is actually a weakness for a specific segment
- An entire segment is being ignored or poorly served
- Buyers are paying for features they don't need or use
- A category belief exists that could be challenged

For each seam found:

```
SEAM: {describe the gap}
EVIDENCE: {why this is real — customer quotes, reviews, market data}
SEGMENT THAT BENEFITS: {who would choose you if you owned this seam}
COUNTER-POSITION: {what you'd say to own this space}
```

## Step 4 — Attack vs avoid map

| Competitor | Where to attack (their weakness) | Where to avoid (their strength) |
|-----------|----------------------------------|--------------------------------|
| {name} | {specific, e.g. "SMB segment where their enterprise pricing is prohibitive"} | {specific, e.g. "large enterprise deals requiring procurement process"} |

## Step 5 — Counter-positioning statement

For each primary competitor, write a one-sentence counter-position:

> "Unlike [Competitor], [Your product] [does X differently] because [reason that matters to buyers] — which means [outcome for customer]."

The goal is not to trash competitors — it's to make their strength into a liability for a specific segment.

## Step 6 — Competitive battle cards (sales-ready)

For each top competitor, a one-page battle card:

```
COMPETING AGAINST: {competitor name}

WHEN THEY COME UP: {the situations where buyers mention this competitor}

THEIR STRENGTHS (acknowledge honestly):
  - {strength 1}
  - {strength 2}

OUR ADVANTAGES FOR THIS BUYER:
  - {advantage 1 — specific and evidence-backed}
  - {advantage 2}

LANDMINES TO PLANT (questions that expose their weaknesses):
  - "Have you asked them about {specific weak point}?"
  - "How do they handle {edge case they handle poorly}?"

PROOF POINTS:
  - {customer name} switched from {competitor} because {reason}
  - {metric}: we outperform {competitor} by {amount} on {dimension}

TRAP: Never lead with price unless you're the cheapest option.
```

## Output

1. **Competitive landscape table**
2. **Feature comparison matrix**
3. **Top 3 positioning seams** (with evidence)
4. **Attack/avoid map** per competitor
5. **Counter-positioning statements** (one per competitor)
6. **Battle cards** for top 2-3 competitors
