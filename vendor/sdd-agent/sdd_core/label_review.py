"""Immutable corpus manifests and scoped human label signatures."""
import uuid
from .model import SddError, Status, canonical, digest, instant, utc_now
from .policy import effective_policy
from .workspace import capture


def authority(store):
    live = capture(store.root.parent)
    baseline = store.baseline()
    accepted = store.load_snapshot(baseline["snapshot_digest"]) if baseline else None
    return live, effective_policy(live, accepted)


def manifest_digest(corpus):
    return digest({k: v for k, v in corpus.items() if k != "label_approvals"})


def stage(store, corpus):
    if not isinstance(corpus, dict) or corpus.get("version") != 1 or not isinstance(corpus.get("cases"), list) or not corpus["cases"]:
        raise SddError("EVAL_CORPUS_INVALID", "Supply a version 1 corpus with cases")
    if len(canonical(corpus)) > 20 * 1024 * 1024: raise SddError("LABEL_CORPUS_LIMIT", "Split manifests above 20 MiB", Status.INCOMPLETE)
    ids = [case.get("id") if isinstance(case, dict) else None for case in corpus["cases"]]
    if any(not isinstance(identity, str) or not 1 <= len(identity) <= 128 for identity in ids) or len(set(ids)) != len(ids):
        raise SddError("EVAL_CORPUS_INVALID", "Case identities must be unique text")
    body = {k: v for k, v in corpus.items() if k != "label_approvals"}
    identifier = "LABELS-" + manifest_digest(body)
    with store.lock(): store.write("label_manifests", identifier, body, immutable=True)
    return {"status": "STAGED", "manifest_id": identifier, "manifest_digest": manifest_digest(body), "case_count": len(ids), "qualified": False}


def load(store, identifier):
    if not isinstance(identifier, str): raise SddError("LABEL_MANIFEST_UNKNOWN", "Select a staged manifest")
    corpus = store.read("label_manifests", identifier)
    if corpus is None: raise SddError("LABEL_MANIFEST_UNKNOWN", "Stage and inspect the corpus first")
    if identifier != "LABELS-" + manifest_digest(corpus): raise SddError("LABEL_MANIFEST_CORRUPT", "Manifest changed; restage original bytes")
    return corpus


def verified_approvals(store, corpus):
    if store.decision_verifier is None: return []
    _, policy = authority(store)
    ids = {case["id"] for case in corpus["cases"]}
    supplied = corpus.get("label_approvals", [])
    if not isinstance(supplied, list): supplied = []
    result = []
    for record in [*store.list("label_approvals"), *supplied]:
        if (not isinstance(record, dict) or record.get("kind") != "eval_labels" or record.get("manifest_digest") != manifest_digest(corpus)
                or not isinstance(record.get("actor"), str) or record["actor"] not in policy["reviewers"]
                or not isinstance(record.get("reason"), str) or not record["reason"].strip()
                or not isinstance(record.get("case_ids"), list) or not record["case_ids"]
                or any(not isinstance(i, str) for i in record["case_ids"]) or not set(record["case_ids"]) <= ids): continue
        if store.decision_verifier(record) is None: result.append(record)
    return result


def prepare(store, manifest_id, actor, reason, case_ids, now=None):
    corpus = load(store, manifest_id)
    live, policy = authority(store)
    if not isinstance(actor, str) or actor not in policy["reviewers"] or actor in live.config.get("skills", {}): raise SddError("DECISION_ACTOR_DENIED", "A configured human must review labels")
    ids = {case["id"] for case in corpus["cases"]}
    if (not isinstance(case_ids, list) or not 1 <= len(case_ids) <= 20 or any(not isinstance(i, str) for i in case_ids)
            or len(set(case_ids)) != len(case_ids) or not set(case_ids) <= ids or not isinstance(reason, str) or not reason.strip()):
        raise SddError("LABEL_REVIEW_SCOPE", "Select 1..20 inspected cases and explain the review")
    return {"kind": "eval_labels", "decision_id": "LDEC-" + uuid.uuid4().hex, "manifest_id": manifest_id,
            "manifest_digest": manifest_digest(corpus), "case_ids": sorted(case_ids), "actor": actor,
            "reason": reason.strip(), "created_at": now or utc_now(), "origin_snapshot": live.digest}


def commit(store, record, now=None):
    required = {"kind", "decision_id", "manifest_id", "manifest_digest", "case_ids", "actor", "reason", "created_at", "origin_snapshot", "attestation"}
    if not isinstance(record, dict) or set(record) != required or record["kind"] != "eval_labels": raise SddError("LABEL_REVIEW_SCHEMA", "A signed label record is required")
    live, _ = authority(store)
    corpus = load(store, record["manifest_id"])
    if record["manifest_digest"] != manifest_digest(corpus) or record["origin_snapshot"] != live.digest: raise SddError("LABEL_MANIFEST_STALE", "Review the current manifest and authority", Status.STALE)
    age = (instant(now or utc_now()) - instant(record["created_at"])).total_seconds()
    if not 0 <= age <= 300 or store.decision_verifier is None or store.decision_verifier(record) is not None: raise SddError("DECISION_SIGNATURE_INVALID", "A current trusted human signature is required")
    prepare(store, record["manifest_id"], record["actor"], record["reason"], record["case_ids"])
    with store.lock(): store.write("label_approvals", record["decision_id"], record, immutable=True)
    return {"status": "RECORDED", "kind": "eval_labels", "decision_id": record["decision_id"], "qualified": False}


def packet(store, identifier, offset=0, limit=20):
    corpus = load(store, identifier)
    if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 20: raise SddError("LABEL_PACKET_INVALID", "Read a page of 1..20 cases")
    approvals = verified_approvals(store, corpus)
    return {"manifest_id": identifier, "manifest_digest": manifest_digest(corpus), "total": len(corpus["cases"]), "offset": offset,
            "cases": [{**case, "verified_reviewers": sorted({r["actor"] for r in approvals if case["id"] in r["case_ids"]})} for case in corpus["cases"][offset:offset + limit]]}
