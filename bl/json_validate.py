"""bl/json_validate.py — validate the JSON output block in BL 2.0 findings."""

import json
import re

REQUIRED_JSON_FIELDS = {"verdict", "question_id"}

_JSON_FENCE_PATTERN = re.compile(r"```json\s*\n(.*?)```", re.DOTALL)


def validate_finding_json(finding_text: str) -> tuple[dict | None, str | None]:
    """Extract and validate the LAST fenced ```json block in finding_text.

    Returns:
      (parsed_dict, None)      — valid JSON with all required fields present
      (None, error_message)    — JSON block found but malformed or missing fields
      (None, None)             — no JSON block found (prose format, not an error)
    """
    matches = _JSON_FENCE_PATTERN.findall(finding_text)
    if not matches:
        return None, None

    raw = matches[-1].strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"JSON parse error: {exc}"

    missing = REQUIRED_JSON_FIELDS - parsed.keys()
    if missing:
        field_list = ", ".join(sorted(missing))
        return None, f"missing required fields: {field_list}"

    return parsed, None


def is_retry(question_status: str) -> bool:
    """Return True if status contains 'PENDING_RETRY' or 'FORMAT-RETRY'."""
    return "PENDING_RETRY" in question_status or "FORMAT-RETRY" in question_status
