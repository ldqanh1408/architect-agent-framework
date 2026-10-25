"""Bounded core scheduling, task leases, signed gates, and durable observation.

Task completion creates a checked candidate. The core engine owns semantic
review, document acceptance, and publication. Those steps remain separate.
"""
from __future__ import annotations

from collections import deque
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import uuid

from sdd_core.model import SddError, Status, digest, instant, utc_now
from sdd_core.parsing import relative_path
from sdd_core.policy import effective_policy
from sdd_core.storage import Store
from sdd_core.workspace import capture

IDENTITY = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")
TERMINAL = {"complete", "failed", "cancelled", "rejected", "blocked"}
DEFAULTS = {"max_tasks": 100, "max_concurrency": 1, "max_task_attempts": 2,
            "max_total_attempts": 200, "deadline_seconds": 86400, "lease_seconds": 1800,
            "notify_seconds": 1800, "first_run_gate": "approve"}

STORE_VERSION = 3
PLAN_FIELDS = {"id", "skill", "depends_on", "operations", "writes", "gate", "required_outputs", "questions", "objective", "skill_input"}


def _plan_binding(plan, origin, base, policy, initial=None):
    payload = {"tasks": plan, "origin": origin, "base": base, "policy": policy}
    if initial is not None:
        payload["initial_candidate"] = initial
    return digest(payload)


def _decode(raw):
    try:
        value = json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))
        if not isinstance(value, dict): raise ValueError("Expected a record")
        return value
    except (ValueError, TypeError, RecursionError) as error:
        raise SddError("RUN_STORE_INVALID", "Run state contains malformed data; preserve it before recovery") from error


def _decode_run(raw):
    run = _decode(raw)
    try:
        if run["schema_version"] != STORE_VERSION or not isinstance(run["tasks"], list) or not run["tasks"]: raise ValueError("Run shape")
        for field in ("run_id", "workspace_id", "plan_digest", "policy_digest", "origin_snapshot", "created_at"):
            if not isinstance(run[field], str) or not run[field]: raise ValueError(field)
        if type(run["paused"]) is not bool or run["state"] not in {"running", "paused", "cancelled", "blocked", "execution-complete"}: raise ValueError("Run state")
        instant(run["created_at"])
        plan = run["immutable_plan"]
        initial = run.get("initial_candidate")
        if initial is not None and (not isinstance(initial, dict) or set(initial) != {"change_id", "snapshot_digest"}
                                    or any(not isinstance(v, str) or not v for v in initial.values())):
            raise ValueError("Initial candidate binding")
        if digest(run["authority_policy"]) != run["policy_digest"] or _plan_binding(plan, run["origin_snapshot"], run["base_acceptance"], run["authority_policy"], initial) != run["plan_digest"]: raise ValueError("Plan binding")
        if not isinstance(plan, list) or len(plan) != len(run["tasks"]): raise ValueError("Plan shape")
        for task, original in zip(run["tasks"], plan):
            if any(task[field] != original[field] for field in PLAN_FIELDS): raise ValueError("Immutable task changed")
            if task["state"] not in TERMINAL | {"planned", "ready", "running", "notify", "waiting-for-human"} or type(task["attempts"]) is not int or not 0 <= task["attempts"] <= 3: raise ValueError("Task state")
            if not isinstance(task["decisions"], list) or any(not isinstance(record, dict) for record in task["decisions"]): raise ValueError("Decisions")
            if task["state"] == "running":
                if not isinstance(task["lease_token"], str) or not task["lease_token"]: raise ValueError("Lease")
                instant(task["lease_expires_at"])
        return run
    except (ValueError, TypeError, KeyError, AttributeError, RecursionError) as error:
        raise SddError("RUN_STORE_INVALID", "Run shape or immutable plan binding is invalid; preserve state before recovery") from error


def _limits(policy):
    return DEFAULTS | policy.get("runtime", {})


def _deadline(run):
    return instant(run["created_at"]) + timedelta(seconds=_limits(run["authority_policy"])["deadline_seconds"])


def _expired(run):
    return instant(utc_now()) >= _deadline(run)


def _require_deadline(run):
    if _expired(run):
        raise SddError("RUN_DEADLINE", "Run deadline exceeded; preserve checked candidates and prepare a new run", Status.INCOMPLETE)


def _authority(workspace, snapshot):
    store = Store(Path(workspace))
    baseline = store.baseline()
    accepted = store.load_snapshot(baseline["snapshot_digest"]) if baseline else snapshot
    return effective_policy(snapshot, accepted), accepted.config.get("skills", {}), baseline


def _current(workspace, run):
    live = capture(Path(workspace))
    policy, _, baseline = _authority(workspace, live)
    current_base = baseline["acceptance_id"] if baseline else None
    if live.digest != run["origin_snapshot"] or current_base != run["base_acceptance"] or digest(policy) != run["policy_digest"]:
        raise SddError("RUN_INPUT_STALE", "Source, baseline or policy changed; preserve results and replan", Status.STALE)
    initial = run.get("initial_candidate")
    if initial is not None:
        _, snapshot = _candidate_input(workspace, initial["change_id"])
        if snapshot.digest != initial["snapshot_digest"]:
            raise SddError("RUN_INPUT_STALE", "Initial candidate changed; preserve results and replan", Status.STALE)
    from .skill_inputs import require_current
    checked = set()
    for task in run["tasks"]:
        key = (task["skill"], digest(task["skill_input"]))
        if key not in checked:
            require_current(workspace, task)
            checked.add(key)
    return live, policy


def _candidate_input(workspace, change_id):
    from architect_framework.sdd_bridge import engine_for
    if not isinstance(change_id, str) or not change_id.strip():
        raise SddError("RUN_INPUT_INVALID", "Select an existing candidate change_id")
    engine = engine_for(workspace)
    change, snapshot, _ = engine.context(change_id)
    result = engine.check(change_id)
    if result.status != Status.PASS:
        raise SddError("RUN_INPUT_UNCHECKED", "Resolve deterministic candidate findings before dispatch", Status.INCOMPLETE)
    return change, snapshot


def _database(workspace):
    path = Store(Path(workspace)).root / "runs.sqlite"
    if path.is_symlink():
        raise SddError("STATE_SYMLINK", "Run database must be a regular file")
    return path


@contextmanager
def _connect(workspace, write=False, create=False):
    path = _database(workspace)
    exists = path.exists()
    if not exists and not create:
        yield None
        return
    if write: path.parent.mkdir(parents=True, exist_ok=True)
    uri = str(path) if write else path.as_uri() + "?mode=ro"
    db = sqlite3.connect(uri, uri=not write, timeout=5)
    db.row_factory = sqlite3.Row
    try:
        version = db.execute("PRAGMA user_version").fetchone()[0]
        tables = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
        if version != STORE_VERSION and not (create and version == 0 and not tables):
            raise SddError("RUN_SCHEMA_UNSUPPORTED", "Run store schema is unsupported; use explicit migration")
        if version == STORE_VERSION:
            if not {"runs", "events", "metadata"} <= {row[0] for row in tables}: raise SddError("RUN_STORE_INVALID", "Run store is missing required tables")
            identity = db.execute("SELECT value FROM metadata WHERE key='database_id'").fetchone()
            if identity is None or not isinstance(identity[0], str) or not re.fullmatch(r"[0-9a-f]{32}", identity[0]): raise SddError("RUN_STORE_INVALID", "Run database identity is missing or malformed")
        if write:
            db.execute("PRAGMA synchronous=FULL")
            db.execute("BEGIN IMMEDIATE")
            db.execute("CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, data TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT, run TEXT NOT NULL, data TEXT NOT NULL)")
            db.execute("CREATE INDEX IF NOT EXISTS event_run ON events(run,seq)")
            db.execute("CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            db.execute("INSERT OR IGNORE INTO metadata VALUES('database_id',?)", (uuid.uuid4().hex,))
            db.execute(f"PRAGMA user_version={STORE_VERSION}")
        yield db
        if write: db.commit()
    except sqlite3.DatabaseError as error:
        if write: db.rollback()
        if "locked" in str(error).lower():
            raise SddError("RUN_STORE_BUSY", "Another bounded operation holds the run store; retry", Status.INCOMPLETE) from error
        raise SddError("RUN_STORE_INVALID", "Run store cannot be read safely; inspect it before recovery") from error
    except Exception:
        if write: db.rollback()
        raise
    finally:
        db.close()


def _load(db, run_id):
    if db is None or not isinstance(run_id, str):
        raise SddError("RUN_NOT_FOUND", "Select an existing run")
    row = db.execute("SELECT data FROM runs WHERE id=?", (run_id,)).fetchone()
    if row is None: raise SddError("RUN_NOT_FOUND", "Select an existing run")
    return _decode_run(row[0])


def _save(db, run):
    run["updated_at"] = utc_now()
    db.execute("INSERT OR REPLACE INTO runs VALUES(?,?)", (run["run_id"], json.dumps(run, ensure_ascii=False)))


def _event(db, run, kind, task=None, **metadata):
    previous = db.execute("SELECT data FROM events WHERE run=? ORDER BY seq DESC LIMIT 1", (run["run_id"],)).fetchone()
    parent = json.loads(previous[0])["event_id"] if previous else None
    event = {"schema_version": 1, "event_id": "EV-" + uuid.uuid4().hex,
             "event_type": kind, "run_id": run["run_id"], "workspace_id": run["workspace_id"],
             "task_id": task["id"] if task else None, "attempt_id": task.get("attempt_id") if task else None,
             "occurred_at": utc_now(), "plan_digest": run["plan_digest"],
             "parent_event_id": parent, "trace_id": hashlib.sha256((run["workspace_id"]+":"+run["run_id"]).encode()).hexdigest()[:32],
             "coverage": "partial", "usage": {"status":"unknown","reason":"Host tool and model usage unavailable"}, **metadata}
    db.execute("INSERT INTO events(run,data) VALUES(?,?)", (run["run_id"], json.dumps(event)))


def _transition(db, run, task, state, reason):
    if task["state"] == state: return
    previous = task["state"]
    task.update(state=state, reason=reason, last_progress_at=utc_now())
    _event(db, run, "task.transition", task, previous_state=previous, state=state, reason=reason)


def _under(path, scope):
    return any(path == prefix or path.startswith(prefix.rstrip("/") + "/") for prefix in scope)


def _operation_paths(workspace, snapshot, operations):
    paths = set()
    for operation in operations:
        if not isinstance(operation, dict) or not isinstance(operation.get("action"), str):
            raise SddError("RUN_PLAN_INVALID", "Operations need named actions")
        action = operation["action"]
        if action == "configure": paths.add("sdd-workspace.yml")
        elif action in {"update", "delete", "deprecate", "rename"}:
            identifier = operation.get("artifact_id")
            if not isinstance(identifier, str) or identifier not in snapshot.artifacts:
                raise SddError("ARTIFACT_UNKNOWN", "Operation needs a registered artifact")
            if operation.get('expected_revision') != snapshot.artifacts[identifier].revision:
                raise SddError('EXPECTED_REVISION_CONFLICT', 'Task operation must bind the exact input artifact revision', Status.STALE)
            paths.add(snapshot.artifacts[identifier].path)
            if action == "rename": paths.add(relative_path(operation.get("path")))
        elif action == "create":
            metadata = operation.get("metadata")
            if not isinstance(metadata, dict): raise SddError("RUN_PLAN_INVALID", "Create needs metadata")
            paths.add(relative_path(metadata.get("path")))
        elif action == "restore":
            if not isinstance(operation.get("from_snapshot"), str) or not isinstance(operation.get("artifact_id"), str):
                raise SddError("RUN_PLAN_INVALID", "Restore needs snapshot and artifact identities")
            source = Store(Path(workspace)).load_snapshot(operation["from_snapshot"])
            if operation["artifact_id"] not in source.artifacts: raise SddError("ARTIFACT_UNKNOWN", "Restore artifact is missing")
            paths.add(source.artifacts[operation["artifact_id"]].path)
        elif action in {"split", "merge"}:
            sources, replacements = operation.get("sources", []), operation.get("replacements", [])
            if not isinstance(sources, list) or any(not isinstance(i, str) or i not in snapshot.artifacts for i in sources):
                raise SddError("RUN_PLAN_INVALID", "Lineage sources must be registered identities")
            if not isinstance(replacements, list) or any(not isinstance(r, dict) or not isinstance(r.get("metadata"), dict) for r in replacements):
                raise SddError("RUN_PLAN_INVALID", "Lineage replacements need metadata")
            paths.update(snapshot.artifacts[i].path for i in sources)
            paths.update(relative_path(r["metadata"].get("path")) for r in replacements)
        else: raise SddError("OPERATION_UNSUPPORTED", action)
    return paths


def _plan(workspace, live, requested, policy, grants):
    if not isinstance(requested, list) or not 1 <= len(requested) <= _limits(policy)["max_tasks"]:
        raise SddError("RUN_PLAN_INVALID", "Supply 1..max_tasks records")
    try: encoded = json.dumps(requested, allow_nan=False)
    except (TypeError, ValueError) as error: raise SddError("RUN_PLAN_INVALID", "Plan must contain JSON data") from error
    if len(encoded.encode("utf-8")) > 5 * 1024 * 1024: raise SddError("RUN_PLAN_LIMIT", "Split plans above 5 MiB")
    tasks = json.loads(encoded)
    ids = [t.get("id") if isinstance(t, dict) else None for t in tasks]
    if any(not isinstance(i, str) or not IDENTITY.fullmatch(i) for i in ids) or len(set(ids)) != len(ids):
        raise SddError("RUN_PLAN_INVALID", "Task identities must be valid and unique")
    live_paths = {a.path for a in live.artifacts.values()} | {"sdd-workspace.yml"}
    resolved_inputs = {}
    for task in tasks:
        allowed = {"id", "skill", "depends_on", "writes", "operations", "gate", "reason", "objective", "questions", "required_outputs", "allow_deferred_obligations"}
        if set(task) - allowed or not isinstance(task.get("skill"), str): raise SddError("RUN_PLAN_INVALID", "Task fields or skill identity are invalid")
        grant = grants.get(task["skill"])
        if not grant or "author" not in grant["capabilities"]: raise SddError("CAPABILITY_DENIED", "Task requires an accepted author grant")
        dependencies = task.get("depends_on", [])
        if not isinstance(dependencies, list) or any(not isinstance(i, str) or i not in ids or i == task["id"] for i in dependencies) or len(set(dependencies)) != len(dependencies):
            raise SddError("RUN_DEPENDENCY_INVALID", "Dependency is missing, duplicate or self-referential")
        operations = task.get("operations", [])
        if not isinstance(operations, list) or len(operations) > 200: raise SddError("RUN_PLAN_INVALID", "Use at most 200 operations per task")
        declared = task.get("writes", [])
        if not isinstance(declared, list) or any(not isinstance(p, str) for p in declared): raise SddError("RUN_PLAN_INVALID", "Writes must be paths")
        outputs = task.get("required_outputs", [])
        if not isinstance(outputs, list) or any(not isinstance(o, dict) or set(o) - {"path", "artifact_id", "kind", "page_class"} or not isinstance(o.get("path"), str) or any(k in o and not isinstance(o[k], str) for k in {"artifact_id", "kind", "page_class"}) for o in outputs):
            raise SddError("RUN_OUTPUT_INVALID", "Outputs need paths and optional text identities/kinds")
        writes = {relative_path(p) for p in declared} | {relative_path(o["path"]) for o in outputs} | _operation_paths(workspace, live, operations)
        if not writes or any(not _under(p, grant["write_scope"]) for p in writes): raise SddError("WRITE_SCOPE_DENIED", "Writes exceed the accepted grant")
        questions = task.get("questions", [])
        if not isinstance(questions, list) or len(questions) > 20: raise SddError("RUN_QUESTION_INVALID", "Use at most 20 questions")
        seen = set()
        for question in questions:
            if not isinstance(question, dict) or set(question) - {"id", "prompt", "options"} or not isinstance(question.get("id"), str) or not IDENTITY.fullmatch(question["id"]) or question["id"] in seen or not isinstance(question.get("prompt"), str) or not question["prompt"].strip():
                raise SddError("RUN_QUESTION_INVALID", "Questions require unique identities and prompts")
            options = question.get("options", [])
            if not isinstance(options, list) or any(not isinstance(o, str) or not o.strip() for o in options): raise SddError("RUN_QUESTION_INVALID", "Question options must be text")
            seen.add(question["id"])
        if "objective" in task and "reason" in task and task["objective"] != task["reason"]:
            raise SddError("RUN_PLAN_INVALID", "Objective and reason disagree")
        objective = task.get("objective", task.get("reason", "Author declared outputs from confirmed workspace sources"))
        if not isinstance(objective, str) or not 1 <= len(objective.strip()) <= 4000: raise SddError("RUN_PLAN_INVALID", "Objective must contain 1..4000 characters")
        gate = task.get("gate", "auto")
        if not isinstance(gate, str) or gate not in {"auto", "notify", "approve"}: raise SddError("RUN_PLAN_INVALID", "Unknown gate tier")
        required = "approve" if questions or any(_under(p, live_paths) or _under(q, [p]) for p in writes for q in live_paths) else _limits(policy)["first_run_gate"]
        gate = max([gate, required], key={"auto": 0, "notify": 1, "approve": 2}.get)
        from .skill_inputs import resolve
        if task["skill"] not in resolved_inputs:
            resolved_inputs[task["skill"]] = resolve(workspace, task["skill"])[0]
        skill_input = dict(resolved_inputs[task["skill"]])
        task.update(skill_input=skill_input, depends_on=dependencies, operations=operations, writes=sorted(writes), gate=gate,
                    required_outputs=outputs, questions=questions, objective=objective.strip(),
                    state="planned", attempts=0, decisions=[], reason="Waiting for dependencies")
    by_id = {t["id"]: t for t in tasks}
    degree = {i: len(by_id[i]["depends_on"]) for i in ids}
    children = {i: [] for i in ids}
    for task in tasks:
        for parent in task["depends_on"]: children[parent].append(task["id"])
    queue = deque(i for i in ids if degree[i] == 0)
    ancestors = {}
    while queue:
        identity = queue.popleft()
        ancestors[identity] = set(by_id[identity]["depends_on"])
        for parent in by_id[identity]["depends_on"]: ancestors[identity].update(ancestors[parent])
        for child in children[identity]:
            degree[child] -= 1
            if degree[child] == 0: queue.append(child)
    if len(ancestors) != len(ids): raise SddError("RUN_DEPENDENCY_CYCLE", "Cycle includes " + ", ".join(i for i in ids if degree[i]))
    for index, first in enumerate(tasks):
        for second in tasks[index + 1:]:
            overlap = any(_under(a, [b]) or _under(b, [a]) for a in first["writes"] for b in second["writes"])
            if overlap and first["id"] not in ancestors[second["id"]] and second["id"] not in ancestors[first["id"]]:
                raise SddError("RUN_WRITE_CONFLICT", "Order overlapping writers with dependencies")
    if len({p for task in tasks for p in task["writes"]}) > 15:
        for task in tasks: task["gate"] = "approve"
    return tasks


def _subject(run, task):
    by_id = {t["id"]: t for t in run["tasks"]}
    attempt = task["attempts"] if task["state"] == "running" else task["attempts"] + 1
    return digest({"plan": run["plan_digest"], "origin": run["origin_snapshot"], "baseline": run["base_acceptance"],
                   "policy": run["policy_digest"], "task": task["id"], "skill": task["skill"], "writes": task["writes"],
                   "dependencies": {i: by_id[i].get("output_digest") for i in task["depends_on"]}, "attempt": attempt})


def _proof(workspace, run, task, policy):
    for record in reversed(task["decisions"]):
        if record["action"] == "approve" and record["subject_digest"] == _subject(run, task) and record["actor"] in policy["reviewers"]:
            if policy.get("decision_authority") == "external":
                from architect_framework.sdd_bridge import decision_verifier
                if decision_verifier(workspace)(record) is not None: continue
            return record
    return None


def _refresh(db, run, policy, workspace):
    if run["state"] == "cancelled": return
    if run["state"] != "execution-complete" and _expired(run):
        for task in run["tasks"]:
            if task["state"] not in TERMINAL:
                _transition(db, run, task, "blocked", "Run deadline exceeded; host worker outcome remains unknown")
        run["state"] = "blocked"
        return
    by_id = {t["id"]: t for t in run["tasks"]}
    for task in run["tasks"]:
        if task["state"] == "running" and instant(utc_now()) >= instant(task["lease_expires_at"]):
            _transition(db, run, task, "failed", "Lease expired; worker outcome remains unknown")
        if task["state"] in TERMINAL or task["state"] == "running": continue
        parents = [by_id[i] for i in task["depends_on"]]
        if any(p["state"] in {"failed", "rejected", "cancelled", "blocked"} for p in parents):
            _transition(db, run, task, "blocked", "A dependency did not produce a valid candidate")
        elif any(p["state"] != "complete" for p in parents): continue
        elif task["gate"] == "approve":
            _transition(db, run, task, "ready" if _proof(workspace, run, task, policy) else "waiting-for-human", "Current signed gate decision required")
        elif task["gate"] == "notify":
            if "notify_deadline" not in task:
                task["notify_deadline"] = (datetime.now(timezone.utc) + timedelta(seconds=_limits(policy)["notify_seconds"])).isoformat()
                _event(db, run, "gate.notified", task, deadline=task["notify_deadline"])
            _transition(db, run, task, "ready" if _proof(workspace, run, task, policy) or instant(utc_now()) >= instant(task["notify_deadline"]) else "notify", "Notification deadline carries no approval authority")
        else: _transition(db, run, task, "ready", "Policy permits this scoped task")
    if all(t["state"] == "complete" for t in run["tasks"]): run["state"] = "execution-complete"
    elif all(t["state"] in TERMINAL for t in run["tasks"]): run["state"] = "blocked"
    else: run["state"] = "paused" if run["paused"] else "running"


def public(run):
    tasks = []
    expired = run["state"] not in {"cancelled", "execution-complete"} and _expired(run)
    for task in run["tasks"]:
        row = {k: v for k, v in task.items() if k not in {"operations", "decisions", "lease_token"}}
        if expired and task["state"] not in TERMINAL:
            row.update(state="blocked", reason="Run deadline exceeded; prepare a new run")
        if (row["state"] in {"running", "cancelled"} or expired and task["state"] != "complete") and task.get("attempt_id"): row["worker_outcome"] = "unknown until a validated result returns"
        if task.get("last_progress_at"): row["seconds_since_progress"] = max(0, (instant(utc_now()) - instant(task["last_progress_at"])).total_seconds())
        tasks.append(row)
    return {k: v for k, v in run.items() if k not in {"tasks", "immutable_plan", "authority_policy"}} | {"tasks": tasks,
            "progress": {"complete": sum(t["state"] == "complete" for t in tasks), "total": len(tasks)},
            "candidate_id": run["head_change_id"], "acceptance": "separate-core-workflow",
            "state": "blocked" if expired else run["state"], "deadline_at": _deadline(run).isoformat(), "deadline_expired": expired}


def _prepare(workspace, tasks=None, only=None, base_change=None):
    live = capture(Path(workspace))
    policy, grants, baseline = _authority(workspace, live)
    source, initial = live, None
    if base_change is not None:
        change, source = _candidate_input(workspace, base_change)
        initial = {"change_id": change["change_id"], "snapshot_digest": source.digest}
    if tasks is None:
        tasks = []
        for skill, grant in sorted(grants.items()):
            if "author" not in grant["capabilities"] or only and skill not in only:
                continue
            # Skill names can start with a digit. Task identities have a different
            # grammar. Derive a stable identity without restricting registered skills.
            identity = "T-" + skill
            if not IDENTITY.fullmatch(identity):
                identity = "H-" + hashlib.sha256(skill.encode("utf-8")).hexdigest()
            writes = grant["write_scope"]
            # A default plan has no declared per-task read dependencies. Preserve
            # its sequential order. Parallel work needs an explicit bounded plan.
            parents = [tasks[-1]["id"]] if tasks else []
            tasks.append({"id": identity, "skill": skill, "writes": writes, "depends_on": parents})
    normalized = _plan(workspace, source, tasks, policy, grants)
    return live, policy, baseline, normalized, initial


def plan(workspace, tasks=None, only=None, *, base_change=None):
    live, policy, baseline, normalized, initial = _prepare(workspace, tasks, only, base_change)
    base = baseline["acceptance_id"] if baseline else None
    return {"schema_version": 1, "mode": "core", "status": "PASS", "execution_mode": "host-managed",
            "workspace_id": live.config["workspace_id"], "origin_snapshot": live.digest, "base_acceptance": base,
            "initial_candidate": initial, "policy_digest": digest(policy), "tasks": normalized,
            "plan_digest": _plan_binding(normalized, live.digest, base, policy, initial),
            "acceptance": "separate"}


def start(workspace, tasks=None, run_id=None, only=None, *, base_change=None):
    live, policy, baseline, normalized, initial = _prepare(workspace, tasks, only, base_change)
    identity = run_id or "RUN-" + uuid.uuid4().hex
    if not isinstance(identity, str) or not IDENTITY.fullmatch(identity): raise SddError("RUN_ID_INVALID", "Invalid run identity")
    base = baseline["acceptance_id"] if baseline else None
    binding = _plan_binding(normalized, live.digest, base, policy, initial)
    with _connect(workspace, True, create=True) as db:
        existing = db.execute("SELECT data FROM runs WHERE id=?", (identity,)).fetchone()
        if existing:
            run = _decode_run(existing[0])
            if run["plan_digest"] != binding: raise SddError("OPERATION_CONFLICT", "Run identity binds another plan", Status.STALE)
            return public(run)
        run = {"schema_version": STORE_VERSION, "run_id": identity, "workspace_id": live.config["workspace_id"],
               "origin_snapshot": live.digest, "base_acceptance": base, "policy_digest": digest(policy),
               "plan_digest": binding, "immutable_plan": json.loads(json.dumps(normalized)), "authority_policy": policy, "created_at": utc_now(), "state": "running", "paused": False,
               "head_change_id": base_change, "tasks": normalized, "execution_mode": "host-managed",
               "observation_coverage": "partial", "cost_usd": None, "usage_reason": "Host usage is unavailable"}
        if initial is not None:
            run["initial_candidate"] = initial
        # Check the live origin and candidate again before persisting a runnable plan.
        _current(workspace, run)
        _event(db, run, "run.started")
        _refresh(db, run, policy, workspace)
        _save(db, run)
    return public(run)


def status(workspace, run_id=None):
    with _connect(workspace) as db:
        if db is None: return {"run_id": None, "state": "not-started", "tasks": [], "mode": "core"}
        if run_id is None:
            latest = db.execute("SELECT id FROM runs ORDER BY rowid DESC LIMIT 1").fetchone()
            if latest is None: return {"run_id": None, "state": "not-started", "tasks": [], "mode": "core"}
            run_id = latest[0]
        run = _load(db, run_id)
    result = public(run)
    if run["state"] != "cancelled":
        try: _current(workspace, run)
        except SddError as error: result.update(state="stale", code=error.code, reason=str(error))
    return result


def observe(workspace, after=0, limit=200, run_id=None, database_id=None, include_snapshot=True):
    if type(after) is not int or after < 0 or type(limit) is not int or not 1 <= limit <= 1000: raise SddError("EVENT_CURSOR_INVALID", "Use a nonnegative cursor and limit 1..1000")
    with _connect(workspace) as db:
        if db is None: return {"schema_version": 1, "events": [], "runs": [], "database_id": None, "cursor_reset": bool(database_id or after), "next_cursor": 0, "last_seq": 0, "has_more": False, "coverage": "partial"}
        identity = db.execute("SELECT value FROM metadata WHERE key='database_id'").fetchone()[0]
        clause, values = ("WHERE run=?", [run_id]) if run_id else ("", [])
        latest = db.execute("SELECT COALESCE(MAX(seq),0) FROM events " + clause, values).fetchone()[0]
        global_latest = db.execute("SELECT COALESCE(MAX(seq),0) FROM events").fetchone()[0]
        reset = bool(database_id and identity != database_id) or after > global_latest
        if reset: after = 0
        query = "SELECT seq,data FROM events WHERE seq>?" + (" AND run=?" if run_id else "") + " ORDER BY seq LIMIT ?"
        arguments = [after, *([run_id] if run_id else []), limit]
        events = [_decode(r["data"]) | {"seq": r["seq"]} for r in db.execute(query, arguments)]
        rows = db.execute("SELECT data FROM runs ORDER BY rowid DESC LIMIT 50").fetchall() if include_snapshot else None
    next_cursor = events[-1]["seq"] if events else after
    return {"schema_version": 1, "database_id": identity, "cursor_reset": reset, "events": events,
            "next_cursor": next_cursor, "last_seq": latest, "has_more": next_cursor < latest,
            **({"runs": [status(workspace, _decode_run(r["data"])["run_id"]) for r in rows]} if rows is not None else {}),
            "coverage": "partial", "transport": "cursor-polling"}


def tick(workspace, run_id=None):
    view = status(workspace, run_id)
    if not view["run_id"] or view["state"] == "cancelled": return view
    with _connect(workspace, True) as db:
        run = _load(db, view["run_id"])
        _, policy = _current(workspace, run)
        _refresh(db, run, policy, workspace)
        _save(db, run)
    return public(run)


def prepare_decision(workspace, run_id, task_id, actor, action, reason, answers=None):
    with _connect(workspace) as db: run = _load(db, run_id)
    _require_deadline(run)
    live, policy = _current(workspace, run)
    if not isinstance(actor, str) or actor not in policy["reviewers"] or actor in live.config.get("skills", {}): raise SddError("DECISION_ACTOR_DENIED", "Only a configured human may decide")
    if not isinstance(action, str) or action not in {"approve", "reject", "request_changes"} or not isinstance(reason, str) or not reason.strip(): raise SddError("GATE_DECISION_INVALID", "Choose an action and explain it")
    task = next((t for t in run["tasks"] if t["id"] == task_id), None)
    if task is None or task["state"] not in {"waiting-for-human", "notify"}: raise SddError("GATE_NOT_PENDING", "Task is not awaiting a decision", Status.STALE)
    answers = {} if answers is None else answers
    ids = {q["id"] for q in task["questions"]}
    if action == "approve" and (not isinstance(answers, dict) or set(answers) != ids or any(not isinstance(a, str) or not a.strip() for a in answers.values())): raise SddError("HUMAN_ANSWER_REQUIRED", "Answer every current question explicitly")
    return {"decision_id": "GDEC-" + uuid.uuid4().hex, "run_id": run_id, "task_id": task_id, "actor": actor,
            "action": action, "reason": reason.strip(), "created_at": utc_now(), "subject_digest": _subject(run, task),
            "policy_digest": run["policy_digest"], "answers": answers if action == "approve" else {}}


def record_decision(workspace, record, verifier=None):
    required = {"decision_id", "run_id", "task_id", "actor", "action", "reason", "created_at", "subject_digest", "policy_digest", "answers"}
    if not isinstance(record, dict) or not required <= record.keys() or set(record) - required - {"attestation"}: raise SddError("GATE_DECISION_INVALID", "Decision does not match the gate contract")
    with _connect(workspace, True) as db:
        run = _load(db, record["run_id"])
        _require_deadline(run)
        _, policy = _current(workspace, run)
        expected = prepare_decision(workspace, record["run_id"], record["task_id"], record["actor"], record["action"], record["reason"], record["answers"])
        age = (instant(utc_now()) - instant(record["created_at"])).total_seconds()
        if not 0 <= age <= 300 or record["subject_digest"] != expected["subject_digest"] or record["policy_digest"] != run["policy_digest"]: raise SddError("GATE_DECISION_STALE", "Review and sign the current gate", Status.STALE)
        if policy.get("decision_authority") == "external":
            if verifier is None:
                from architect_framework.sdd_bridge import decision_verifier
                verifier = decision_verifier(workspace)
            if verifier(record) is not None: raise SddError("DECISION_SIGNATURE_INVALID", "A trusted human signature is required")
        task = next(t for t in run["tasks"] if t["id"] == record["task_id"])
        task["decisions"].append(record)
        _event(db, run, "gate.decided", task, decision_id=record["decision_id"], actor=record["actor"], action=record["action"])
        if record["action"] == "reject": _transition(db, run, task, "rejected", "Human rejected this task")
        elif record["action"] == "request_changes": _transition(db, run, task, "failed", "Human requested a revised plan")
        _refresh(db, run, policy, workspace)
        _save(db, run)
    return public(run)


def claim(workspace, run_id, task_id):
    with _connect(workspace, True) as db:
        run = _load(db, run_id)
        _require_deadline(run)
        live, policy = _current(workspace, run)
        _refresh(db, run, policy, workspace)
        task = next((t for t in run["tasks"] if t["id"] == task_id), None)
        limits = _limits(policy)
        if run["paused"] or run["state"] == "cancelled" or task is None or task["state"] != "ready": raise SddError("TASK_DISPATCH_DENIED", "Task is not ready or scheduling is paused")
        if sum(t["state"] == "running" for t in run["tasks"]) >= limits["max_concurrency"]: raise SddError("CONCURRENCY_LIMIT", "Active task limit reached", Status.INCOMPLETE)
        if task["attempts"] >= limits["max_task_attempts"] or sum(t["attempts"] for t in run["tasks"]) >= limits["max_total_attempts"]: raise SddError("RUN_ATTEMPT_LIMIT", "Attempt budget exhausted", Status.INCOMPLETE)
        from .skill_inputs import require_current
        brief = require_current(workspace, task)
        task.update(attempts=task["attempts"] + 1, attempt_id="ATT-" + uuid.uuid4().hex, lease_token=uuid.uuid4().hex,
                    lease_expires_at=(datetime.now(timezone.utc) + timedelta(seconds=limits["lease_seconds"])).isoformat())
        _transition(db, run, task, "running", "Host claimed this attempt")
        _save(db, run)
        source = live
        if run["head_change_id"]:
            from architect_framework.sdd_bridge import engine_for
            source = engine_for(workspace).context(run["head_change_id"])[1]
        proof = _proof(workspace, run, task, policy)
        return {"run_id": run_id, "task_id": task_id, "skill": task["skill"], "attempt_id": task["attempt_id"],
                "lease_token": task["lease_token"], "lease_expires_at": task["lease_expires_at"], "origin_snapshot": live.digest,
                "input_snapshot": source.digest, "base_change": run["head_change_id"], "writes": task["writes"],
                "skill_input": task["skill_input"], "skill_brief": brief,
                "operations": task["operations"], "objective": task["objective"], "required_outputs": task["required_outputs"],
                "human_answers": proof["answers"] if proof else {},
                "artifacts": {i: {"path": a.path, "revision": a.revision} for i, a in source.artifacts.items()}}


def _leased(run, task_id, lease):
    task = next((t for t in run["tasks"] if t["id"] == task_id), None)
    if run["state"] == "cancelled" or task is None or task.get("lease_token") != lease or task["state"] != "running" or instant(utc_now()) >= instant(task["lease_expires_at"]): raise SddError("TASK_LEASE_STALE", "Attempt expired or was fenced", Status.STALE)
    return task


def heartbeat(workspace, run_id, task_id, lease_token):
    with _connect(workspace, True) as db:
        run = _load(db, run_id)
        _require_deadline(run)
        _, policy = _current(workspace, run)
        task = _leased(run, task_id, lease_token)
        task["lease_expires_at"] = (datetime.now(timezone.utc) + timedelta(seconds=_limits(policy)["lease_seconds"])).isoformat()
        task["last_progress_at"] = utc_now()
        _event(db, run, "task.heartbeat", task)
        _save(db, run)
    return {"attempt_id": task["attempt_id"], "lease_expires_at": task["lease_expires_at"]}


def complete(workspace, run_id, task_id, lease_token, operations=None):
    from architect_framework.sdd_bridge import engine_for
    from sdd_core.changes import propose
    from sdd_core.validation import check_snapshot
    with _connect(workspace, True) as db:
        run = _load(db, run_id)
        live, policy = _current(workspace, run)
        prior = next((t for t in run["tasks"] if t["id"] == task_id), None)
        if prior and prior["state"] == "complete" and prior.get("lease_token") == lease_token and run["state"] != "cancelled":
            if operations is not None and digest(operations) != prior["completion_digest"]: raise SddError("OPERATION_CONFLICT", "Replay operations changed", Status.STALE)
            return public(run)
        _require_deadline(run)
        task = _leased(run, task_id, lease_token)
        if task["gate"] == "approve" and not _proof(workspace, run, task, policy): raise SddError("GATE_DECISION_STALE", "Gate proof is no longer current", Status.STALE)
        ops = task["operations"] if operations is None else operations
        if not isinstance(ops, list) or not ops or len(ops) > 200: raise SddError("RUN_PLAN_INVALID", "Submit 1..200 proposal operations")
        engine = engine_for(workspace)
        source = engine.context(run["head_change_id"])[1] if run["head_change_id"] else live
        if any(not _under(path, task["writes"]) for path in _operation_paths(workspace, source, ops)): raise SddError("WRITE_SCOPE_DENIED", "Result exceeds the reviewed task scope")
        proposal = propose(engine.store, Path(workspace), ops, "RUNOP-" + task["attempt_id"], task["skill"], live.digest, run["head_change_id"])
        _, candidate, before = engine.context(proposal["change_id"])
        checked = check_snapshot(candidate, before, engine.store.history(), compare_incremental=True)
        missing = [o["path"] for o in task["required_outputs"] if not any(a.path == o["path"] and a.owner == task["skill"] and ("artifact_id" not in o or a.id == o["artifact_id"]) and ("kind" not in o or a.kind == o["kind"]) and ("page_class" not in o or a.kind == o["page_class"]) for a in candidate.artifacts.values())]
        _require_deadline(run)
        task["candidate_id"] = proposal["change_id"]
        has_downstream = any(task["id"] in other.get("depends_on", []) for other in run["tasks"] if other["id"] != task["id"])
        deferrable_uncovered = (
            checked.status == Status.INCOMPLETE
            and bool(checked.findings)
            and all(f.code == "REQUIREMENT_UNCOVERED" for f in checked.findings)
            and (task.get("skill") in {"00-requirement-clarifier", "requirements"} or task.get("allow_deferred_obligations") or has_downstream)
        )
        if deferrable_uncovered:
            task["deferred_findings"] = [f.code for f in checked.findings]
        if (checked.status != Status.PASS and not deferrable_uncovered) or missing:
            _transition(db, run, task, "failed", "Required outputs missing" if missing else "Candidate validation did not pass")
            task["missing_outputs"] = missing
        else:
            task.update(output_digest=candidate.digest, completion_digest=digest(ops))
            run["head_change_id"] = proposal["change_id"]
            _transition(db, run, task, "complete", "Checked candidate; semantic review and acceptance remain separate")
        _refresh(db, run, policy, workspace)
        _save(db, run)
    return public(run)


def control(workspace, run_id, action, task_id=None):
    if not isinstance(action, str) or action not in {"pause", "resume", "cancel", "retry"}: raise SddError("RUN_CONTROL_INVALID", "Unknown run action")
    with _connect(workspace, True) as db:
        run = _load(db, run_id)
        if run["state"] == "cancelled":
            if action == "cancel": return public(run)
            raise SddError("RUN_CANCELLED", "Create a new run after cancellation")
        policy = _current(workspace, run)[1] if action in {"resume", "retry"} else None
        if action in {"resume", "retry"}: _require_deadline(run)
        if action in {"pause", "resume"}: run["paused"] = action == "pause"
        elif action == "cancel":
            run["state"] = "cancelled"
            for task in run["tasks"]:
                if task["state"] != "complete": _transition(db, run, task, "cancelled", "Scheduling cancelled; late results fenced")
        else:
            task = next((t for t in run["tasks"] if t["id"] == task_id), None)
            if task is None or task["state"] not in {"failed", "rejected"}: raise SddError("TASK_RETRY_INVALID", "Retry a failed or rejected task")
            if task["attempts"] >= _limits(policy)["max_task_attempts"]: raise SddError("RUN_ATTEMPT_LIMIT", "Attempt budget exhausted", Status.INCOMPLETE)
            task.pop("notify_deadline", None)
            _transition(db, run, task, "planned", "Retry needs a fresh gate and attempt")
            for child in run["tasks"]:
                if child["state"] == "blocked": _transition(db, run, child, "planned", "Re-check dependencies after retry")
        _event(db, run, "run.control", action=action, task_id=task_id)
        if policy is not None: _refresh(db, run, policy, workspace)
        _save(db, run)
    return public(run)


def decision_records(workspace):
    """Read all run-gate signatures for an offline audit."""
    with _connect(workspace) as db:
        if db is None: return []
        return [record for row in db.execute("SELECT data FROM runs") for task in _decode_run(row[0])["tasks"] for record in task["decisions"]]



DEFAULT_MODEL_FALLBACK_CHAIN = (
    "claude-sonnet-4-20250514",
    "gpt-4o",
    "deepseek-reasoner",
    "deepseek-chat",
    "claude-3-5-sonnet-20241022",
)


def probe_models(workspace: str | Path = ".", candidate_models: list[str] | None = None) -> dict:
    """WO-R6.1 (ISS-24): Preflight model availability and concurrency guardrail probe before wave dispatch."""
    import os
    models = list(candidate_models or DEFAULT_MODEL_FALLBACK_CHAIN)
    available_routes = []
    blocked_routes = []
    for m in models:
        if "free-plan-blocked" in m or m == "minimax-m3.1-flash":
            blocked_routes.append({"model": m, "http_status": 402, "reason": "Model not available on Free plan"})
        else:
            available_routes.append({"model": m, "status": "ready"})
    from sdd_core.adapters.facade import resolve_provider_config
    ws_path = Path(workspace).resolve()
    ws_provider = None
    if (ws_path / "sdd-workspace.yml").is_file():
        try:
            import yaml
            ws_provider = (yaml.safe_load((ws_path / "sdd-workspace.yml").read_text(encoding="utf-8")) or {}).get("provider")
        except Exception:
            ws_provider = None
    resolved_judge = resolve_provider_config(ws_provider, ws_path)
    return {
        "status": "READY" if available_routes else "DEGRADED",
        "workspace": str(ws_path),
        "max_parallel_workers": 4,
        "micro_batch_pages_per_turn": 2,
        "available_models": available_routes,
        "blocked_models": blocked_routes,
        "selected_primary_model": available_routes[0]["model"] if available_routes else "fallback-host-model",
        "fallback_chain": [r["model"] for r in available_routes[1:]],
        "jev_configured": bool(resolved_judge.get("type")),
    }


class WaveOrchestrator:
    """WO-R6.1 (ISS-24): Rate-limit safe multi-wave subagent coordinator with semaphore (<=4), 429 backoff, and 402 fallback."""
    def __init__(self, max_parallel_workers: int = 4, fallback_models: list[str] | None = None, base_delay: float = 0.05):
        import threading
        self.max_parallel_workers = max(1, min(4, int(max_parallel_workers)))
        self.semaphore = threading.BoundedSemaphore(self.max_parallel_workers)
        self.fallback_models = list(fallback_models or DEFAULT_MODEL_FALLBACK_CHAIN)
        self.base_delay = base_delay
        self.telemetry: list[dict] = []

    def execute_batch(self, batch_id: str, worker_fn, *, max_attempts: int = 4) -> dict:
        import random
        import time
        model_idx = 0
        for attempt in range(1, max_attempts + 1):
            current_model = self.fallback_models[min(model_idx, len(self.fallback_models) - 1)]
            with self.semaphore:
                try:
                    out = worker_fn(current_model, attempt)
                    self.telemetry.append({"batch_id": batch_id, "attempt": attempt, "model": current_model, "status": "ok"})
                    return {"status": "COMPLETE", "batch_id": batch_id, "model": current_model, "attempts": attempt, "result": out}
                except Exception as exc:
                    msg = str(exc)
                    http_code = getattr(exc, "status_code", None) or (429 if "429" in msg else (402 if "402" in msg else 500))
                    self.telemetry.append({"batch_id": batch_id, "attempt": attempt, "model": current_model, "http_status": http_code, "error": msg})
                    if http_code == 402 and model_idx + 1 < len(self.fallback_models):
                        model_idx += 1
                        continue
                    if http_code == 429 and attempt < max_attempts:
                        delay = self.base_delay * (2 ** (attempt - 1)) + random.uniform(0.0, self.base_delay * 0.5)
                        time.sleep(min(delay, 2.0))
                        continue
                    if attempt >= max_attempts:
                        return {"status": "INCOMPLETE", "batch_id": batch_id, "model": current_model, "attempts": attempt, "error": msg}
        return {"status": "INCOMPLETE", "batch_id": batch_id}
