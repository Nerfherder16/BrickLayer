# Refactor Candidates

Generated: 2026-03-28T02:08:56.178Z
Project: Bricklayer2.0
Files scanned: 323

## Summary

| Check | Count |
|-------|-------|
| God files (>500 lines) | 41 |
| Deep nesting (>5 levels) | 15 |
| Duplicate code blocks | 20 |

## God Files (41)

These files exceed 500 lines and should be split into focused modules.

- `recall-arch-frontier\simulate.py` — **4154 lines**
- `simulate.py` — **2564 lines**
- `recall\simulate.py` — **2290 lines**
- `masonry\bin\masonry-mcp.js` — **1910 lines**
- `bl\nl_entry.py` — **1241 lines**
- `adbp\simulate.py` — **1061 lines**
- `masonry\mcp_server\server.py` — **955 lines**
- `projects\ADBP3\operational_sims.py` — **855 lines**
- `bl\runners\contract.py` — **828 lines**
- `projects\ADBP\simulate.py` — **786 lines**
- `projects\ADBP3\advanced_sims.py` — **784 lines**
- `adbp\analyze.py` — **752 lines**
- `tests\test_onboard_agent.py` — **750 lines**
- `bl\crucible.py` — **725 lines**
- `tests\test_agent_scripts.py` — **722 lines**
- `onboard.py` — **678 lines**
- `bl\runners\benchmark.py` — **676 lines**
- `bl\runners\document.py` — **657 lines**
- `bl\runners\simulate.py` — **657 lines**
- `bl\runners\performance.py` — **654 lines**
- `bl\training_export.py` — **634 lines**
- `projects\bricklayer\analyze.py` — **610 lines**
- `bl-audit\analyze.py` — **608 lines**
- `projects\adbp2\analyze.py` — **608 lines**
- `projects\ADBP3\analyze.py` — **608 lines**
- `projects\bl2\analyze.py` — **608 lines**
- `template\analyze.py` — **608 lines**
- `projects\adbp2\simulate.py` — **606 lines**
- `tests\test_run_vigil.py` — **591 lines**
- `docs\training_export.py` — **584 lines**
- `tests\test_score_findings.py` — **583 lines**
- `masonry\scripts\onboard_agent.py` — **575 lines**
- `bl\findings.py` — **573 lines**
- `adbp\simulate_v4.py` — **560 lines**
- `bl\runners\agent.py` — **549 lines**
- `bl\ci\run_campaign.py` — **545 lines**
- `projects\ADBP3\vendor_sims.py` — **536 lines**
- `tests\test_snapshot_agent.py` — **529 lines**
- `projects\ADBP3\fee_optimization.py` — **527 lines**
- `masonry\scripts\optimize_with_claude.py` — **510 lines**
- `projects\ADBP3\monte_carlo.py` — **510 lines**

## Duplicate Code Blocks (20)

8+ line blocks with identical structure found across multiple files.

- **2 files**: `adbp\analyze.py:11`, `bl-audit\analyze.py:13`
  Pattern: `"""||import argparse|import csv|import re|import sys|from da...`
- **2 files**: `adbp\analyze.py:12`, `bl-audit\analyze.py:14`
  Pattern: `|import argparse|import csv|import re|import sys|from dateti...`
- **2 files**: `adbp\analyze.py:13`, `bl-audit\analyze.py:15`
  Pattern: `import argparse|import csv|import re|import sys|from datetim...`
- **2 files**: `adbp\analyze.py:14`, `bl-audit\analyze.py:16`
  Pattern: `import csv|import re|import sys|from datetime import datetim...`
- **2 files**: `adbp\analyze.py:15`, `bl-audit\analyze.py:17`
  Pattern: `import re|import sys|from datetime import datetime|from path...`
- **2 files**: `adbp\analyze.py:16`, `bl-audit\analyze.py:18`
  Pattern: `import sys|from datetime import datetime|from pathlib import...`
- **2 files**: `adbp\analyze.py:17`, `bl-audit\analyze.py:19`
  Pattern: `from datetime import datetime|from pathlib import Path||from...`
- **2 files**: `adbp\analyze.py:18`, `bl-audit\analyze.py:20`
  Pattern: `from pathlib import Path||from reportlab.lib import colors|f...`
- **2 files**: `adbp\analyze.py:19`, `bl-audit\analyze.py:21`
  Pattern: `|from reportlab.lib import colors|from reportlab.lib.enums i...`
- **2 files**: `adbp\analyze.py:20`, `bl-audit\analyze.py:22`
  Pattern: `from reportlab.lib import colors|from reportlab.lib.enums im...`
- **2 files**: `adbp\analyze.py:21`, `bl-audit\analyze.py:23`
  Pattern: `from reportlab.lib.enums import TA_CENTER|from reportlab.lib...`
- **2 files**: `adbp\analyze.py:22`, `bl-audit\analyze.py:24`
  Pattern: `from reportlab.lib.pagesizes import letter|from reportlab.li...`
- **2 files**: `adbp\analyze.py:23`, `bl-audit\analyze.py:25`
  Pattern: `from reportlab.lib.styles import ParagraphStyle|from reportl...`
- **2 files**: `adbp\analyze.py:24`, `bl-audit\analyze.py:26`
  Pattern: `from reportlab.lib.units import inch|from reportlab.platypus...`
- **2 files**: `adbp\analyze.py:25`, `bl-audit\analyze.py:27`
  Pattern: `from reportlab.platypus import (|HRFlowable,|PageBreak,|Para...`
- **2 files**: `adbp\analyze.py:26`, `bl-audit\analyze.py:28`
  Pattern: `HRFlowable,|PageBreak,|Paragraph,|SimpleDocTemplate,|Spacer,...`
- **2 files**: `adbp\analyze.py:27`, `bl-audit\analyze.py:29`
  Pattern: `PageBreak,|Paragraph,|SimpleDocTemplate,|Spacer,|Table,|Tabl...`
- **2 files**: `adbp\analyze.py:42`, `bl-audit\analyze.py:62`
  Pattern: `RED = colors.HexColor("#CNB")|ORANGE = colors.HexColor("#ENE...`
- **2 files**: `adbp\analyze.py:43`, `bl-audit\analyze.py:63`
  Pattern: `ORANGE = colors.HexColor("#ENEN")|GREEN = colors.HexColor("#...`
- **2 files**: `adbp\analyze.py:44`, `bl-audit\analyze.py:64`
  Pattern: `GREEN = colors.HexColor("#NAEN")|BLUE = colors.HexColor("#NB...`

## Deep Nesting (15)

Nesting depth > 5 levels — consider extracting inner logic.

- `masonry\bin\masonry-mcp.js:1849` — depth 6
- `masonry\src\daemon\worker-deepdive.js:99` — depth 6
- `masonry\src\daemon\worker-document.js:123` — depth 6
- `masonry\src\hooks\masonry-context-safety.js:58` — depth 6
- `masonry\src\hooks\masonry-context-safety.js:91` — depth 6
- `masonry\src\hooks\masonry-context-safety.js:108` — depth 6
- `masonry\src\hooks\masonry-observe.js:254` — depth 6
- `masonry\src\hooks\masonry-pre-compact.js:229` — depth 6
- `masonry\src\hooks\masonry-register.js:136` — depth 6
- `masonry\src\hooks\masonry-register.js:185` — depth 6
- `masonry\src\hooks\masonry-session-end.js:177` — depth 6
- `masonry\src\hooks\masonry-session-end.js:191` — depth 6
- `masonry\src\hooks\masonry-session-start.js:73` — depth 6
- `masonry\src\hooks\masonry-session-start.js:146` — depth 6
- `masonry\src\hooks\masonry-session-start.js:162` — depth 6

## Actions

Spawn the `refactorer` agent: `Act as the refactorer agent in ~/.claude/agents/refactorer.md.`
Or use `/fix` targeting specific files listed above.