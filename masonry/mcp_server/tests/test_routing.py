"""Tests for masonry/mcp_server/tools/routing.py."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from masonry.mcp_server.tools.routing import (
    _tool_masonry_route,
    _tool_masonry_registry_list,
)


class TestMasonryRoute:
    def test_js_engine_result_returned(self):
        js_payload = {"agent": "rough-in", "confidence": 1.0, "layer": "L1b", "note": "build"}
        with patch("masonry.mcp_server.tools.routing._call_js_engine", return_value=js_payload):
            result = _tool_masonry_route({"request_text": "/build the auth endpoint"})
        assert result == js_payload

    def test_missing_request_text_returns_error(self):
        result = _tool_masonry_route({})
        assert "error" in result

    def test_python_fallback_on_js_failure(self):
        from masonry.src.schemas.payloads import RoutingDecision
        decision = RoutingDecision(target_agent="mortar", layer="L1", confidence=0.9, reason="keyword match")
        with patch("masonry.mcp_server.tools.routing._call_js_engine", return_value=None):
            with patch("masonry.src.routing.router.route", return_value=decision):
                result = _tool_masonry_route({"request_text": "test"})
        assert result["target_agent"] == "mortar"
        assert result["layer"] == "L1"

    def test_full_fallback_on_import_error(self):
        with patch("masonry.mcp_server.tools.routing._call_js_engine", return_value=None):
            with patch("masonry.mcp_server.tools.routing._python_route_fallback",
                       return_value={"target_agent": "user", "layer": "fallback", "confidence": 0.0, "error": "import failed", "reason": "x", "fallback_agents": [], "fallback_reason": "multi_failure"}):
                result = _tool_masonry_route({"request_text": "test"})
        assert result["layer"] == "fallback"


class TestMasonryRegistryList:
    def test_js_engine_result_returned(self):
        js_payload = [{"id": "rough-in", "tier": "trusted"}]
        with patch("masonry.mcp_server.tools.routing._call_js_engine", return_value=js_payload):
            result = _tool_masonry_registry_list({})
        assert result == js_payload

    def test_python_fallback_on_js_failure(self, tmp_path):
        import yaml
        registry = {"version": 1, "agents": [{"name": "rough-in", "tier": "trusted"}]}
        reg_path = tmp_path / "agent_registry.yml"
        reg_path.write_text(yaml.dump(registry))
        with patch("masonry.mcp_server.tools.routing._call_js_engine", return_value=None):
            result = _tool_masonry_registry_list({"registry_path": str(reg_path)})
        assert "agents" in result
        assert "count" in result
        assert result["count"] == 1

    def test_error_returns_empty_agents(self, tmp_path):
        with patch("masonry.mcp_server.tools.routing._call_js_engine", return_value=None):
            with patch("masonry.src.schemas.registry_loader.load_registry", side_effect=Exception("no registry")):
                result = _tool_masonry_registry_list({"registry_path": str(tmp_path / "missing.yml")})
        assert result["agents"] == []
        assert "error" in result
