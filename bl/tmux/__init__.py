"""
bl/tmux — Unified tmux dispatch layer for BrickLayer agents.

When $TMUX is set, agents spawn in visible tmux panes with real-time
stderr. When not in tmux, falls back to subprocess behavior.
"""

from bl.tmux.core import AgentResult as AgentResult
from bl.tmux.core import SpawnResult as SpawnResult
from bl.tmux.core import spawn_agent as spawn_agent
from bl.tmux.core import wait_for_agent as wait_for_agent
from bl.tmux.helpers import MODEL_MAP as MODEL_MAP
from bl.tmux.helpers import build_env as build_env
from bl.tmux.helpers import in_tmux as in_tmux
from bl.tmux.helpers import resolve_model as resolve_model
from bl.tmux.pane import cleanup_panes as cleanup_panes
from bl.tmux.wave import collect_wave as collect_wave
from bl.tmux.wave import spawn_wave as spawn_wave
