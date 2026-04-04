1. How does the loop know to ask the retrospective, and should we improve the prompt?

  Right now the trigger is mechanical: synthesize() in bl/synthesizer.py calls _run_retrospective(project_dir) as its last step. That function checks if retrospective.md agent
   exists in .claude/agents/, then fires a claude -p subprocess with a fixed prompt:

  ▎ "Act as the retrospective agent. Project directory: {dir}. Score this campaign's execution quality and write retrospective.md."

  That prompt is thin. It tells the agent what to do but not what to look at or what we care about most. The agent then has to go discover all the campaign artifacts on its   
  own.

  Better prompt would front-load the most important context and ask a sharper question:

  Act as the retrospective agent in {agent_file}.

  Project: {project_name} (from project-brief.md)
  Directory: {project_dir}
  Campaign stats: {N} questions total, {done} DONE, {inconclusive} INCONCLUSIVE
  Wave count: {wave}

  Read findings/*.md, results.tsv, synthesis.md, and pre-flight.md.
  Score execution quality across Tool Friction, Sweep Efficiency, Finding Quality,
  and Question Coverage. Focus especially on: which questions consumed the most
  simulation runs? Which findings had low confidence? Were any null-gate questions
  run that pre-flight would have caught?

  Write retrospective.md and output the JSON block for Recall storage.

  The key additions: pre-loading the question counts (so the agent doesn't have to parse questions.md to get denominator), naming specific friction signals to look for, and   
  connecting pre-flight null gates to question slot waste. I'll fold this into the C2 task prompt below.

  We should also consider: the synthesizer currently scores the findings quality. The retrospective scores the process quality. They're complementary — the synthesis tells you
   what was learned, the retrospective tells you how efficiently you learned it. A future improvement would be to pass synthesis conclusions into the retrospective prompt so  
  it can correlate "we found X" with "it took Y question slots to find it." That's Phase 8 territory.

  ---
  2. BrickLayer in Rust or Go — would it perform better?

  Short answer: not for the bottlenecks that actually matter.

  ┌─────────────────────────────────────┬────────────────┬─────────────────────────────────────────────────────────────────┐
  │             Bottleneck              │ % of wall time │                     Addressable by Rust/Go?                     │
  ├─────────────────────────────────────┼────────────────┼─────────────────────────────────────────────────────────────────┤
  │ Claude API response time            │ ~70–80%        │ No — network I/O, not compute                                   │
  ├─────────────────────────────────────┼────────────────┼─────────────────────────────────────────────────────────────────┤
  │ Subprocess cold-start (210 in ADBP) │ ~15%           │ Partially — but Phase 7 persistent server eliminates most of it │
  ├─────────────────────────────────────┼────────────────┼─────────────────────────────────────────────────────────────────┤
  │ File I/O (findings, results.tsv)    │ ~3%            │ Yes, but already fast enough                                    │
  ├─────────────────────────────────────┼────────────────┼─────────────────────────────────────────────────────────────────┤
  │ Python simulation compute           │ ~2%            │ Yes, significant speedup possible                               │
  ├─────────────────────────────────────┼────────────────┼─────────────────────────────────────────────────────────────────┤
  │ JSON parsing between tools          │ ~1%            │ Yes, but negligible                                             │
  └─────────────────────────────────────┴────────────────┴─────────────────────────────────────────────────────────────────┘

  Rewriting the BL framework in Rust or Go would buy you maybe 5% real wall-clock improvement because 75% of the time is waiting for Claude. The simulation itself is fast     
  Python — a 36-month model runs in milliseconds.

  Where Rust/Go would actually help: If BrickLayer ever ran simulations that were computationally expensive — Monte Carlo with 10K samples, agent-based models, stochastic     
  processes — then the Python simulation would become the bottleneck and Rust could give 50–100x speedup on that specific piece. The bl/sweep.py harness is designed for       
  exactly this pattern: if someone's simulate.py becomes compute-heavy, the sweep still abstracts the loop.

  The real performance win is in the architecture, not the language. Phase 7's persistent sim server + sweep harness + Wave 0 pre-flight eliminates more latency than a Rust   
  rewrite would, by reducing total questions needed and eliminating subprocess cold-starts.

  Go would be interesting for the orchestration layer (mortar, the question loop, findings writes) because Go's concurrency model fits the "manage N parallel agent workers"   
  pattern well. But it would mean agents couldn't be Python classes anymore — they'd be subprocess-spawned, which is already how they work. Not worth the port cost.

  The strongest argument for Rust: if BrickLayer ever became a shared service (multiple users, concurrent campaigns) instead of a local tool. Rust's memory safety +
  performance under load would matter then. As a single-user local tool on a dev machine, it's irrelevant.

  ---
  Now launching B and C:

● Running 2 agents… (ctrl+o to expand)
   ├─ Stream B: MCP tools + mortar Wave 0 patch · 16 tool uses · 70.2k tokens
   │  ⎿  Read: template\.claude\agents\mortar.md
   └─ Stream C: retrospective agent + synthesizer integration · 12 tool uses · 53.3k tokens
      ⎿  Done

───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 Edit file
 template\.claude\agents\mortar.md