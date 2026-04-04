"""Tests for bl.tmux.stream_format — stream-json to human-readable formatter."""

from bl.tmux.stream_format import format_event


class TestFormatAssistant:
    def test_text_block(self):
        event = {
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "Hello world"}]},
        }
        assert format_event(event) == "Hello world"

    def test_thinking_block_shows_preview(self):
        event = {
            "type": "assistant",
            "message": {
                "content": [{"type": "thinking", "thinking": "Let me analyze this"}]
            },
        }
        result = format_event(event)
        assert "[thinking]" in result
        assert "analyze" in result

    def test_thinking_truncates_long_text(self):
        long_thought = "x" * 500
        event = {
            "type": "assistant",
            "message": {"content": [{"type": "thinking", "thinking": long_thought}]},
        }
        result = format_event(event)
        assert result.endswith("...")
        assert len(result) < 500

    def test_tool_use_bash(self):
        event = {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "name": "Bash",
                        "input": {"command": "ls -la"},
                    }
                ]
            },
        }
        result = format_event(event)
        assert "$ ls -la" in result

    def test_tool_use_read(self):
        event = {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "name": "Read",
                        "input": {"file_path": "/tmp/foo.py"},
                    }
                ]
            },
        }
        result = format_event(event)
        assert "Read:" in result
        assert "/tmp/foo.py" in result

    def test_tool_use_grep(self):
        event = {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "name": "Grep",
                        "input": {"pattern": "def main", "path": "/tmp"},
                    }
                ]
            },
        }
        result = format_event(event)
        assert "Grep:" in result
        assert "def main" in result

    def test_tool_use_edit(self):
        event = {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "name": "Edit",
                        "input": {"file_path": "/tmp/foo.py"},
                    }
                ]
            },
        }
        result = format_event(event)
        assert "Edit:" in result

    def test_tool_use_unknown(self):
        event = {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "tool_use", "name": "WebSearch", "input": {}}
                ]
            },
        }
        result = format_event(event)
        assert "WebSearch" in result

    def test_empty_content_returns_none(self):
        event = {"type": "assistant", "message": {"content": []}}
        assert format_event(event) is None

    def test_multiple_blocks(self):
        event = {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "text", "text": "I'll check"},
                    {
                        "type": "tool_use",
                        "name": "Bash",
                        "input": {"command": "ls"},
                    },
                ]
            },
        }
        result = format_event(event)
        assert "I'll check" in result
        assert "$ ls" in result


class TestFormatToolResult:
    def test_string_content(self):
        event = {"type": "tool_result", "content": "file1.py\nfile2.py"}
        result = format_event(event)
        assert "file1.py" in result
        assert "file2.py" in result

    def test_long_content_truncates(self):
        lines = [f"line{i}" for i in range(20)]
        event = {"type": "tool_result", "content": "\n".join(lines)}
        result = format_event(event)
        assert "+15 lines" in result

    def test_list_content(self):
        event = {
            "type": "tool_result",
            "content": [{"text": "result text"}],
        }
        result = format_event(event)
        assert "result text" in result

    def test_empty_content_returns_none(self):
        event = {"type": "tool_result", "content": ""}
        assert format_event(event) is None


class TestFormatResult:
    def test_success(self):
        event = {
            "type": "result",
            "subtype": "success",
            "total_cost_usd": 0.1234,
            "num_turns": 5,
        }
        result = format_event(event)
        assert "Done" in result
        assert "5 turns" in result
        assert "$0.1234" in result

    def test_error(self):
        event = {"type": "result", "subtype": "error", "error": "timeout"}
        result = format_event(event)
        assert "Error" in result
        assert "timeout" in result


class TestFormatIgnored:
    def test_system_event_returns_none(self):
        event = {"type": "system", "subtype": "init"}
        assert format_event(event) is None

    def test_unknown_type_returns_none(self):
        event = {"type": "unknown_thing"}
        assert format_event(event) is None
