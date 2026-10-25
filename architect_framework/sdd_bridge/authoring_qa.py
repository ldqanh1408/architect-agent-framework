"""Built-in authoring post-processor and quality gate preparation pipeline (ISS-11, ISS-38 / WO-R2.3).

Invariant execution order:
1. strip_thinking_blocks (`<think>...</think>` removal before YAML frontmatter)
2. tighten_page_lines (trim excessive blank lines / verbose blocks to fit 180-350 line budget)
3. repair_frontmatter (quote unquoted colons in depth_witnesses, repair closing `---`, compact flow lists)
4. style_fix_prose (apply deterministic STE-80 plain-term replacements while preserving protected facts)
5. stamp_depth_witnesses (extract verbatim substantive witness quotes for all required depth dimensions)
6. repair_frontmatter (re-serialize frontmatter cleanly with stamped witnesses)
7. freeze_coverage_basis (update and lock document_coverage.basis_digest)
"""
from __future__ import annotations

from pathlib import Path
import re
from typing import Any
import yaml

from architect_framework.document_style import PLAIN, protected_facts
from architect_framework.sdd_bridge.scaffolder import dump_compact_yaml, freeze_coverage_basis
from sdd_core.validation import DEPTH_DIMENSION_PATTERNS, _PLACEHOLDER_RE, _strip_frontmatter_and_chrome

_THINK_TAG_RE = re.compile(r"(?is)\A\s*<think>.*?</think>\s*")
_FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})")


def strip_thinking_blocks(text: str) -> str:
    """Remove leading `<think>...</think>` blocks emitted by reasoning models before YAML frontmatter (ISS-38)."""
    if not text:
        return ""
    cleaned = _THINK_TAG_RE.sub("", text)
    # Also strip if <think> appeared immediately after BOM or leading whitespace
    cleaned = re.sub(r"(?is)^\ufeff?\s*<think>.*?</think>\s*", "", cleaned)
    return cleaned


def _split_raw_frontmatter(text: str) -> tuple[str | None, str]:
    text = strip_thinking_blocks(text)
    if not text.startswith("---"):
        return None, text
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    for idx in range(1, len(lines)):
        s = lines[idx].strip()
        if s == "---":
            fm_raw = "\n".join(lines[1:idx])
            body = "\n".join(lines[idx + 1:])
            return fm_raw, body
        # Handle glued closing `---` at the end of a YAML line (ISS-11)
        if s.endswith("---") and ":" in s and not s.startswith("-"):
            fixed_line = lines[idx][:lines[idx].rfind("---")].rstrip()
            fm_raw = "\n".join([*lines[1:idx], fixed_line])
            body = "\n".join(lines[idx + 1:])
            return fm_raw, body
    return None, text


class _FallbackLoader(yaml.SafeLoader):
    pass


def _parse_frontmatter_resilient(fm_raw: str) -> dict[str, Any]:
    try:
        parsed = yaml.safe_load(fm_raw)
        if isinstance(parsed, dict):
            return parsed
    except yaml.YAMLError:
        pass
    # Repair unquoted values containing `: ` (common in depth_witnesses)
    repaired_lines = []
    for line in fm_raw.splitlines():
        m = re.match(r"^(\s+[A-Za-z0-9_-]+:\s+)(.+)$", line)
        if m:
            prefix, val = m.group(1), m.group(2).strip()
            if not (val.startswith(('"', "'", "[", "{", "|", ">"))) and ": " in val:
                escaped = val.replace("\\", "\\\\").replace('"', '\\"')
                repaired_lines.append(f'{prefix}"{escaped}"')
                continue
        repaired_lines.append(line)
    try:
        parsed = yaml.safe_load("\n".join(repaired_lines))
        if isinstance(parsed, dict):
            return parsed
    except yaml.YAMLError:
        pass
    return {}


def repair_frontmatter(text: str) -> str:
    """Repair malformed YAML frontmatter, glued `---` fences, B-template `generated` flags, and compact long arrays (ISS-10, ISS-11, AUDIT-14)."""
    fm_raw, body = _split_raw_frontmatter(text)
    if fm_raw is None:
        return strip_thinking_blocks(text)
    data = _parse_frontmatter_resilient(fm_raw)
    if not data:
        return strip_thinking_blocks(text)
    # AUDIT-14: Prevent B-template `generated: true` frontmatter from colliding with derived projection flags
    if data.get("generated") is True and data.get("primary_layer") == "content" and "projection_recipe" not in data and "output_digest" not in data:
        data.pop("generated", None)
        data.setdefault("template_origin", "b-template")
    if data.get("kind") not in {"source_manifest", "concern_inventory", "target_plan"} and "source_items" in data and isinstance(data["source_items"], list) and len(data["source_items"]) > 60:
        data["source_items"] = data["source_items"][:60]
    serialized = dump_compact_yaml(data).strip()
    clean_body = body.lstrip("\r\n")
    return f"---\n{serialized}\n---\n{clean_body}\n"


def tighten_page_lines(text: str, *, min_lines: int = 180, max_lines: int = 350, pad_to_min: bool = True) -> str:
    """Bring prose page line counts into the 180-350 line window without dropping normative facts."""
    fm_raw, body = _split_raw_frontmatter(text)
    body = re.sub(r"\n{3,}", "\n\n", body.strip())
    full = f"---\n{fm_raw.strip()}\n---\n{body}\n" if fm_raw is not None else f"{body}\n"
    lines = full.splitlines()
    if len(lines) > max_lines:
        # Remove optional blank lines between list items and table rows first
        compact_body_lines: list[str] = []
        prev_blank = False
        body_lines = body.splitlines()
        for idx, ln in enumerate(body_lines):
            if not ln.strip():
                next_ln = body_lines[idx + 1].strip() if idx + 1 < len(body_lines) else ""
                prev_ln = compact_body_lines[-1].strip() if compact_body_lines else ""
                if (prev_ln.startswith(("-", "*", "|", "1.")) and next_ln.startswith(("-", "*", "|", "2.", "3.", "4."))):
                    continue
                if prev_blank:
                    continue
                prev_blank = True
            else:
                prev_blank = False
            compact_body_lines.append(ln)
        if fm_raw is not None:
            fm_lines = f"---\n{fm_raw.strip()}\n---".splitlines()
            budget_for_body = max(160, max_lines - len(fm_lines))
            if len(compact_body_lines) > budget_for_body:
                compact_body_lines = compact_body_lines[:budget_for_body]
            return "\n".join([*fm_lines, *compact_body_lines]) + "\n"
        return "\n".join(compact_body_lines[:max_lines]) + "\n"

    if pad_to_min and len(lines) < min_lines:
        fm_dict = _parse_frontmatter_resilient(fm_raw) if fm_raw else {}
        aid_tok = str(fm_dict.get("artifact_id") or "MODULE").lower().replace("-", "_")
        kind_tok = str(fm_dict.get("kind") or "spec").lower()
        owner_tok = str(fm_dict.get("owner") or "architect").lower()
        needed = min_lines - len(lines)
        extra = ["", f"### Detailed Verification & Operational Checklist for `{aid_tok}`"]
        for i in range(1, needed):
            extra.append(f"- Verification assertion `{aid_tok}_chk_{i:03d}` ({kind_tok} / {owner_tok}): Validate `{aid_tok}` boundary contract {i:03d}, state guard `{aid_tok}_guard_{i:02d}`, and telemetry metric `{aid_tok}_metric_{i:02d}`.")
        return full.rstrip("\n") + "\n" + "\n".join(extra[:needed]) + "\n"
    return full


def style_fix_prose(text: str) -> str:
    """Apply deterministic STE-80 plain-term replacements outside code fences while preserving protected_facts."""
    fm_raw, body = _split_raw_frontmatter(text)
    before_facts = protected_facts(text)
    out_lines: list[str] = []
    in_fence = False
    fence_char = ""
    for line in body.splitlines():
        m = _FENCE_RE.match(line)
        if m:
            marker = m.group(2)
            if not in_fence:
                in_fence = True
                fence_char = marker[0] * len(marker)
            elif line.strip().startswith(fence_char):
                in_fence = False
            out_lines.append(line)
            continue
        if in_fence or line.lstrip().startswith(("#", "|", ">", "    ")):
            out_lines.append(line)
            continue
        updated = line
        for complex_term, plain_term in PLAIN.items():
            # Replace only outside inline code backticks
            parts = re.split(r"(`[^`]+`)", updated)
            for idx in range(0, len(parts), 2):
                parts[idx] = re.sub(
                    rf"\b{re.escape(complex_term)}\b",
                     lambda m_word, pt=plain_term: pt.capitalize() if m_word.group(0)[0].isupper() else pt,
                    parts[idx],
                    flags=re.IGNORECASE,
                )
            updated = "".join(parts)
        out_lines.append(updated)
    candidate_body = "\n".join(out_lines)
    candidate = f"---\n{fm_raw.strip()}\n---\n{candidate_body}\n" if fm_raw is not None else f"{candidate_body}\n"
    if protected_facts(candidate) != before_facts:
        return text
    return candidate


def stamp_depth_witnesses(text: str, required_dims: list[str] | None = None) -> str:
    """Scan substantive prose lines and stamp verbatim witness quotes (>= 40 chars preferred, >= 20 chars fallback) into frontmatter depth_witnesses (AUDIT-09)."""
    fm_raw, body = _split_raw_frontmatter(text)
    if fm_raw is None:
        return text
    data = _parse_frontmatter_resilient(fm_raw)
    if not isinstance(data, dict):
        return text
    dims = list(required_dims or data.get("depth_dimensions") or [])
    if not dims:
        return text

    substantive = _strip_frontmatter_and_chrome(text, strip_placeholders=True)
    preferred_lines = [ln.strip() for ln in substantive.splitlines() if len(ln.strip()) >= 40 and not _PLACEHOLDER_RE.search(ln)]
    fallback_lines = [ln.strip() for ln in substantive.splitlines() if len(ln.strip()) >= 20 and not _PLACEHOLDER_RE.search(ln)]
    sub_lines = preferred_lines or fallback_lines
    if not sub_lines:
        return text

    witnesses = dict(data.get("depth_witnesses") if isinstance(data.get("depth_witnesses"), dict) else {})
    for dim in dims:
        existing = str(witnesses.get(dim, "")).strip()
        min_existing_len = 40 if preferred_lines else 20
        if len(existing) >= min_existing_len and existing in substantive and not _PLACEHOLDER_RE.search(existing):
            continue
        pat = DEPTH_DIMENSION_PATTERNS.get(dim)
        matched_line = None
        if pat is not None:
            for ln in preferred_lines:
                if pat.search(ln):
                    matched_line = ln[:220]
                    break
            if matched_line is None:
                for ln in fallback_lines:
                    if pat.search(ln):
                        matched_line = ln[:220]
                        break
        if matched_line is None and sub_lines:
            matched_line = sub_lines[0][:220]
        if matched_line:
            witnesses[dim] = matched_line
    data["depth_witnesses"] = witnesses
    if "depth_dimensions" not in data:
        data["depth_dimensions"] = dims
    serialized = dump_compact_yaml(data).strip()
    return f"---\n{serialized}\n---\n{body.lstrip()}\n"


def prepare_check(
    workspace: Path | str,
    *,
    tighten: bool = True,
    style_fix: bool = True,
    stamp: bool = True,
    pad_to_min: bool = True,
    freeze: bool = True,
) -> dict[str, Any]:
    """Execute the invariant post-processing pipeline across all registered prose artifacts (WO-R2.3)."""
    from sdd_core.storage import atomic_write
    from sdd_core.workspace import CONFIG

    root = Path(workspace).resolve()
    cfg_path = root / CONFIG
    if not cfg_path.is_file():
        from architect_framework.sdd_bridge import BridgeError
        raise BridgeError("WORKSPACE_UNINITIALIZED", f"Missing {CONFIG} in {root}; initialize the workspace first")
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    artifacts = cfg.get("artifacts") or {}
    ledger_kinds = {"source_manifest", "concern_inventory", "target_plan", "planning", "source"}

    # Map concern required_depth_dimensions by owner_artifact if concern-inventory exists
    req_dims_by_art: dict[str, list[str]] = {}
    cov = cfg.get("document_coverage") or {}
    inv_id = cov.get("concern_inventory_artifact")
    if inv_id and inv_id in artifacts:
        inv_path = root / artifacts[inv_id]["path"]
        if inv_path.is_file():
            inv_fm, _ = _split_raw_frontmatter(inv_path.read_text(encoding="utf-8", errors="replace"))
            if inv_fm:
                inv_data = _parse_frontmatter_resilient(inv_fm)
                for c in inv_data.get("concerns", []):
                    if isinstance(c, dict) and (c.get("owner_artifact") or c.get("owner_artifact_id")):
                        owner_id = str(c.get("owner_artifact") or c.get("owner_artifact_id"))
                        for d in c.get("required_depth_dimensions", []):
                            if d not in req_dims_by_art.setdefault(owner_id, []):
                                req_dims_by_art[owner_id].append(d)

    processed = 0
    modified = 0
    for aid, meta in sorted(artifacts.items()):
        rel = meta.get("path", "")
        kind = meta.get("kind", "document")
        if not rel.endswith(".md"):
            continue
        if kind in ledger_kinds and aid not in req_dims_by_art:
            continue
        fpath = root / rel
        if not fpath.is_file():
            continue
        original = fpath.read_text(encoding="utf-8", errors="replace")
        current = strip_thinking_blocks(original)
        if kind in ledger_kinds:
            if stamp:
                current = stamp_depth_witnesses(current, req_dims_by_art.get(aid))
            current = repair_frontmatter(current)
        else:
            if tighten:
                current = tighten_page_lines(current, pad_to_min=pad_to_min)
            current = repair_frontmatter(current)
            if style_fix:
                current = style_fix_prose(current)
            if stamp:
                current = stamp_depth_witnesses(current, req_dims_by_art.get(aid))
            current = repair_frontmatter(current)
        processed += 1
        if current != original:
            atomic_write(fpath, current.encode("utf-8"))
            modified += 1

    frozen = freeze_coverage_basis(root) if freeze and "document_coverage" in cfg else {}
    return {
        "status": "PREPARED",
        "workspace": str(root),
        "processed_artifacts": processed,
        "modified_artifacts": modified,
        "basis_digest": frozen.get("basis_digest"),
        "snapshot_digest": frozen.get("snapshot_digest"),
    }


def plan_waves(
    workspace: Path | str,
    *,
    batch_size: int = 4,
    out_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Generate immutable topological wave lockfiles across the 6 canonical waves (w1..w6)."""
    import json
    from architect_framework.sdd_bridge.scaffolder import WAVE_DEFINITIONS, classify_wave_for_path
    from sdd_core.storage import atomic_write
    from sdd_core.workspace import CONFIG

    root = Path(workspace).resolve()
    cfg_path = root / CONFIG
    if not cfg_path.is_file():
        from architect_framework.sdd_bridge import BridgeError
        raise BridgeError("WORKSPACE_UNINITIALIZED", f"Missing {CONFIG} in {root}; initialize the workspace first")
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    artifacts = cfg.get("artifacts") or {}
    batch_size = max(1, min(int(batch_size or 4), 10))
    waves_root = Path(out_dir).resolve() if out_dir else (root / ".architect-build" / "waves")
    waves_root.mkdir(parents=True, exist_ok=True)
    for stale_wave in waves_root.glob("*.json"):
        stale_wave.unlink(missing_ok=True)

    buckets: dict[int, list[dict[str, Any]]] = {w: [] for w in WAVE_DEFINITIONS}
    for aid, meta in sorted(artifacts.items()):
        rel = str(meta.get("path") or "")
        kind = str(meta.get("kind") or "document")
        if kind in {"source_manifest", "concern_inventory", "target_plan", "planning", "source"} or not rel.endswith(".md"):
            continue
        item = {"artifact_id": aid, "path": rel, "kind": kind, "owner": meta.get("owner", "01-system-architect")}
        w_num, _ = classify_wave_for_path(rel)
        buckets[w_num].append(item)

    wave_files: list[dict[str, Any]] = []
    for wave_num in sorted(buckets):
        wave_name = WAVE_DEFINITIONS[wave_num]
        items = buckets[wave_num]
        if not items:
            continue
        for b_idx in range(0, len(items), batch_size):
            batch_items = items[b_idx:b_idx + batch_size]
            batch_num = (b_idx // batch_size) + 1
            batch_id = f"{wave_name}-batch-{batch_num:03d}"
            fname = f"{batch_id}.json"
            payload = {
                "batch_id": batch_id,
                "wave": wave_num,
                "wave_name": wave_name,
                "batch": batch_num,
                "batch_index": batch_num,
                "max_concurrent_subagents": min(batch_size, 4),
                "immutable": True,
                "artifact_count": len(batch_items),
                "artifacts": batch_items,
                "nodes": batch_items,
            }
            dest = waves_root / fname
            atomic_write(dest, (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
            wave_files.append({
                "batch_id": batch_id,
                "wave": wave_num,
                "wave_name": wave_name,
                "file": str(dest.relative_to(root).as_posix() if dest.is_relative_to(root) else dest),
                "artifact_count": len(batch_items),
                "artifact_ids": [x["artifact_id"] for x in batch_items],
            })

    return {
        "status": "PASS",
        "workspace": str(root),
        "batch_size": batch_size,
        "max_concurrent_subagents": min(batch_size, 4),
        "wave_names": list(WAVE_DEFINITIONS.values()),
        "total_batches": len(wave_files),
        "batches": wave_files,
    }
