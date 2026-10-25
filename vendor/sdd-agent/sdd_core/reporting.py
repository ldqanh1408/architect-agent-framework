"""Derived debt/coverage report. Findings close only on an accepted revision."""
from __future__ import annotations

from collections import Counter

from .model import Status, instant
from .validation import subject_artifact


def report(engine, change_id=None):
    result = engine.readiness(change_id)
    snapshot = engine.store.load_snapshot(result.snapshot)
    now = engine.clock()
    baseline = engine.store.baseline()
    published = bool(baseline and baseline["snapshot_digest"] == snapshot.digest and result.status == Status.PASS)
    live = {f.id: f for f in result.findings}
    active_obligations = {o["id"]: o for o in snapshot.config["obligations"] if o.get("active", True)}
    waived_ids = {risk["finding"]["finding_id"] for risk in result.details["accepted_risks"]}
    with engine.store.lock():
        records = {r["finding_id"]: r for r in engine.store.list("finding_history")}
        for identifier, finding in live.items():
            obligation = active_obligations.get(finding.obligation_id, {})
            owners = [a.owner for s in finding.subjects if (a := subject_artifact(snapshot, s)) is not None]
            owner = obligation.get("owner") or (owners[0] if owners else snapshot.config["policy"].get("fallback_owner") or ",".join(snapshot.config["policy"]["reviewers"]))
            state = "CONFIRMED" if finding.status == Status.FAIL else finding.status.value
            record = records.get(identifier, {"finding_id": identifier, "first_seen": now, "events": []})
            if record.get("state") != state or record.get("snapshot_digest") != snapshot.digest:
                record["events"].append({"at": now, "state": state, "snapshot_digest": snapshot.digest})
            record.update({"state": state, "last_seen": now, "snapshot_digest": snapshot.digest, "owner": owner, "finding": finding.to_dict()})
            records[identifier] = record
            engine.store.write("finding_history", identifier, record)
        for risk in result.details["accepted_risks"]:
            finding = risk["finding"]
            identifier = finding["finding_id"]
            owner = active_obligations.get(finding.get("obligation_id"), {}).get("owner") or snapshot.config["policy"].get("fallback_owner") or ",".join(snapshot.config["policy"]["reviewers"])
            record = records.get(identifier, {"finding_id": identifier, "first_seen": now, "events": []})
            if record.get("state") != "WAIVED" or record.get("snapshot_digest") != snapshot.digest:
                record["events"].append({"at": now, "state": "WAIVED", "snapshot_digest": snapshot.digest,
                                         "decision_id": risk["decision"]["decision_id"]})
            record.update({"state": "WAIVED", "last_seen": now, "snapshot_digest": snapshot.digest,
                           "owner": owner, "finding": finding, "waiver": risk["decision"]})
            records[identifier] = record
            engine.store.write("finding_history", identifier, record)
        for identifier in records.keys() - live.keys() - waived_ids:
            record = records[identifier]
            state = "CLOSED" if published else "CANDIDATE_REPAIRED"
            if record.get("state") == "CLOSED" or record.get("state") == state:
                continue
            record.update({"state": state, "last_seen": now})
            record["events"].append({"at": now, "state": state, "snapshot_digest": snapshot.digest,
                                     "acceptance_id": baseline["acceptance_id"] if published else None})
            engine.store.write("finding_history", identifier, record)
    debt = [{**r, "age_seconds": max(0, (instant(now) - instant(r["first_seen"])).total_seconds())}
            for r in records.values() if r["state"] != "CLOSED"]
    critical = {o["id"] for o in active_obligations.values() if o["criticality"] == "critical"}
    semantic = {c["obligation_id"]: c for c in result.details["semantic_coverage"]}
    deterministic = result.details["relations"]
    freshness = {s["source_id"]: s["state"] for s in result.details["freshness"]}
    current = {i for i in critical if all(c["status"] == "PASS" for c in deterministic.get(i, []))
               and ((i not in semantic and bool(deterministic.get(i))) or (i in semantic and semantic[i]["status"] == "CURRENT"))
               and all(freshness.get(s) == "CURRENT" for s in active_obligations[i].get("external_sources", []))}
    output = result.to_dict() | {"kind": "regression-debt-report", "generated_at": now, "baseline": baseline,
        "critical_coverage": {"current": len(current), "expected": len(critical), "missing": sorted(critical - current)},
        "confirmed_blocker_count": sum(f.status == Status.FAIL and f.severity == "blocker" for f in result.findings),
        "debt": sorted(debt, key=lambda r: (r["owner"], r["first_seen"], r["finding_id"])),
        "debt_by_owner": dict(Counter(r["owner"] for r in debt)),
        "waivers": result.details["accepted_risks"], "closed_count": sum(r["state"] == "CLOSED" for r in records.values())}
    return output
