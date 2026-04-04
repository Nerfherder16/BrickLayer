"""Typed payload schemas for Masonry routing and agent communication."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentRegistryEntry:
    name: str
    file: str = ""
    description: str = ""
    capabilities: list[str] = field(default_factory=list)
    modes: list[str] = field(default_factory=list)
    tier: str = "standard"
    routing_keywords: list[str] = field(default_factory=list)
    model: Optional[str] = None


@dataclass
class RoutingDecision:
    target_agent: str
    layer: str
    confidence: float
    reason: str
