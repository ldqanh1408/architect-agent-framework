"""Labeled semantic evaluation. Contract fixtures never qualify a real provider."""
from __future__ import annotations

from collections import Counter
from datetime import timedelta
import math
import hashlib
from pathlib import Path
import uuid
import random

from .adapters.facade import build_provider
from .model import SddError, Status, canonical, digest, instant, utc_now
from .review import make_packet, obligations_for_review, verify_review
from .storage import atomic_write
from .workspace import CONFIG, build_snapshot


OPERATIONAL_ERRORS = {"PROVIDER_HTTP_ERROR", "PROVIDER_MODEL_CHANGED", "PROVIDER_UNAVAILABLE",
    "BUDGET_EXHAUSTED", "PROVIDER_NOT_CONFIGURED", "REVIEW_CANCELLED", "PROVIDER_DEADLINE"}


def provider_binding(config):
    root = Path(__file__).parent
    implementation = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob("*.py"))}
    return digest({"binding_version": 2, "provider": {k: v for k, v in (config or {}).items() if k != "qualification_digest"}, "implementation": implementation})


def wilson(successes, total):
    if not total:
        return None
    z, p = 1.959963984540054, successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [max(0, center - radius), min(1, center + radius)]


def metrics(records):
    counts = Counter(r["classification"] for r in records)
    tp, fp, fn = counts["TP"], counts["FP"], counts["FN"]
    clean = sum(r["expected"] == "pass" for r in records)
    defects = sum(r["expected"] == "fail" for r in records)
    critical = [r for r in records if r["expected"] == "fail" and r.get("severity") == "critical"]
    critical_tp = sum(r["classification"] == "TP" for r in critical)
    return {"sample_size": len(records), "counts": dict(counts),
            "blocker_precision": tp / (tp + fp) if tp + fp else None,
            "all_defect_recall": tp / defects if defects else None,
            "critical_recall": critical_tp / len(critical) if critical else None,
            "critical_sample_size": len(critical), "critical_recall_95_ci": wilson(critical_tp, len(critical)),
            "precision_95_ci": wilson(tp, tp + fp), "recall_95_ci": wilson(tp, defects),
            "false_blocker_rate": fp / clean if clean else None,
            "false_blocker_95_ci": wilson(fp, clean),
            "abstention_rate": (counts["UNKNOWN"] + counts["INVALID"]) / len(records) if records else None,
            "invalid_evidence_rate": counts["INVALID"] / len(records) if records else None,
            "false_negatives": fn}


def cluster_intervals(records, repetitions=1000):
    groups = {}
    for record in records:
        if not record.get("source_group"):
            return {"status": "INCOMPLETE", "reason": "Source groups are required for clustered uncertainty"}
        groups.setdefault(record["source_group"], []).append(record)
    if len(groups) < 2:
        return {"status": "INCOMPLETE", "reason": "At least two independent source groups are required"}
    randomizer = random.Random(20261014)
    keys = list(groups)
    names = ["blocker_precision", "critical_recall", "false_blocker_rate"]
    samples = {name: [] for name in names}
    for _ in range(repetitions):
        sample = [record for key in randomizer.choices(keys, k=len(keys)) for record in groups[key]]
        measured = metrics(sample)
        for name in names:
            if measured[name] is not None: samples[name].append(measured[name])
    intervals = {}
    for name, values in samples.items():
        values.sort()
        intervals[name] = [values[int((len(values) - 1) * .025)], values[int((len(values) - 1) * .975)]] if values else None
    return {"status": "MEASURED", "method": "source-group-bootstrap", "repetitions": repetitions, "seed": 20261014, "groups": len(groups), "intervals_95": intervals}


def evaluate(store, config, corpus, destination=None, live=False, responses=None, provider=None, now=None, operation_id=None):
    operation_id = operation_id or "EVAL-" + uuid.uuid4().hex
    # Per-run lock allows unrelated workspace operations while the API runs.
    with store.lock("evaluation-" + operation_id):
        return _evaluate(store, config, corpus, destination, live, responses, provider, now, operation_id)


def _evaluate(store, config, corpus, destination=None, live=False, responses=None, provider=None, now=None, operation_id=None):
    now = now or utc_now()
    if not isinstance(corpus, dict) or corpus.get("version") != 1 or not isinstance(corpus.get("cases"), list) or not corpus["cases"]:
        raise SddError("EVAL_CORPUS_INVALID", "Version 1 corpus with nonempty cases is required")
    if any(not isinstance(c, dict) or not isinstance(c.get("id"), str) or not c["id"] for c in corpus["cases"]):
        raise SddError("EVAL_CORPUS_INVALID", "Cases require text identities")
    for case in corpus["cases"]:
        for field in ("base_case_id", "source_group", "family", "profile_id"):
            if field in case and (not isinstance(case[field], str) or not case[field]):
                raise SddError("EVAL_CORPUS_INVALID", "Optional case metadata must contain text: " + field)
    identifiers = [c["id"] for c in corpus["cases"]]
    if len(set(identifiers)) != len(identifiers):
        raise SddError("EVAL_CORPUS_INVALID", "Duplicate case identity")
    prepared = []
    # Freeze and validate every nested case before constructing a paid adapter.
    for case in corpus["cases"]:
        for field in ("language", "group", "obligation_id"):
            if not isinstance(case.get(field), str) or not case[field]:
                raise SddError("EVAL_CORPUS_INVALID", "Cases require text: " + field)
        label = case.get("label")
        if (not isinstance(case.get("split"), str) or case["split"] not in {"calibration", "held_out"}
                or not isinstance(label, dict) or not isinstance(label.get("verdict"), str)
                or label["verdict"] not in {"pass", "fail"}):
            raise SddError("EVAL_LABEL_INVALID", case["id"])
        targets = label.get("required_subjects")
        if ((targets is not None and (not isinstance(targets, list) or not all(isinstance(s, str) and s for s in targets)))
                or (label["verdict"] == "fail" and not targets)):
            raise SddError("EVAL_LABEL_INVALID", "Defect labels require explicit nonempty target subjects: " + case["id"])
        files = case.get("files")
        if not isinstance(files, dict) or not files or any(not isinstance(k, str) or not k or not isinstance(v, str) for k, v in files.items()):
            raise SddError("EVAL_CORPUS_INVALID", "Cases require text file mappings: " + case["id"])
        snapshot = build_snapshot(files)
        if targets and any(s not in snapshot.artifacts for s in targets):
            raise SddError("EVAL_LABEL_INVALID", "Target subjects must name artifacts in the frozen case: " + case["id"])
        # Label and expected defects never enter the packet.
        snapshot.config["provider"] = {k: v for k, v in (config or {}).items() if k != "qualification_digest"}
        obligation = next((o for o in obligations_for_review(snapshot) if o["id"] == case["obligation_id"]), None)
        if obligation is None:
            raise SddError("EVAL_OBLIGATION_MISSING", case["id"])
        prepared.append((case, make_packet(snapshot, obligation)))
    if live and (responses is not None or provider is not None):
        raise SddError("EVAL_MODE_INVALID", "Live evaluation uses only the configured real API adapter")
    if live and not config:
        raise SddError("PROVIDER_NOT_CONFIGURED", "Live eval needs provider/model/budget configuration", Status.INCOMPLETE)
    operation_id = operation_id or "EVAL-" + uuid.uuid4().hex
    run_binding = digest({"corpus": corpus, "provider": provider_binding(config or {}), "live": live,
                          "responses": responses, "fixture": provider is not None})
    with store.lock():
        run = store.read("evaluation_runs", operation_id)
        if run and run["binding"] != run_binding:
            raise SddError("OPERATION_CONFLICT", operation_id, Status.STALE)
        if run and run.get("evaluation_digest"):
            report = store.read("evaluations", run["evaluation_digest"])
            if report is None or digest(report) != run["evaluation_digest"]:
                raise SddError("EVALUATION_CORRUPT", "Completed evaluation digest does not match its stored report")
            if destination:
                atomic_write(Path(destination), canonical(report | {"evaluation_digest": run["evaluation_digest"]}))
            return report | {"evaluation_digest": run["evaluation_digest"]}
        run = run or {"binding": run_binding, "status": "RUNNING", "records": [], "started_at": now}
        store.write("evaluation_runs", operation_id, run)
    reserved = store.read("budgets", operation_id, {"reserved_usd": 0.0})["reserved_usd"]
    def reserve(amount):
        nonlocal reserved
        with store.lock():
            account = store.read("budgets", operation_id, {"reserved_usd": 0.0})
            if account["reserved_usd"] + amount > float(config.get("max_cost_usd", 5.0)):
                raise SddError("BUDGET_EXHAUSTED", "Evaluation budget exhausted", Status.INCOMPLETE)
            account["reserved_usd"] += amount
            reserved = account["reserved_usd"]
            store.write("budgets", operation_id, account)
    selected = build_provider(config, reserve=reserve) if live else provider
    previous_telemetry = list(run.get("telemetry", []))
    call_offset = len(getattr(selected, "calls", []))
    records = list(run["records"])
    interrupted = False
    for case, packet in prepared:
        if any(r["case_id"] == case["id"] for r in records):
            continue
        error, raw = None, None
        try:
            if selected:
                raw = selected.review(packet)
            elif responses and case["id"] in responses:
                raw = responses[case["id"]]
            else:
                raise SddError("EVAL_RESPONSE_MISSING", "No API or recorded response; case was not evaluated", Status.INCOMPLETE)
            verified = verify_review(raw, packet)
        except SddError as exc:
            verified, error = {"status": "INCOMPLETE", "coverage": [], "findings": []}, exc.to_dict()
        finally:
            # Keep attempted requests even when a host interrupts the case.
            with store.lock():
                run["telemetry"] = previous_telemetry + list(getattr(selected, "calls", []))[call_offset:]
                store.write("evaluation_runs", operation_id, run)
        expected = case["label"]["verdict"]
        if error:
            classification = "UNKNOWN"
        elif verified["status"] != "COMPLETE":
            classification = "INVALID"
        else:
            verdict = verified["coverage"][0]["status"]
            blockers = [f for f in verified["findings"] if f["severity"] == "blocker"]
            targeted = any(set(case["label"].get("required_subjects", [])) <= {e["artifact_id"] for e in f["evidence"]} for f in blockers)
            if verdict in {"unknown", "intentionally_changed"}:
                classification = "UNKNOWN"
            elif expected == "pass":
                classification = "FP" if blockers else "TN"
            else:
                # An unrelated failure is not successful defect detection.
                classification = "TP" if verdict == "fail" and targeted else "FN"
        records.append({"case_id": case["id"], "split": case["split"], "language": case["language"], "group": case["group"],
                        "expected": expected, "classification": classification, "severity": case["label"].get("severity"), "packet_digest": packet["packet_digest"],
                        "source_group": case.get("source_group"), "base_case_id": case.get("base_case_id"), "family": case.get("family", case["group"]),
                        "label_status": case["label"].get("status", "proposed"), "error": error or verified.get("error"),
                        "response": raw, "verified": verified})
        interrupted = bool(error and error.get("code") in OPERATIONAL_ERRORS)
        with store.lock():
            # Failed operational attempts stay in the immutable report, not in
            # completed progress, so the same operation can retry that case.
            run["records"] = records[:-1] if interrupted else list(records)
            store.write("evaluation_runs", operation_id, run)
        if interrupted:
            break  # One operational failure must not trigger the remaining paid cohort.
    held = [r for r in records if r["split"] == "held_out"]
    measured = metrics(held)
    # Minimum counts prevent a handful of easy fixtures being sold as qualification.
    # Thresholds are explicit pilot defaults, not evidence that this release met them.
    from .label_review import verified_approvals
    approvals = verified_approvals(store, corpus)
    held_cases = [c for c in corpus["cases"] if c["split"] == "held_out"]
    approved = all(len({a["actor"] for a in approvals if c["id"] in a["case_ids"]}) >= 2 for c in held_cases)
    enough = len(held_cases) >= 600 and len({c.get("base_case_id") for c in held_cases if c.get("base_case_id")}) >= 600 and len({c.get("source_group") for c in held_cases if c.get("source_group")}) >= 30 and len({c.get("family", c.get("group")) for c in held_cases}) >= 12
    calibration_groups = {c.get("source_group") for c in corpus["cases"] if c["split"] == "calibration"}
    held_groups = {c.get("source_group") for c in held_cases}
    enough = enough and not calibration_groups.intersection(held_groups) and measured["critical_sample_size"] >= 30 and sum(r["expected"] == "pass" for r in held) >= 30
    clustered = cluster_intervals(held)
    bounds = clustered.get("intervals_95", {})
    cluster_pass = all(bounds.get(name) is not None for name in ["blocker_precision", "critical_recall", "false_blocker_rate"]) and bounds["blocker_precision"][0] >= .90 and bounds["critical_recall"][0] >= .90 and bounds["false_blocker_rate"][1] <= .05
    confidence = (cluster_pass and measured["precision_95_ci"] is not None and measured["precision_95_ci"][0] >= .90
                  and measured["critical_recall_95_ci"] is not None and measured["critical_recall_95_ci"][0] >= .90
                  and measured["false_blocker_95_ci"] is not None and measured["false_blocker_95_ci"][1] <= .05)
    scope_bound = bool(config and config.get("qualification_scope")) and all(c.get("profile_id") == config["qualification_scope"] for c in held_cases)
    started_at = run.get("started_at", now)
    expires_at = instant(started_at) + timedelta(days=30)
    window_current = instant(started_at) <= instant(now) < expires_at
    qualified = live and not interrupted and window_current and len(records) == len(corpus["cases"]) and approved and enough and confidence and scope_bound and (measured["blocker_precision"] or 0) >= .95 and (measured["critical_recall"] or 0) >= .95 and measured["invalid_evidence_rate"] == 0 and measured["abstention_rate"] == 0
    report = {"status": "PASS" if qualified else "INCOMPLETE", "kind": "semantic-evaluation", "qualified": qualified, "certified_scope": config.get("qualification_scope") if qualified else None,
              "operation_id": operation_id,
              "completion_status": "INTERRUPTED" if interrupted else "COMPLETE",
              "processed": len(run["records"]), "total": len(corpus["cases"]),
              "request_count": len(run.get("telemetry", [])) if live else 0,
              "mode": "live-api" if live else "contract-fixture" if provider else "recorded" if responses else "not-run",
              "created_at": now, "started_at": started_at, "expires_at": expires_at.isoformat(),
              "provider_binding": provider_binding(config or {}), "corpus_digest": digest(corpus),
              "clustered_confidence": clustered, "held_out": measured, "by_language": {language: metrics([r for r in held if r["language"] == language]) for language in sorted({r["language"] for r in held})},
              "by_group": {group: metrics([r for r in held if r["group"] == group]) for group in sorted({r["group"] for r in held})},
              "qualification_requirements": {"live_api": live, "measurement_window_current": window_current, "labels_approved_by_two_humans": approved, "minimum_600_distinct_base_cases_and_30_source_groups": enough, "confidence_bounds_met": confidence, "profile_scope_bound": scope_bound,
                                              "precision_min": .95, "critical_recall_min": .95},
              "reserved_usd": reserved, "telemetry": run.get("telemetry", []), "records": records}
    identifier = digest(report)
    with store.lock():
        store.write("evaluations", identifier, report, immutable=True)
        run.setdefault("attempts", []).append(identifier)
        run.update({"status": "INTERRUPTED" if interrupted else "COMPLETED", "last_report_digest": identifier})
        if not interrupted:
            run["evaluation_digest"] = identifier
        store.write("evaluation_runs", operation_id, run)
    if destination:
        atomic_write(Path(destination), canonical(report | {"evaluation_digest": identifier}))
    return report | {"evaluation_digest": identifier}


def qualification_current(store, config, now=None, scope=None):
    identifier = config.get("qualification_digest")
    report = store.read("evaluations", identifier) if identifier else None
    if not report or digest(report) != identifier or not report.get("qualified") or report.get("mode") != "live-api":
        return False
    if not scope or report.get("certified_scope") != scope or config.get("qualification_scope") != scope:
        return False
    if any(r.get("evaluation_digest") == identifier for r in store.list("evaluation_revocations")):
        return False
    time = instant(now or utc_now())
    return report.get("provider_binding") == provider_binding(config) and instant(report["created_at"]) <= time < instant(report["expires_at"])
