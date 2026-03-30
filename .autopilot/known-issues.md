# Known Issues — Phase 14

From Recall search (no critical blockers found):

- No pytest/Windows path issues found for this stack
- masonry-tool-failure.js OMC refs already fixed this session (not relevant)
- DISABLE_OMC=1 in CLAUDE.md still present — low priority, not blocking

## Platform notes
- Windows 11, forward slashes in paths, /dev/null not NUL
- Test runner: python -m pytest tests/ -q
- 264 existing passing tests — must not regress
