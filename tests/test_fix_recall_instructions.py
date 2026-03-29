"""Tests for masonry/scripts/fix_recall_instructions.py"""
import sys
import pathlib
import textwrap
import tempfile
import os

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / 'masonry' / 'scripts'))

from fix_recall_instructions import (
    split_top_level_commas,
    parse_call_to_bullets,
    transform_file,
    block_has_only_recall_calls,
)


# ---------------------------------------------------------------------------
# split_top_level_commas
# ---------------------------------------------------------------------------

def test_split_simple():
    assert split_top_level_commas('a=1, b=2') == ['a=1', 'b=2']


def test_split_preserves_nested_brackets():
    result = split_top_level_commas('tags=["a", "b"], importance=0.9')
    assert result == ['tags=["a", "b"]', 'importance=0.9']


def test_split_preserves_nested_parens():
    result = split_top_level_commas('query="foo", domain="bar"')
    assert result == ['query="foo"', 'domain="bar"']


# ---------------------------------------------------------------------------
# parse_call_to_bullets
# ---------------------------------------------------------------------------

def test_parse_recall_search_single_line():
    call = 'recall_search(query="test assumption", domain="{project}-bricklayer")'
    result = parse_call_to_bullets(call)
    assert result is not None
    assert 'mcp__recall__recall_search' in result
    assert '`query`' in result
    assert '"test assumption"' in result


def test_parse_recall_store_multiline():
    call = textwrap.dedent('''\
        recall_store(
            content="FAILURE: [Q1] something failed",
            memory_type="semantic",
            domain="{project}-bricklayer",
            tags=["bricklayer", "agent:research-analyst"],
            importance=0.95,
            durability="durable",
        )''')
    result = parse_call_to_bullets(call)
    assert result is not None
    assert 'mcp__recall__recall_store' in result
    assert '`content`' in result
    assert '`memory_type`' in result
    assert '`tags`' in result
    assert '`importance`' in result


def test_parse_unknown_function_returns_none():
    assert parse_call_to_bullets('some_other_call(a=1)') is None


def test_parse_empty_args_returns_none():
    assert parse_call_to_bullets('recall_store()') is None


# ---------------------------------------------------------------------------
# block_has_only_recall_calls
# ---------------------------------------------------------------------------

def test_block_with_recall_store():
    body = 'recall_store(\n    content="x",\n    memory_type="semantic",\n)\n'
    assert block_has_only_recall_calls(body) is True


def test_block_with_non_recall_code():
    body = 'import os\nprint("hello")\n'
    assert block_has_only_recall_calls(body) is False


def test_empty_block():
    assert block_has_only_recall_calls('') is False
    assert block_has_only_recall_calls('   \n') is False


# ---------------------------------------------------------------------------
# transform_file — end-to-end
# ---------------------------------------------------------------------------

SAMPLE_AGENT_MD = textwrap.dedent('''\
    # Test Agent

    ## Some section

    Do some work first.

    **At session start** — check prior findings:
    ```
    recall_search(query="assumption tested", domain="{project}-bricklayer", tags=["agent:test"])
    ```

    **After FAILURE** — store immediately:
    ```
    recall_store(
        content="FAILURE: [Q1] Assumption refuted.",
        memory_type="semantic",
        domain="{project}-bricklayer",
        tags=["bricklayer", "agent:test", "type:assumption-failure"],
        importance=0.95,
        durability="durable",
    )
    ```

    ## Other section

    ```python
    # This is real code — should NOT be touched
    x = 1 + 1
    ```

    End of file.
''')


def test_transform_file_converts_recall_blocks():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(SAMPLE_AGENT_MD)
        tmp = f.name
    try:
        n = transform_file(tmp)
        assert n > 0, "Expected at least one block to be converted"
        result = pathlib.Path(tmp).read_text(encoding='utf-8')
        # Code blocks for recall calls should be gone
        assert '```\nrecall_search' not in result
        assert '```\nrecall_store' not in result
        # Imperative form should be present
        assert 'mcp__recall__recall_search' in result
        assert 'mcp__recall__recall_store' in result
        # Python block should be untouched
        assert '```python' in result
        assert 'x = 1 + 1' in result
    finally:
        os.unlink(tmp)


def test_transform_file_no_change_when_no_recall_blocks():
    content = "# Agent\n\nNo recall calls here.\n\n```python\nprint('hi')\n```\n"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(content)
        tmp = f.name
    try:
        n = transform_file(tmp)
        assert n == 0
        assert pathlib.Path(tmp).read_text(encoding='utf-8') == content
    finally:
        os.unlink(tmp)


def test_transform_preserves_surrounding_prose():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(SAMPLE_AGENT_MD)
        tmp = f.name
    try:
        transform_file(tmp)
        result = pathlib.Path(tmp).read_text(encoding='utf-8')
        assert '**At session start** — check prior findings:' in result
        assert '**After FAILURE** — store immediately:' in result
        assert 'Do some work first.' in result
        assert 'End of file.' in result
    finally:
        os.unlink(tmp)


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
