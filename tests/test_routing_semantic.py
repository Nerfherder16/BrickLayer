"""Tests for masonry/src/routing/semantic.py — Layer 2 semantic/embedding routing."""

from __future__ import annotations

import math
from typing import Any
from unittest.mock import MagicMock, patch


from masonry.src.routing.semantic import route_semantic, _cosine_similarity
from masonry.src.schemas import AgentRegistryEntry, RoutingDecision


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────


def make_agent(name: str, description: str, capabilities: list[str]) -> AgentRegistryEntry:
    return AgentRegistryEntry(
        name=name,
        file=f"agents/{name}.md",
        description=description,
        capabilities=capabilities,
        modes=["research"],
        tier="draft",
    )


def fake_embed_response(embedding: list[float]) -> dict[str, Any]:
    return {"embeddings": [embedding]}


# ──────────────────────────────────────────────────────────────────────────
# Cosine similarity unit tests
# ──────────────────────────────────────────────────────────────────────────


class TestCosineSimilarity:
    def test_identical_vectors(self):
        v = [1.0, 2.0, 3.0]
        assert abs(_cosine_similarity(v, v) - 1.0) < 1e-6

    def test_orthogonal_vectors(self):
        v1 = [1.0, 0.0, 0.0]
        v2 = [0.0, 1.0, 0.0]
        assert abs(_cosine_similarity(v1, v2) - 0.0) < 1e-6

    def test_opposite_vectors(self):
        v1 = [1.0, 0.0]
        v2 = [-1.0, 0.0]
        assert abs(_cosine_similarity(v1, v2) - (-1.0)) < 1e-6

    def test_known_similarity(self):
        v1 = [1.0, 1.0]
        v2 = [1.0, 0.0]
        expected = 1 / math.sqrt(2)
        assert abs(_cosine_similarity(v1, v2) - expected) < 1e-6

    def test_zero_vector_returns_zero(self):
        """Zero vector should not raise, return 0."""
        v1 = [0.0, 0.0]
        v2 = [1.0, 0.0]
        result = _cosine_similarity(v1, v2)
        assert result == 0.0


# ──────────────────────────────────────────────────────────────────────────
# route_semantic — main routing function
# ──────────────────────────────────────────────────────────────────────────


class TestRouteSemantic:
    def _make_registry(self):
        return [
            make_agent(
                "agent-a",
                "Handles simulation and parameter sweep",
                ["simulation", "sweep"],
            ),
            make_agent(
                "agent-b",
                "Handles legal research and compliance",
                ["legal", "compliance"],
            ),
        ]

    def _make_mock_post(self, request_emb: list[float], agent_embs: list[list[float]]):
        """Create a mock httpx.Client().post() that returns embeddings in sequence."""
        responses = [fake_embed_response(request_emb)] + [
            fake_embed_response(e) for e in agent_embs
        ]
        mock_response = MagicMock()

        call_count = [0]

        def side_effect(*args, **kwargs):
            r = MagicMock()
            r.raise_for_status = MagicMock()
            r.json.return_value = responses[call_count[0]]
            call_count[0] += 1
            return r

        return side_effect

    def test_returns_agent_with_highest_similarity(self):
        """Request closer to agent-a → returns agent-a."""
        registry = self._make_registry()

        # agent-a description embedding is [1, 0]
        # agent-b description embedding is [0, 1]
        # request embedding is [0.9, 0.1] → closer to agent-a
        agent_a_emb = [1.0, 0.0]
        agent_b_emb = [0.0, 1.0]
        request_emb = [0.9, 0.1]

        with patch("masonry.src.routing.semantic._embedding_cache", {}):
            with patch("masonry.src.routing.semantic.httpx") as mock_httpx:
                mock_client = MagicMock()
                mock_httpx.Client.return_value.__enter__ = MagicMock(return_value=mock_client)
                mock_httpx.Client.return_value.__exit__ = MagicMock(return_value=False)
                mock_httpx.TimeoutException = Exception
                mock_httpx.HTTPError = Exception

                responses = iter([
                    fake_embed_response(request_emb),
                    fake_embed_response(agent_a_emb),
                    fake_embed_response(agent_b_emb),
                ])

                def post_side_effect(*args, **kwargs):
                    r = MagicMock()
                    r.raise_for_status = MagicMock()
                    r.json.return_value = next(responses)
                    return r

                mock_client.post.side_effect = post_side_effect

                result = route_semantic(
                    "simulate parameter sweep",
                    registry,
                    threshold=0.5,
                )

        assert result is not None
        assert result.target_agent == "agent-a"
        assert result.layer == "semantic"
        assert result.confidence >= 0.5

    def test_below_threshold_returns_none(self):
        """All similarities below threshold → None."""
        registry = self._make_registry()

        # Use orthogonal embeddings → similarity=0, well below threshold=0.75
        request_emb = [1.0, 0.0]
        agent_a_emb = [0.0, 1.0]
        agent_b_emb = [0.0, 0.0]  # zero vector

        with patch("masonry.src.routing.semantic._embedding_cache", {}):
            with patch("masonry.src.routing.semantic.httpx") as mock_httpx:
                mock_client = MagicMock()
                mock_httpx.Client.return_value.__enter__ = MagicMock(return_value=mock_client)
                mock_httpx.Client.return_value.__exit__ = MagicMock(return_value=False)
                mock_httpx.TimeoutException = Exception
                mock_httpx.HTTPError = Exception

                responses = iter([
                    fake_embed_response(request_emb),
                    fake_embed_response(agent_a_emb),
                    fake_embed_response(agent_b_emb),
                ])

                def post_side_effect(*args, **kwargs):
                    r = MagicMock()
                    r.raise_for_status = MagicMock()
                    r.json.return_value = next(responses)
                    return r

                mock_client.post.side_effect = post_side_effect

                result = route_semantic(
                    "unrelated text",
                    registry,
                    threshold=0.75,
                )

        assert result is None

    def test_ollama_connection_error_returns_none(self):
        """If Ollama is unreachable, return None without raising."""
        registry = self._make_registry()

        with patch("masonry.src.routing.semantic._embedding_cache", {}):
            with patch("masonry.src.routing.semantic.httpx") as mock_httpx:
                mock_client = MagicMock()
                mock_httpx.Client.return_value.__enter__ = MagicMock(return_value=mock_client)
                mock_httpx.Client.return_value.__exit__ = MagicMock(return_value=False)
                mock_httpx.TimeoutException = ConnectionError
                mock_httpx.HTTPError = ConnectionError

                mock_client.post.side_effect = ConnectionError("Connection refused")

                result = route_semantic("simulate parameter sweep", registry)

        assert result is None

    def test_confidence_equals_cosine_similarity(self):
        """The confidence field should equal the best cosine similarity score."""
        registry = [make_agent("only-agent", "simulation", ["sim"])]

        # Request embedding identical to agent → similarity=1.0
        emb = [1.0, 0.0, 0.0]

        with patch("masonry.src.routing.semantic._embedding_cache", {}):
            with patch("masonry.src.routing.semantic.httpx") as mock_httpx:
                mock_client = MagicMock()
                mock_httpx.Client.return_value.__enter__ = MagicMock(return_value=mock_client)
                mock_httpx.Client.return_value.__exit__ = MagicMock(return_value=False)
                mock_httpx.TimeoutException = Exception
                mock_httpx.HTTPError = Exception

                responses = iter([
                    fake_embed_response(emb),
                    fake_embed_response(emb),
                ])

                def post_side_effect(*args, **kwargs):
                    r = MagicMock()
                    r.raise_for_status = MagicMock()
                    r.json.return_value = next(responses)
                    return r

                mock_client.post.side_effect = post_side_effect

                result = route_semantic(
                    "simulation task",
                    registry,
                    threshold=0.5,
                )

        assert result is not None
        assert abs(result.confidence - 1.0) < 1e-6

    def test_embedding_cache_used_on_second_call(self):
        """Agent embeddings are cached — second call should not re-fetch them."""
        registry = [make_agent("cached-agent", "simulation", ["sim"])]
        emb = [1.0, 0.0]

        call_log: list[dict] = []

        def post_side_effect(*args, **kwargs):
            call_log.append({"args": args, "kwargs": kwargs})
            r = MagicMock()
            r.raise_for_status = MagicMock()
            r.json.return_value = fake_embed_response(emb)
            return r

        with patch("masonry.src.routing.semantic._embedding_cache", {}):
            with patch("masonry.src.routing.semantic.httpx") as mock_httpx:
                mock_client = MagicMock()
                mock_httpx.Client.return_value.__enter__ = MagicMock(return_value=mock_client)
                mock_httpx.Client.return_value.__exit__ = MagicMock(return_value=False)
                mock_httpx.TimeoutException = Exception
                mock_httpx.HTTPError = Exception
                mock_client.post.side_effect = post_side_effect

                # First call: should make 2 posts (1 request + 1 agent)
                route_semantic("simulation", registry, threshold=0.5)
                first_call_count = len(call_log)

                # Second call: agent embedding should be cached → only 1 post (request)
                route_semantic("simulation", registry, threshold=0.5)
                second_call_count = len(call_log) - first_call_count

        assert first_call_count == 2, f"Expected 2 posts on first call, got {first_call_count}"
        assert second_call_count == 1, f"Expected 1 post on second call (cached), got {second_call_count}"

    def test_result_is_routing_decision(self):
        """Return type is RoutingDecision when match found."""
        registry = [make_agent("test-agent", "research analysis", ["research"])]
        emb = [1.0, 0.0]

        with patch("masonry.src.routing.semantic._embedding_cache", {}):
            with patch("masonry.src.routing.semantic.httpx") as mock_httpx:
                mock_client = MagicMock()
                mock_httpx.Client.return_value.__enter__ = MagicMock(return_value=mock_client)
                mock_httpx.Client.return_value.__exit__ = MagicMock(return_value=False)
                mock_httpx.TimeoutException = Exception
                mock_httpx.HTTPError = Exception

                responses = iter([fake_embed_response(emb), fake_embed_response(emb)])

                def post_side_effect(*args, **kwargs):
                    r = MagicMock()
                    r.raise_for_status = MagicMock()
                    r.json.return_value = next(responses)
                    return r

                mock_client.post.side_effect = post_side_effect

                result = route_semantic("research analysis", registry, threshold=0.5)

        assert isinstance(result, RoutingDecision)
        assert result.layer == "semantic"


# ------------------------------------------------------------------
# Ollama URL env var configuration
# ------------------------------------------------------------------


class TestOllamaUrlConfig:
    def test_ollama_url_reads_from_env_var(self, monkeypatch):
        """OLLAMA_URL env var overrides the default URL."""
        import masonry.src.routing.semantic as sem
        monkeypatch.setenv("OLLAMA_URL", "http://custom-host:11434")

        # Re-import to pick up the env var (or check the module attr directly)
        import importlib
        importlib.reload(sem)

        assert sem._OLLAMA_URL == "http://custom-host:11434"

    def test_ollama_url_default_when_env_not_set(self, monkeypatch):
        """When OLLAMA_URL is not set, uses the default URL."""
        import masonry.src.routing.semantic as sem
        monkeypatch.delenv("OLLAMA_URL", raising=False)

        import importlib
        importlib.reload(sem)

        assert sem._OLLAMA_URL == "http://192.168.50.62:11434"

    def test_route_semantic_uses_ollama_url_parameter(self):
        """route_semantic accepts ollama_url parameter and uses it for requests."""
        import inspect
        from masonry.src.routing.semantic import route_semantic
        sig = inspect.signature(route_semantic)
        assert "ollama_url" in sig.parameters


# ------------------------------------------------------------------
# Corpus built from registry
# ------------------------------------------------------------------


class TestCorpusFromRegistry:
    def test_route_semantic_accepts_registry_list(self):
        """route_semantic accepts a list[AgentRegistryEntry] as registry param."""
        import inspect
        from masonry.src.routing.semantic import route_semantic
        sig = inspect.signature(route_semantic)
        assert "registry" in sig.parameters

    def test_empty_registry_returns_none(self):
        """Empty registry results in no match (None)."""
        from masonry.src.routing.semantic import route_semantic
        result = route_semantic("simulate parameter sweep", registry=[])
        assert result is None
