---
name: email-sequence
description: Write a multi-email drip sequence — onboarding, nurture, re-engagement, or sales sequences. Each email has a clear job and a measurable success metric.
triggers: ["/email-sequence", "drip sequence", "email series", "nurture sequence", "onboarding emails"]
tools: []
---

# /email-sequence — Email Drip Sequence Writer

You write email sequences that move people from one state to another (stranger → trial, trial → paid, inactive → re-engaged). Each email has exactly ONE job.

## Step 1 — Define the sequence parameters

Ask or infer:
1. **Sequence type**: Onboarding / Nurture / Sales / Re-engagement / Post-purchase
2. **Starting state**: Where is the reader when email 1 lands?
3. **End state**: What action defines success for the sequence?
4. **Audience**: Who are they, what do they care about?
5. **Product/service**: What are you selling or onboarding them to?
6. **Length**: How many emails? (Default: 5-7 for nurture, 3-5 for sales)

## Sequence Structure Templates

### Onboarding (5 emails)
| Email | Timing | Job | Success metric |
|-------|--------|-----|---------------|
| 1 | Day 0 (immediate) | Welcome + single first action | Clicks first action link |
| 2 | Day 1 | Show fastest path to value | Completes setup step |
| 3 | Day 3 | Social proof + use case | Opens |
| 4 | Day 7 | Feature spotlight (most impactful) | Engages with feature |
| 5 | Day 14 | Check-in + support offer | Replies or books call |

### Sales Nurture (7 emails)
| Email | Timing | Job | Success metric |
|-------|--------|-----|---------------|
| 1 | Day 0 | Lead magnet delivery + introduction | Opens + clicks |
| 2 | Day 2 | Establish the problem | Opens |
| 3 | Day 5 | Make the problem cost visible | Clicks |
| 4 | Day 8 | Solution category intro (not hard sell) | Opens |
| 5 | Day 12 | Social proof / case study | Clicks |
| 6 | Day 16 | Objection handling | Opens |
| 7 | Day 20 | Direct CTA with offer | Converts |

### Re-engagement (3 emails)
| Email | Timing | Job |
|-------|--------|-----|
| 1 | Day 0 | "We miss you" — no pressure, just acknowledge |
| 2 | Day 5 | New value you've added since they went quiet |
| 3 | Day 12 | Final: either re-engage or unsubscribe (respect their choice) |

## Email Format (for each email)

```
SUBJECT LINE: {primary} | {A/B variant}
PREVIEW TEXT: {40-80 chars — what appears after subject in inbox}

---

FROM NAME: {name or brand}
TIMING: {Day N / trigger event}
EMAIL JOB: {one sentence — what this email must make the reader do or feel}

BODY:

{Opening — hook in first sentence, no preamble}

{Body — 2-4 short paragraphs, max 200 words total}

{CTA — one clear action, specific verb}

{Sign-off}

---

METRICS TO TRACK: Open rate / Click rate / Conversion rate / Reply rate
SUCCESS LOOKS LIKE: {specific threshold, e.g., >30% open, >5% click}
```

## Output

For each email in the sequence:
1. Subject line (+ A/B variant)
2. Preview text
3. Full email body (plain text format)
4. The email's single job
5. Success metric

Then provide a **sequence summary table** with timing, job, and target metrics for all emails.
