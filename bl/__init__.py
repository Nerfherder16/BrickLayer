# BrickLayer package

from bl.question_weights import (  # noqa: F401
    QuestionWeight,
    compute_weight,
    get_sorted_questions,
    load_weights,
    prune_candidates,
    record_result,
    save_weights,
    weight_report,
)

# Model-hash embedding — patch write_finding to append **Model hash** to every finding.
# Wraps bl.findings.write_finding without modifying the over-limit findings.py file.
import bl.findings as _findings
from bl.model_version import compute_model_hash, embed_in_finding as _embed
from bl.config import cfg as _cfg
_orig_write_finding = _findings.write_finding


def _write_finding_with_hash(question: dict, result: dict):
    path = _orig_write_finding(question, result)
    try:
        project_root = _cfg.project_root if hasattr(_cfg, "project_root") else None
        model_hash = compute_model_hash(project_root) if project_root else "no-model"
        content = path.read_text(encoding="utf-8")
        patched = _embed(content, model_hash)
        if patched != content:
            path.write_text(patched, encoding="utf-8")
    except Exception:
        pass
    return path


_findings.write_finding = _write_finding_with_hash
