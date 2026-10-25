"""Revision-bound candidate language evidence and bounded host-authored repairs.

Live calls are explicit. Reports never qualify, sign, accept or publish a draft.
"""
import hashlib
import time
import uuid
from pathlib import Path

from . import BridgeError, engine_for, propose
from architect_framework.document_style import PROFILE, evaluate, protected_facts
from architect_framework.style_review import assess_jev, digest as glossary_digest, meaning_jev

_NON_PROSE_KINDS = frozenset({"source_manifest", "concern_inventory", "target_plan", "planning", "source"})


def _is_prose_document(artifact) -> bool:
    """WO-R4.4 (ISS-15): Filter out JSON/YAML machine artifacts and huge planning ledgers from language review."""
    if artifact.kind in _NON_PROSE_KINDS:
        return False
    path = str(artifact.path or "").lower()
    if path.endswith((".json", ".yml", ".yaml")):
        return False
    return True


def binding(snapshot, workspace=None):
    from sdd_core.evaluation import provider_binding
    from sdd_core.model import digest
    root = Path(__file__).resolve().parents[1]
    code = {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in ["style_review.py", "document_style.py", "sdd_bridge/language.py"]}
    provider_cfg = snapshot.config.get("provider") or {}
    if workspace is not None and not provider_cfg:
        from sdd_core.adapters.facade import resolve_provider_config
        provider_cfg = resolve_provider_config(provider_cfg, workspace)
    return digest({"snapshot": snapshot.digest, "language": snapshot.config.get("language", {}),
                   "profile": PROFILE, "provider": provider_binding(provider_cfg), "code": code})


def latest(engine, change, snapshot):
    from sdd_core.model import instant, utc_now
    expected = binding(snapshot)
    now = instant(utc_now())
    rows = []
    for row in engine.store.list("language_jobs"):
        if (row.get("change_id") != change["change_id"] or row.get("binding") != expected
                or row.get("base_acceptance") != change["base_acceptance"]): continue
        try: age = (now - instant(row["finished_at"])).total_seconds()
        except (ValueError, KeyError): continue
        if 0 <= age < snapshot.config["policy"].get("max_review_age_seconds", 30 * 86400): rows.append(row)
    return max(rows, key=lambda row: row.get("sequence", 0), default=None)


def _safe_calls(calls):
    safe = [{key: value for key, value in call.items() if key in {
        "stage", "attempt", "reserved_usd", "status", "http_status", "latency_seconds", "model"}} for call in calls]
    for target, source in zip(safe, calls):
        usage = source.get("usage")
        target["usage"] = {key: value for key, value in usage.items() if key in {"input_tokens", "output_tokens", "prompt_tokens", "completion_tokens"}
                           and type(value) is int and value >= 0} if isinstance(usage, dict) else None
    return safe


def review(workspace, change_id, *, live=False, force=False, transport=None, cancel=None, timeout=120):
    from sdd_core.adapters.typed_jev import JevSession
    from sdd_core.budget import Budget, candidate_root
    from sdd_core.model import SddError, Status, digest, utc_now
    engine = engine_for(workspace)
    change, snapshot, before = engine.context(change_id)
    expected = binding(snapshot)
    with engine.store.lock("language-" + change_id):
        previous = latest(engine, change, snapshot)
        if previous and previous.get("execution_status") == "COMPLETE" and previous.get("live") == live and not force:
            return {**previous, "reused": True}
        from sdd_core.adapters.facade import resolve_provider_config
        config = resolve_provider_config(snapshot.config.get("provider"), workspace)
        budget = Budget(engine.store, candidate_root(engine.store, change), config.get("max_cost_usd", 0))
        glossary = snapshot.config.get("language", {}).get("glossary", {})
        prof_digest = evaluate("")["profile_digest"]
        gloss_digest = glossary_digest(glossary)
        identity = "LANG-" + uuid.uuid4().hex
        with engine.store.lock():
            sequence = 1 + max((row.get("sequence", 0) for row in engine.store.list("language_jobs")), default=0)
            result = {"job_id": identity, "kind": "candidate-language-review", "change_id": change_id,
                "snapshot_digest": snapshot.digest, "base_acceptance": change["base_acceptance"], "binding": expected,
                "profile_digest": prof_digest, "glossary_digest": gloss_digest,
                "sequence": sequence, "live": live, "execution_status": "RUNNING", "status": "INCOMPLETE",
                "started_at": utc_now(), "artifacts": [], "qualified": False, "approval_authority": False, "published": False}
            engine.store.write("language_jobs", identity, result)
        # WO-R4.4 (ISS-15): Filter out non-prose artifacts (ledgers/JSON) when workspace has prose docs
        prose_artifacts = [a for a in sorted(snapshot.artifacts.values(), key=lambda artifact: artifact.id) if _is_prose_document(a)]
        if not prose_artifacts:
            prose_artifacts = sorted(snapshot.artifacts.values(), key=lambda artifact: artifact.id)
        documents = [{"artifact_id": artifact.id, "revision": artifact.revision, "text": artifact.text}
                     for artifact in prose_artifacts]
        all_calls = []
        try:
            max_docs = snapshot.config.get("policy", {}).get("max_workspace_documents", 512)
            max_bytes = 50_000 if len(documents) <= 32 else snapshot.config.get("policy", {}).get("max_file_bytes", 250_000)
            if len(documents) > max_docs or any(len(document["text"].encode()) > max_bytes for document in documents):
                raise SddError("CONTEXT_LIMIT", f"Language review supports {max_docs} complete documents of at most 50,000 bytes each", Status.INCOMPLETE)
            if live and config.get("type") not in {"typesafe-jev", "openai-compatible"}:
                raise SddError("PROVIDER_NOT_CONFIGURED", "Configure typesafe-jev or set JEV_API_KEY / SDD_JUDGE_API_KEY in .env before live language review", Status.INCOMPLETE)
            repairs, cursor = {}, change
            for _ in range(128):
                record = engine.store.read("language_repairs", cursor["change_id"])
                if record:
                    prior = repairs.get(record["artifact_id"], record)
                    repairs[record["artifact_id"]] = {**record, "round": prior["round"]}
                if not cursor.get("parent_change"): break
                cursor = engine.store.read("changes", cursor["parent_change"])
            is_large_workspace = len(documents) > 32
            for document in documents:
                repair_record = repairs.get(document["artifact_id"])
                text = document["text"]
                local = evaluate(text)
                # WO-R4.4 (ISS-16): Never duplicate the current document as its own related_documents
                ctx_docs = documents if not is_large_workspace else None
                cache_id = digest({
                    "artifact_id": document["artifact_id"],
                    "revision": document["revision"],
                    "profile_digest": prof_digest,
                    "glossary_digest": gloss_digest,
                    "live": live,
                    "repair_round": repair_record["round"] if repair_record else 0,
                })
                cached_row = engine.store.read("language_artifact_cache", cache_id) if (not force and is_large_workspace) else None
                if cached_row is not None:
                    result["artifacts"].append(cached_row)
                    continue
                doc_session = None
                if live:
                    # WO-R4.4 (ISS-17): Per-document JevSession prevents hitting a shared 64-call ceiling at doc #5
                    per_doc_timeout = min(timeout, 120, config.get("timeout_seconds", 60)) if not is_large_workspace else min(120, config.get("timeout_seconds", 60))
                    doc_session = JevSession(config | {"timeout_seconds": max(0.01, per_doc_timeout)},
                                             transport=transport, cancel=cancel, reserve=budget.reserve, max_calls=64)
                try:
                    assessment = assess_jev(text, config, budget, glossary, session=doc_session, context_documents=ctx_docs,
                                            allow_windowing=(is_large_workspace or len(local["sentence_ids"]) > 64)) if live else local
                    meaning = {"status": "UNKNOWN", "reason": "No separate meaning assessment for this revision"}
                    if repair_record:
                        parent = engine.store.read("changes", repair_record["parent_change"])
                        original = engine.store.load_snapshot(parent["snapshot_digest"]).artifacts[document["artifact_id"]].text
                        meaning = meaning_jev(original, text, doc_session) if live else {"status": "UNKNOWN", "reason": "Live meaning review not requested"}
                finally:
                    if doc_session is not None:
                        all_calls.extend(doc_session.calls)
                art_row = {"artifact_id": document["artifact_id"], "revision": document["revision"],
                           "assessment": assessment, "local": local, "semantic_preservation": meaning,
                           "repair_round": repair_record["round"] if repair_record else 0}
                result["artifacts"].append(art_row)
                if is_large_workspace:
                    with engine.store.lock():
                        engine.store.write("language_artifact_cache", cache_id, art_row)
            result["execution_status"] = "COMPLETE"
        except SddError as error:
            result["error"] = {"code": error.code, "status": getattr(error.status, "value", error.status)}
            result["execution_status"] = "INCOMPLETE"
        except Exception as error:
            result["error"] = {"code": "LANGUAGE_REVIEW_UNAVAILABLE", "type": type(error).__name__}
            result["execution_status"] = "INCOMPLETE"
        numerator = sum(row["assessment"].get("model_assessed_numerator", 0) for row in result["artifacts"])
        max_docs = snapshot.config.get("policy", {}).get("max_workspace_documents", 512)
        denominator = sum(evaluate(document["text"])["denominator"] for document in documents) if len(documents) <= max_docs else None
        result |= {"model_assessed_numerator": numerator, "denominator": denominator,
                   "model_assessed_coverage": numerator / denominator if denominator else None,
                   "calls": _safe_calls(all_calls), "budget": budget.report(), "finished_at": utc_now()}
        statuses = [row["assessment"].get("assessment_status", row["assessment"]["status"]) for row in result["artifacts"]]
        if result["execution_status"] == "COMPLETE":
            result["status"] = "NOT_APPLICABLE" if not denominator else "FAIL" if "FAIL" in statuses or any(row["local"]["findings"] for row in result["artifacts"]) or any(
                row["semantic_preservation"]["status"] == "FAIL" for row in result["artifacts"]) else "INCOMPLETE" if any(
                status not in {"PASS", "NOT_APPLICABLE"} for status in statuses) or any(
                row["repair_round"] and row["semantic_preservation"]["status"] != "PASS" for row in result["artifacts"]) else "NEEDS_HUMAN_REVIEW"
        try:
            current = engine.context(change_id)[1]
            if current.digest != snapshot.digest or binding(current) != expected: raise SddError("LANGUAGE_STALE", "Inputs changed", Status.STALE)
        except SddError: result["status"], result["execution_status"] = "STALE", "STALE"
        result["next_action"] = {
            "PROVIDER_NOT_CONFIGURED": "Ask the workspace owner to configure the server credential; keep this draft unpublished.",
            "BUDGET_EXHAUSTED": "Keep the draft and request manual review. A child candidate does not reset this budget.",
            "CONTEXT_LIMIT": "Explicitly split the contract boundary; preserve unresolved cross-document obligations.",
        }.get(result.get("error", {}).get("code"), "Inspect sentence findings and unknowns. Request a targeted author repair or signed human review.")
        with engine.store.lock(): engine.store.write("language_jobs", identity, result)
        return result


def repair(workspace, change_id, artifact_id, text, skill, expected_snapshot, operation_id=None):
    """Reserve one bounded repair attempt, then create a grant-checked proposal."""
    from sdd_core.budget import candidate_root
    from sdd_core.model import digest
    engine = engine_for(workspace)
    change, snapshot, before = engine.context(change_id)
    artifact = snapshot.artifacts.get(artifact_id)
    if artifact is None: raise BridgeError("ARTIFACT_UNKNOWN", "Select a registered candidate artifact")
    if not isinstance(text, str) or len(text.encode()) > 50_000 or protected_facts(text) != protected_facts(artifact.text):
        raise BridgeError("LANGUAGE_FACT_CHANGE", "Repair must preserve ordered facts, literals, quantities, normative force and quotes")
    if text == artifact.text: raise BridgeError("LANGUAGE_NO_CHANGE", "Supply a targeted unpublished revision")
    authority = (before or snapshot).config
    grant = authority.get("skills", {}).get(skill, {})
    if "author" not in grant.get("capabilities", []) or artifact.owner != skill:
        raise BridgeError("CAPABILITY_DENIED", "Repair requires the document owner's accepted author grant")
    if not any(artifact.path == path or artifact.path.startswith(path.rstrip('/') + '/') for path in grant.get("write_scope", [])):
        raise BridgeError("WRITE_SCOPE_DENIED", "Document lies outside the author's accepted scope")
    if expected_snapshot != change["origin_snapshot"]:
        raise BridgeError("WORKSPACE_CHANGED", "Repair must bind the current live origin", "STALE")
    root = candidate_root(engine.store, change)
    expected = digest({"parent": change_id, "artifact": artifact_id, "text": text, "skill": skill, "origin": expected_snapshot})
    operation_id = operation_id or "REPAIR-" + expected[:32]
    account_id = digest({"root": root, "artifact": artifact_id})
    with engine.store.lock("language-repair-" + root):
        account = engine.store.read("repair_accounts", account_id, {"attempts": {}})
        prior = account["attempts"].get(operation_id)
        if prior and prior["binding"] != expected: raise BridgeError("OPERATION_CONFLICT", "Repair operation names different input")
        limit = (before or snapshot).config.get("language", {}).get("max_repair_rounds", 2)
        if not prior:
            if len(account["attempts"]) >= limit:
                raise BridgeError("LANGUAGE_ROUND_LIMIT", "Repair attempt limit reached; request independent manual review", "INCOMPLETE")
            prior = {"binding": expected, "round": len(account["attempts"]) + 1}
            account["attempts"][operation_id] = prior
            with engine.store.lock(): engine.store.write("repair_accounts", account_id, account)
        result = propose(workspace, [{"action": "update", "artifact_id": artifact_id,
                          "expected_revision": artifact.revision, "content": text}], skill, expected_snapshot, operation_id, change_id)
        with engine.store.lock():
            engine.store.write("language_repairs", result["change"]["change_id"], {"parent_change": change_id,
                "artifact_id": artifact_id, "from_revision": artifact.revision, "round": prior["round"],
                "root_change": root, "draft_only": True}, immutable=True)
        return result | {"repair_round": prior["round"], "review_required": True,
                         "next_action": "Review the new candidate; inspect language, meaning and semantic evidence before signed acceptance."}


def review_candidate(workspace, change_id, *, live=False, force=False, transport=None, cancel=None):
    from sdd_core.adapters.facade import build_provider, resolve_provider_config
    from sdd_core.budget import Budget, candidate_root
    from sdd_core.model import SddError, Status
    engine = engine_for(workspace)
    change, snapshot, _ = engine.context(change_id)
    deterministic = engine.check(change_id).to_dict()
    if deterministic["status"] != "PASS": return {"status": deterministic["status"], "check": deterministic, "published": False}
    semantic, started = {"status": "NOT_RUN", "reason": "Live review not requested"}, time.monotonic()
    total_deadline = 600 if len(snapshot.artifacts) > 32 else 120
    max_total_calls = max(128, len(snapshot.artifacts) * 4)
    resolved_cfg = resolve_provider_config(snapshot.config.get("provider"), workspace)
    if live and resolved_cfg:
        config = resolved_cfg
        budget = Budget(engine.store, candidate_root(engine.store, change), float(config.get("max_cost_usd", 5.0)))
        class Bounded:
            calls = []
            def review(self, packet):
                remaining = min(config.get("timeout_seconds", 60), total_deadline - (time.monotonic() - started))
                if remaining <= 0 or len(self.calls) >= max_total_calls:
                    raise SddError("PROVIDER_DEADLINE", "Candidate review limit reached", Status.INCOMPLETE)
                judge = build_provider(config | {"timeout_seconds": remaining}, transport=transport, cancel=cancel, reserve=budget.reserve)
                try: return judge.review(packet)
                finally: self.calls.extend(getattr(judge, "calls", []))
        semantic = engine.review(change_id, provider=Bounded(), force=force)
    language = review(workspace, change_id, live=live, force=force, transport=transport, cancel=cancel,
                      timeout=max(.001, total_deadline - (time.monotonic() - started)))
    status = "FAIL" if semantic["status"] == "FAIL" or language["status"] == "FAIL" else "STALE" if language["status"] == "STALE" else "INCOMPLETE" if semantic["status"] != "PASS" or language["status"] not in {"NEEDS_HUMAN_REVIEW", "NOT_APPLICABLE"} else "NEEDS_HUMAN_REVIEW"
    return {"status": status, "change_id": change_id, "snapshot_digest": snapshot.digest, "check": deterministic,
            "semantic": semantic, "language": language, "qualified": False, "published": False,
            "next_action": "Inspect findings; request targeted author repair or signed human review. Results grant no acceptance."}
