from __future__ import annotations

import uuid

from .model import SddError, Status, digest, utc_now
from .parsing import relative_path
from .workspace import capture, diff
from .validation import check_snapshot


def start_task(store, root, skill, capability):
    with store.lock():
        snapshot = capture(root)
        grant = snapshot.config.get("skills", {}).get(skill)
        if grant is None or capability not in grant["capabilities"]:
            raise SddError("CAPABILITY_DENIED", f"{skill}:{capability}")
        if any(t["skill"] == skill and t["state"] == "running" for t in store.list("tasks")):
            raise SddError("TASK_ALREADY_RUNNING", skill, Status.STALE)
        store.save_snapshot(snapshot)
        task = {"contract_version": 1, "task_id": "TASK-" + uuid.uuid4().hex, "skill": skill,
                "capability": capability, "snapshot_digest": snapshot.digest,
                "read_set": {a.id: a.revision for a in snapshot.artifacts.values()},
                "write_scope": grant["write_scope"] if capability == "author" else [],
                "expected_revisions": {a.id: a.revision for a in snapshot.artifacts.values() if a.owner == skill},
                "state": "running", "started_at": utc_now()}
        store.write("tasks", task["task_id"], task)
        return task


def finish_task(store, root, task_id):
    with store.lock():
        task = store.read("tasks", task_id)
        if task is None:
            raise SddError("TASK_UNKNOWN", task_id)
        if task["state"] != "running":
            return task
        old = store.load_snapshot(task["snapshot_digest"])
        current = capture(root)
        delta = diff(old, current)
        prefixes = [relative_path(p) for p in task["write_scope"]]
        changed_paths = {name for name in old.files.keys() | current.files.keys() if old.files.get(name) != current.files.get(name)}
        # Identity registry edits go through proposals, not unrestricted skill IO.
        if any(not any(name == prefix or name.startswith(prefix + "/") for prefix in prefixes) for name in changed_paths):
            raise SddError("WRITE_SCOPE_DENIED", ", ".join(sorted(changed_paths)))
        if any((old.artifacts.get(i) or current.artifacts[i]).owner != task["skill"] for i in delta["changed"]):
            raise SddError("OWNER_MISMATCH", task["skill"])
        for identifier, revision in task["read_set"].items():
            if identifier not in task["expected_revisions"]:
                if identifier not in current.artifacts or current.artifacts[identifier].revision != revision:
                    raise SddError("TASK_CONTEXT_STALE", identifier, Status.STALE)
        result = check_snapshot(current, old)
        store.save_snapshot(current)
        task.update({"state": "validated" if result.status == Status.PASS else "needs_revision",
                     "finished_at": utc_now(), "output_snapshot": current.digest, "result": result.to_dict(),
                     "attestation": digest({"input": old.digest, "output": current.digest, "result": result.to_dict()})})
        store.write("tasks", task_id, task)
        return task
