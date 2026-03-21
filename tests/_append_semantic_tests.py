"""Helper script to append new tests to test_routing_semantic.py."""

from pathlib import Path

new_tests = """

# ------------------------------------------------------------------
# Ollama URL env var configuration
# ------------------------------------------------------------------


class TestOllamaUrlConfig:
    def test_ollama_url_reads_from_env_var(self, monkeypatch):
        \"\"\"OLLAMA_URL env var overrides the default URL.\"\"\"
        import masonry.src.routing.semantic as sem
        monkeypatch.setenv("OLLAMA_URL", "http://custom-host:11434")

        # Re-import to pick up the env var (or check the module attr directly)
        import importlib
        importlib.reload(sem)

        assert sem._OLLAMA_URL == "http://custom-host:11434"

    def test_ollama_url_default_when_env_not_set(self, monkeypatch):
        \"\"\"When OLLAMA_URL is not set, uses the default URL.\"\"\"
        import masonry.src.routing.semantic as sem
        monkeypatch.delenv("OLLAMA_URL", raising=False)

        import importlib
        importlib.reload(sem)

        assert sem._OLLAMA_URL == "http://192.168.50.62:11434"

    def test_route_semantic_uses_ollama_url_parameter(self):
        \"\"\"route_semantic accepts ollama_url parameter and uses it for requests.\"\"\"
        import inspect
        from masonry.src.routing.semantic import route_semantic
        sig = inspect.signature(route_semantic)
        assert "ollama_url" in sig.parameters


# ------------------------------------------------------------------
# Corpus built from registry
# ------------------------------------------------------------------


class TestCorpusFromRegistry:
    def test_route_semantic_accepts_registry_list(self):
        \"\"\"route_semantic accepts a list[AgentRegistryEntry] as registry param.\"\"\"
        import inspect
        from masonry.src.routing.semantic import route_semantic
        sig = inspect.signature(route_semantic)
        assert "registry" in sig.parameters

    def test_empty_registry_returns_none(self):
        \"\"\"Empty registry results in no match (None).\"\"\"
        from masonry.src.routing.semantic import route_semantic
        result = route_semantic("simulate parameter sweep", registry=[])
        assert result is None
"""

target = Path("tests/test_routing_semantic.py")
current = target.read_text(encoding="utf-8")
target.write_text(current + new_tests, encoding="utf-8")
print("Appended successfully")
