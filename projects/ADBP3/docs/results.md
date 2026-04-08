 Here is the full campaign report.

  ---
  RAISE System — 15-Year Campaign Analysis

  What Was Tested

  10 scenario sweeps across every meaningful variable — D9 (escrow interest), D12 (credit obligation), D14 (gate start), D15 (logistic growth), D7/D8 (allocation
  split), D16 (admin wallet interest), and capacity scaling — with a "pause" at month 180 (year 15) modeled as: minting stops, admin fees stop, escrow compounds at D9
  until L reaches 100%.

  ---
  Finding 1 — Employee Count Is Capacity-Constrained, Not Rate-Constrained

  The single biggest surprise: adjusting D14 (gate start) and D15 (logistic growth rate) barely moves the 15-year employee total. D14 ranging from 1 to 60 produces the
   exact same 542,916 employees. D15 from 0.5 to 2.0 moves the number by only ~11,000. Why? The capacity growth schedule (your N column, Year 1–25 table) is the actual
   ceiling. Once enrollment hits the capacity wall, the logistic and gate become irrelevant. You could set D15=0.05 and lose ~157k employees, but above D15=0.30 you're
   already within 97% of maximum.

  Implication: You cannot meaningfully increase employees beyond ~543k in 15 years without changing the capacity growth schedule itself.

  ---
  Finding 2 — Realistic 15-Year Employee Range

  ┌──────────────────────────┬─────────────────────┐
  │      Configuration       │ Employees @ Year 15 │
  ├──────────────────────────┼─────────────────────┤
  │ D15 = 0.05 (slow growth) │ 385,931             │
  ├──────────────────────────┼─────────────────────┤
  │ D15 = 0.30 (moderate)    │ 526,418             │
  ├──────────────────────────┼─────────────────────┤
  │ Baseline V4              │ 542,916             │
  ├──────────────────────────┼─────────────────────┤
  │ D15 = 2.0 (hyper)        │ 547,203             │
  ├──────────────────────────┼─────────────────────┤
  │ 10× capacity schedule    │ ~3.3–4.1M           │
  └──────────────────────────┴─────────────────────┘

  Realistic number with current capacity schedule: ~540,000–545,000 employees over 15 years. This is robust regardless of how aggressively you tune the gate or growth
  rate.

  To reach millions of employees, the capacity growth schedule (G6:G30) must be scaled up proportionally.

  ---
  Finding 3 — L Health Is Stable and Growing Throughout

  L never dips below 52.5% in any baseline scenario and trends upward the entire 15 years — from 52.5% at month 1 to 54.2% at month 180. The system is structurally
  healthy. The escrow wallet grows from $129M (Year 1) to $112.5B (Year 15). Admin wallet peaks near $1.4B at Year 7–8 then stabilizes around $1B. Escrow never needs
  to sweep for admin fees in the baseline.

  ---
  Finding 4 — The Escrow Interest Rate (D9) Is the Most Powerful Single Lever

  D9 does not affect employee count at all, but it dominates both L health and time-to-shutdown:

  ┌───────────────┬─────────────┬────────────────────────────┐
  │      D9       │ L @ Year 15 │ Time to L=100% after pause │
  ├───────────────┼─────────────┼────────────────────────────┤
  │ 2%            │ 50.9%       │ 33.9 years                 │
  ├───────────────┼─────────────┼────────────────────────────┤
  │ 4%            │ 52.1%       │ 16.3 years                 │
  ├───────────────┼─────────────┼────────────────────────────┤
  │ 5% (baseline) │ 54.2%       │ 12.3 years                 │
  ├───────────────┼─────────────┼────────────────────────────┤
  │ 6%            │ 56.8%       │ 9.5 years                  │
  ├───────────────┼─────────────┼────────────────────────────┤
  │ 7%            │ 59.7%       │ 7.4 years                  │
  ├───────────────┼─────────────┼────────────────────────────┤
  │ 8%            │ 62.9%       │ 5.8 years                  │
  ├───────────────┼─────────────┼────────────────────────────┤
  │ 10%           │ 70.2%       │ 3.6 years                  │
  └───────────────┴─────────────┴────────────────────────────┘

  Moving from 5% to 7% cuts the shutdown runway from 12.3 years to 7.4 years with zero trade-offs.

  ---
  Finding 5 — Credit Obligation (D12) Is the Other Major Lever

  D12 is the buying-power multiplier. A lower D12 means less obligation per credit relative to escrow — L is higher throughout:

  ┌──────────────────┬─────────────┬───────┬─────────────────┐
  │       D12        │ L @ Year 15 │ MinL  │ TTF after pause │
  ├──────────────────┼─────────────┼───────┼─────────────────┤
  │ $1.40            │ 77.5%       │ 75.0% │ 5.2 years       │
  ├──────────────────┼─────────────┼───────┼─────────────────┤
  │ $1.50            │ 72.3%       │ 70.0% │ 6.5 years       │
  ├──────────────────┼─────────────┼───────┼─────────────────┤
  │ $1.60            │ 67.8%       │ 65.6% │ 7.8 years       │
  ├──────────────────┼─────────────┼───────┼─────────────────┤
  │ $2.00 (baseline) │ 54.2%       │ 52.5% │ 12.3 years      │
  └──────────────────┴─────────────┴───────┴─────────────────┘

  D12 = $1.50 puts the system in the 70%+ L range from day one and achieves shutdown in under 7 years.

  ---
  Finding 6 — Admin Wallet Interest Rate (D16) Has Minor Impact

  D16 ranging from 0% to 10% only moves L by ~0.6% and TTF by 3 months. The admin wallet is already well-funded by the $0.30/credit pre-allocation — it barely needs
  interest support at the current scale.

  ---
  Finding 7 — Optimal Shutdown Configuration

  Combining the two key levers (D9 and D12) produces dramatic improvements:

  ┌────────────────────┬───────────┬───────────┬─────────────────┐
  │      Scenario      │ Employees │ L @ pause │ TTF after pause │
  ├────────────────────┼───────────┼───────────┼─────────────────┤
  │ Baseline V4        │ 542,916   │ 54.2%     │ 12.3 years      │
  ├────────────────────┼───────────┼───────────┼─────────────────┤
  │ D9 = 7% only       │ 542,916   │ 59.7%     │ 7.4 years       │
  ├────────────────────┼───────────┼───────────┼─────────────────┤
  │ D12 = 1.5, D9 = 7% │ 542,916   │ 79.5%     │ 3.3 years       │
  ├────────────────────┼───────────┼───────────┼─────────────────┤
  │ D12 = 1.5, D9 = 8% │ 542,916   │ 83.8%     │ 2.2 years       │
  └────────────────────┴───────────┴───────────┴─────────────────┘

  The D12=1.5, D9=7% configuration is the standout: same employee count, L stays above 70% the entire 15 years, and the system can fully wind down in 3.3 years after
  pause. It's also more conservative than using 8% escrow interest.

  Note: Changing D12 from $2.00 to $1.50 means employee buying power per credit is $1.50 instead of $2.00 — verify this is acceptable from a product standpoint.

  ---
  Finding 8 — Post-Pause L Growth (Year-by-Year After Month 180)

  With D9=7%, D12=1.5 (recommended):
  - Month 192 (Year 1 post-pause): L = 80.0%
  - Month 204 (Year 2): L = 85.7%
  - Month 216 (Year 3): L = 91.9%
  - Month 228 (Year 4): L = 98.6%
  - Month ~220: L crosses 100% — full wind-down complete

  ---
  Recommended Settings

  ┌─────────────────────────┬───────────────────────────┬──────────────────────────────────────────────┐
  │                         │         Baseline          │                 Recommended                  │
  ├─────────────────────────┼───────────────────────────┼──────────────────────────────────────────────┤
  │ D9 (Escrow Interest)    │ 5%                        │ 7%                                           │
  ├─────────────────────────┼───────────────────────────┼──────────────────────────────────────────────┤
  │ D12 (Credit Obligation) │ $2.00                     │ $1.50–$1.70                                  │
  ├─────────────────────────┼───────────────────────────┼──────────────────────────────────────────────┤
  │ D14 (Gate Start)        │ 10                        │ Keep at 10 (no meaningful effect)            │
  ├─────────────────────────┼───────────────────────────┼──────────────────────────────────────────────┤
  │ D15 (Logistic Rate)     │ 1.0                       │ Keep at 1.0 (diminishing returns above this) │
  ├─────────────────────────┼───────────────────────────┼──────────────────────────────────────────────┤
  │ D16 (Admin Interest)    │ 5%                        │ Keep at 5% (marginal impact)                 │
  ├─────────────────────────┼───────────────────────────┼──────────────────────────────────────────────┤
  │ Result                  │ 542k emp, 12.3yr shutdown │ 542k emp, 3.3–4.2yr shutdown                 │
  └─────────────────────────┴───────────────────────────┴──────────────────────────────────────────────┘