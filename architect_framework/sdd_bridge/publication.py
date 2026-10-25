"""Publish only certified bytes, with a resumable journal and a filesystem CAS."""
from pathlib import Path

from . import BridgeError, engine_for


def prepare(engine, change, record):
    identifier = "PUB-" + record["decision_id"]
    journal = {"publication_id": identifier, "change_id": change["change_id"],
               "origin_snapshot": change["origin_snapshot"], "snapshot_digest": change["snapshot_digest"],
               "acceptance_id": "console-" + record["decision_id"], "phase": "PREPARED"}
    with engine.store.lock():
        engine.store.write("host_publications", identifier, journal, immutable=True)
    return journal


def publish(workspace, identifier, fault=None):
    from sdd_core.model import digest
    from sdd_core.parsing import relative_path
    from sdd_core.storage import atomic_write
    from sdd_core.workspace import _inventory, capture
    engine = engine_for(workspace)
    with engine.store.lock():
        journal = engine.store.read("host_publications", identifier)
        if journal is None:
            raise BridgeError("PUBLICATION_UNKNOWN", "No publication journal for this operation")
        baseline = engine.store.baseline()
        if baseline is None or baseline["acceptance_id"] != journal["acceptance_id"] or baseline["snapshot_digest"] != journal["snapshot_digest"]:
            raise BridgeError("PUBLICATION_BASE_CONFLICT", "The certified baseline changed; preserve the working files", "STALE")
        certificate = engine.store.read("acceptances", baseline["acceptance_id"])
        if certificate is None or digest(certificate) != baseline["certificate_digest"]:
            raise BridgeError("PUBLICATION_CERTIFICATE_INVALID", "The accepted certificate is missing or changed")
        if certificate.get("origin_snapshot") != journal["origin_snapshot"] or certificate["change_id"] != journal["change_id"]:
            raise BridgeError("PUBLICATION_BINDING_INVALID", "The journal does not match the certified origin and change")
        target = engine.store.load_snapshot(journal["snapshot_digest"])
        origin = engine.store.load_snapshot(journal["origin_snapshot"])
        # Only the explicitly reserved host metadata is excluded. Unknown documents
        # and edits are never overwritten by recovery.
        controls = set(origin.config.get("control_directories", [])) | set(target.config.get("control_directories", []))
        live = _inventory(engine.workspace, 8 * 1024 * 1024, controls)
        if journal["phase"] == "PREPARED" and live != origin.files:
            raise BridgeError("PUBLICATION_WORKSPACE_CHANGED", "Working documents changed since signing; preserve them and inspect the accepted snapshot", "STALE")
        for path in set(live) | set(origin.files) | set(target.files):
            if path in live and live[path] not in {origin.files.get(path), target.files.get(path)}:
                raise BridgeError("PUBLICATION_WORKSPACE_CHANGED", f"Preserving changed or unknown document: {path}", "STALE")
            if path not in live and path in origin.files and path in target.files and journal["phase"] == "PREPARED":
                raise BridgeError("PUBLICATION_WORKSPACE_CHANGED", f"Preserving deletion: {path}", "STALE")
        journal["phase"] = "APPLYING"
        engine.store.write("host_publications", identifier, journal)
        for path in sorted(set(origin.files) - set(target.files)):
            location = engine.workspace / relative_path(path)
            if location.is_file():
                location.unlink()
        # Config last: interim files cannot masquerade as a fully published spec.
        ordered = sorted(target.files, key=lambda p: (p == "sdd-workspace.yml", p))
        for path in ordered:
            location = engine.workspace / relative_path(path)
            for parent in (location, *location.parents):
                if parent == engine.workspace:
                    break
                if parent.is_symlink():
                    raise BridgeError("PUBLICATION_SYMLINK", "Publication cannot cross a symlink")
            atomic_write(location, target.files[path].encode("utf-8"))
            if fault:
                fault(path)
        if capture(engine.workspace).digest != target.digest:
            raise BridgeError("PUBLICATION_INCOMPLETE", "Publication did not reproduce the certified snapshot", "INCOMPLETE")
        journal["phase"] = "PUBLISHED"
        engine.store.write("host_publications", identifier, journal)
        return {"status": "PUBLISHED", "snapshot_digest": target.digest, "publication_id": identifier}


def recover(workspace):
    engine = engine_for(workspace)
    transactions = engine.recover()["transactions"]
    results = []
    for journal in engine.store.list("host_publications"):
        if journal["phase"] in {"PUBLISHED", "ABORTED", "SUPERSEDED"}:
            continue
        with engine.store.lock():
            transaction = engine.store.read("journal", journal["acceptance_id"])
            baseline = engine.store.baseline()
            if not transaction or transaction["phase"] == "ABORTED":
                journal["phase"] = "ABORTED"
                engine.store.write("host_publications", journal["publication_id"], journal)
                results.append({"publication_id": journal["publication_id"], "status": "ABORTED",
                                "next_action": "Inspect and sign a new acceptance; live documents were preserved."})
                continue
            if baseline is None or baseline["acceptance_id"] != journal["acceptance_id"]:
                journal["phase"] = "SUPERSEDED"
                engine.store.write("host_publications", journal["publication_id"], journal)
                results.append({"publication_id": journal["publication_id"], "status": "SUPERSEDED"})
                continue
        try:
            results.append(publish(workspace, journal["publication_id"]))
        except (BridgeError, OSError, ValueError, RuntimeError) as exc:
            results.append({"publication_id": journal["publication_id"], "status": "INCOMPLETE", "error": str(exc)})
    return {"status": "INCOMPLETE" if any(r["status"] == "INCOMPLETE" for r in results) else "PASS",
            "transactions": transactions, "publications": results}
