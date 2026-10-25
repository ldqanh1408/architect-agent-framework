"""CRUD creates isolated immutable candidates; no multi-file overwrite of a live editor."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import uuid

import yaml

from .model import SddError, Status, digest, utc_now
from .parsing import relative_path
from .schema import ARTIFACT, validate
from .storage import Store, atomic_write
from .workspace import CONFIG, build_snapshot, capture, diff


def propose(store: Store, root: Path, operations: list[dict], operation_id: str | None = None,
            skill: str | None = None, expected_snapshot: str | None = None,
            base_change: str | None = None) -> dict:
    with store.lock():
        origin = capture(root)
        baseline = store.baseline()
        current = origin
        restored_ids = []
        if base_change:
            parent = store.read("changes", base_change)
            if parent is None:
                raise SddError("CHANGE_UNKNOWN", base_change)
            if parent["origin_snapshot"] != origin.digest or parent["base_acceptance"] != (baseline["acceptance_id"] if baseline else None):
                raise SddError("BASE_CHANGE_STALE", "The parent candidate no longer shares the live origin and accepted baseline", Status.STALE)
            current = store.load_snapshot(parent["snapshot_digest"])
            restored_ids = parent.get("restored_ids", [])
        # A pending candidate never supplies its own authorisation grants.
        authority = store.load_snapshot(baseline["snapshot_digest"]).config if baseline else origin.config
        if authority["policy"].get("decision_authority") == "external" and (not skill or not expected_snapshot):
            raise SddError("HOST_PROPOSAL_BINDING_REQUIRED", "Host proposals require an author skill and the exact live origin snapshot")
        request_digest = digest({"operations": operations, "skill": skill, "expected_snapshot": expected_snapshot,
                                 **({"base_change": base_change} if base_change else {})})
        operation_id = operation_id or "OP-" + uuid.uuid4().hex
        previous = store.read("changes", operation_id)
        if previous:
            if previous["request_digest"] != request_digest:
                raise SddError("OPERATION_CONFLICT", operation_id, Status.STALE)
            return previous
        if expected_snapshot and expected_snapshot != origin.digest:
            raise SddError("EXPECTED_REVISION_CONFLICT", "Workspace changed", Status.STALE)
        files, config = deepcopy(current.files), deepcopy(current.config)
        write_set, restored, touched = set(), list(restored_ids), set()
        for op_idx, operation in enumerate(operations):
            if not isinstance(operation, dict):
                raise SddError("VALIDATION_ERROR", f"Operation at index {op_idx} must be an object (field_path=operations[{op_idx}])")
            action, identifier = operation.get("action") or operation.get("op"), operation.get("artifact_id")
            for req_key in {"create": ("metadata", "content"), "update": ("content",), "rename": ("path",), "restore": ("from_snapshot",)}.get(str(action), ()):
                if req_key not in operation or operation[req_key] is None:
                    raise SddError("VALIDATION_ERROR", f"Operation '{action}' missing required field '{req_key}' (field_path=operations[{op_idx}].{req_key})")
            if action == "configure":
                if operation.get("expected_config") != digest(current.config):
                    raise SddError("EXPECTED_CONFIG_CONFLICT", "Configuration changed", Status.STALE)
                updates = operation.get("set", {})
                if not isinstance(updates, dict) or not updates or set(updates) - {"obligations", "policy", "provider", "external_sources", "skills", "owners", "attachments", "document_coverage", "selected_profile", "governance_preset", "control_directories"}:
                    raise SddError("CONFIGURATION_SCOPE", "Unsupported configuration fields")
                if skill:
                    grant = authority.get("skills", {}).get(skill, {})
                    if "configure" not in grant.get("capabilities", []) or set(updates) - {"obligations", "external_sources", "document_coverage", "selected_profile"}:
                        raise SddError("CAPABILITY_DENIED", "Only human configuration can change policy/provider/identity grants")
                    for key in updates:
                        if key in {"document_coverage", "selected_profile"}:
                            continue
                        old_items = {x["id"]: x for x in current.config.get(key, [])}
                        new_items = {x["id"]: x for x in updates[key]}
                        for changed_id in old_items.keys() | new_items.keys():
                            if old_items.get(changed_id) != new_items.get(changed_id) and any(x and x["owner"] != skill for x in (old_items.get(changed_id), new_items.get(changed_id))):
                                raise SddError("OWNER_MISMATCH", changed_id)
                config.update(deepcopy(updates))
                write_set.add(CONFIG)
                continue
            if action not in {"create", "update", "delete", "rename", "restore", "split", "merge", "deprecate"}:
                raise SddError("OPERATION_UNSUPPORTED", str(action))
            if action in {"split", "merge"}:
                sources = operation.get("sources", [])
                replacements = operation.get("replacements", [])
                if not sources or not replacements or (action == "split" and len(sources) != 1) or (action == "merge" and len(replacements) != 1):
                    raise SddError("LINEAGE_MAPPING_REQUIRED", action)
                for source in sources:
                    old = config["artifacts"].get(source)
                    if old is None:
                        raise SddError("ARTIFACT_UNKNOWN", source)
                    if operation.get("expected_revisions", {}).get(source) != digest(files[old["path"]].encode()):
                        raise SddError("EXPECTED_REVISION_CONFLICT", source, Status.STALE)
                    write_set.add(old["path"])
                    touched.add(source)
                    del files[old["path"]]
                    del config["artifacts"][source]
                for replacement in replacements:
                    new_id = replacement["artifact_id"]
                    meta = {**replacement["metadata"], "supersedes": sources}
                    validate(meta, ARTIFACT)
                    if new_id in config["artifacts"] or meta["path"] in files:
                        raise SddError("IDENTITY_CONFLICT", new_id)
                    relative_path(meta["path"])
                    config["artifacts"][new_id] = meta
                    files[meta["path"]] = replacement["content"]
                    touched.add(new_id)
                    write_set.add(meta["path"])
                continue
            if not isinstance(identifier, str):
                raise SddError("ARTIFACT_ID_REQUIRED", str(identifier))
            touched.add(identifier)
            old = config["artifacts"].get(identifier)
            if action in {"create", "restore"}:
                if old:
                    raise SddError("DUPLICATE_ID", identifier)
                if action == "restore":
                    source = store.load_snapshot(operation["from_snapshot"])
                    if identifier not in source.artifacts:
                        raise SddError("ARTIFACT_UNKNOWN", identifier)
                    meta = deepcopy(source.config["artifacts"][identifier])
                    content = source.artifacts[identifier].text
                    restored.append(identifier)
                    restored.extend(source.artifacts[identifier].clauses)
                else:
                    meta, content = operation["metadata"], operation["content"]
                validate(meta, ARTIFACT)
                relative_path(meta["path"])
                if meta["path"] in files:
                    raise SddError("PATH_COLLISION", meta["path"])
                config["artifacts"][identifier] = deepcopy(meta)
                files[meta["path"]] = content
                write_set.add(meta["path"])
            else:
                if old is None or old["path"] not in files:
                    raise SddError("ARTIFACT_UNKNOWN", identifier)
                if operation.get("expected_revision") != digest(files[old["path"]].encode()):
                    raise SddError("EXPECTED_REVISION_CONFLICT", identifier, Status.STALE)
                write_set.add(old["path"])
                if action == "delete":
                    del files[old["path"]]
                    del config["artifacts"][identifier]
                elif action == "deprecate":
                    old["status"] = "deprecated"
                elif action == "rename":
                    destination = relative_path(operation["path"])
                    if destination in files or any(p.casefold() == destination.casefold() and p != old["path"] for p in files):
                        raise SddError("PATH_COLLISION", destination)
                    files[destination] = files.pop(old["path"])
                    old["path"] = destination
                    write_set.add(destination)
                else:
                    files[old["path"]] = operation["content"]
                    if "metadata" in operation:
                        validate(operation["metadata"], ARTIFACT)
                        if operation["metadata"]["path"] != old["path"]:
                            raise SddError("RENAME_REQUIRED", identifier)
                        config["artifacts"][identifier] = deepcopy(operation["metadata"])
        if skill:
            grant = authority.get("skills", {}).get(skill)
            if grant is None or "author" not in grant["capabilities"]:
                raise SddError("CAPABILITY_DENIED", skill)
            prefixes = [relative_path(p) for p in grant["write_scope"]]
            if any(not any(p == prefix or p.startswith(prefix + "/") for prefix in prefixes) for p in write_set):
                raise SddError("WRITE_SCOPE_DENIED", ", ".join(sorted(write_set)))
            for identifier in touched:
                metas = (current.config["artifacts"].get(identifier), config["artifacts"].get(identifier))
                if any(meta and meta["owner"] != skill for meta in metas):
                    raise SddError("OWNER_MISMATCH", identifier)
        files[CONFIG] = yaml.safe_dump(config, sort_keys=False, allow_unicode=True)
        candidate = build_snapshot(files)
        store.save_snapshot(origin)
        store.save_snapshot(candidate)
        record = {"change_id": operation_id, "request_digest": request_digest, "created_at": utc_now(),
                  "snapshot_digest": candidate.digest, "origin_snapshot": origin.digest,
                  "parent_change": base_change,
                  "base_acceptance": baseline["acceptance_id"] if baseline else None,
                  "operations": operations, "write_set": sorted(write_set), "restored_ids": restored,
                  "status": "planned", "origin": "proposal", "skill": skill}
        store.write("changes", operation_id, record, immutable=True)
        return record


def reconcile(store: Store, root: Path) -> dict:
    with store.lock():
        snapshot = capture(root)
        store.save_snapshot(snapshot)
        baseline = store.baseline()
        before = store.load_snapshot(baseline["snapshot_digest"]) if baseline else None
        identity = digest({"snapshot": snapshot.digest, "base": baseline})
        record = {"change_id": "CH-" + identity[:24], "request_digest": identity,
                  "snapshot_digest": snapshot.digest, "origin_snapshot": snapshot.digest,
                  "base_acceptance": baseline["acceptance_id"] if baseline else None,
                  "operations": [], "restored_ids": [], "write_set": diff(before, snapshot)["changed"],
                  "status": "discovered", "origin": "external"}
        store.write("changes", record["change_id"], record, immutable=True)
        return record


def export_snapshot(snapshot, destination: Path, store=None, expected_baseline=None):
    destination = Path(destination)
    if destination.exists():
        raise SddError("EXPORT_DESTINATION_EXISTS", "Choose a new directory; existing edits are never overwritten")
    destination.mkdir(parents=True)
    try:
        for name, text in snapshot.files.items():
            relative_path(name)
            atomic_write(destination / name, text.encode())
        if store:
            with store.lock():
                if store.baseline() != expected_baseline or expected_baseline["snapshot_digest"] != snapshot.digest:
                    raise SddError("EXPORT_BASELINE_CHANGED", "Accepted pointer changed during export", Status.STALE)
                exported = Store(destination)
                # Carry provenance so adopting an official export does not lose
                # history or require inventing a new human acceptance. Publish
                # its pointer last, after all referenced records are present.
                for category in ("snapshots", "acceptances", "changes", "packets", "review_jobs", "language_jobs", "language_repairs", "repair_accounts", "evaluation_monitors", "evaluation_revocations", "language_evaluations", "language_evaluation_runs", "label_manifests", "label_approvals", "decisions", "observations", "evaluations", "evaluation_runs", "budgets", "finding_history", "journal"):
                    for path in sorted((store.root / category).glob("*.json")):
                        exported.write(category, path.stem, store.read(category, path.stem), immutable=True)
                exported.write("state", "baseline", expected_baseline, immutable=True)
        atomic_write(destination / ".sdd" / "export.json", __import__("json").dumps({"snapshot_digest": snapshot.digest, "export_kind": "ACCEPTED" if store else "DRAFT"}).encode())
    except Exception:
        # Keep a partial export for inspection. It is not a published baseline.
        raise
    return {"status": "PASS", "snapshot_digest": snapshot.digest, "destination": str(destination.resolve()),
            "acceptance_id": expected_baseline["acceptance_id"] if expected_baseline else None}
