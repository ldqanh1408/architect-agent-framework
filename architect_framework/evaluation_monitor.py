"""Bounded recurring Jev evaluation, drift reports and fail-closed revocation.

No report installs a qualification or changes an accepted provider/policy.
"""
from datetime import timedelta
import json
from pathlib import Path

from architect_framework.sdd_bridge import engine_for


def paired(baseline, candidate):
    """Compare like-for-like case outcomes; synthetic runs remain unqualified."""
    if baseline.get("corpus_digest") != candidate.get("corpus_digest"):
        raise ValueError("Paired evaluation requires the identical frozen corpus")
    left = {row["case_id"]: row for row in baseline["records"]}
    right = {row["case_id"]: row for row in candidate["records"]}
    if not left or left.keys() != right.keys(): raise ValueError("Paired evaluations need identical case identities")
    regressions = [identity for identity in left if left[identity]["classification"] in {"TP", "TN"}
                   and right[identity]["classification"] not in {"TP", "TN"}]
    def usage(report):
        calls = report.get("telemetry", [])
        latencies = sorted(row["latency_seconds"] for row in calls if isinstance(row.get("latency_seconds"), (int, float)))
        return {"reserved_usd": report.get("reserved_usd"), "calls": len(calls),
                "p50_seconds": latencies[len(latencies) // 2] if latencies else None,
                "p95_seconds": latencies[min(len(latencies) - 1, int(len(latencies) * .95))] if latencies else None,
                "actual_billing": "UNKNOWN"}
    return {"kind": "paired-evaluation", "status": "REGRESSION" if regressions else "NO_OBSERVED_REGRESSION",
            "cases": len(left), "regressions": regressions, "baseline": usage(baseline), "candidate": usage(candidate),
            "quality_claim": "LIVE_MEASURED" if all(report.get("mode") == "live-api" for report in [baseline, candidate]) else "SYNTHETIC_OR_RECORDED_ONLY",
            "qualified": False, "approval_authority": False}


def run(workspace, corpus, *, live=False, force=False, interval_hours=24, now=None):
    from sdd_core.evaluation import evaluate, provider_binding, qualification_current
    from sdd_core.model import SddError, digest, instant, utc_now
    from sdd_core.workspace import capture
    if type(interval_hours) is not int or not 1 <= interval_hours <= 720:
        raise ValueError("Evaluation interval must be 1 to 720 hours")
    from sdd_core.adapters.facade import resolve_provider_config
    engine = engine_for(workspace)
    snapshot = capture(Path(workspace))
    config = snapshot.config.get("provider") or resolve_provider_config({}, Path(workspace))
    now = now or utc_now()
    expected = digest({"provider": provider_binding(config), "corpus": corpus, "interval_hours": interval_hours})
    identity = "MONITOR-" + expected[:32]
    with engine.store.lock("monitor-" + expected[:32]):
        previous = engine.store.read("evaluation_monitors", identity)
        healthy = qualification_current(engine.store, config, now, config.get("qualification_scope"))
        if previous and not force and not previous.get("retryable") and previous.get("live") == live and instant(now) < instant(previous["next_due"]):
            return {**previous, "reused": True, "current_qualification": healthy}
        report = {"kind": "evaluation-monitor", "binding": expected, "created_at": now,
            "next_due": (instant(now) + timedelta(hours=interval_hours)).isoformat(),
            "live": live, "status": "ADVISORY", "current_qualification": healthy,
            "qualified": False, "approval_authority": False, "published": False}
        old = config.get("qualification_digest")
        known = engine.store.read("evaluations", old) if old else None
        report["drift"] = {"implementation_or_provider_changed": bool(known and known.get("provider_binding") != provider_binding(config)),
                            "qualification_expired_or_revoked": bool(old and not healthy)}
        if not live:
            report["reason"] = "LIVE_EVALUATION_NOT_REQUESTED"
        elif config.get("type") != "typesafe-jev":
            report["reason"] = "CONFIGURE_JEV_PROVIDER"
        else:
            # A stable operation ID resumes partial evaluations without resetting
            # their persistent budget. Force creates a new explicitly requested run.
            from uuid import uuid4
            bucket = int(instant(now).timestamp()) // (interval_hours * 3600)
            operation = "CANARY-" + expected[:20] + "-" + (uuid4().hex[:12] if force else str(bucket))
            if previous and previous.get("retryable") and not force:
                operation = previous.get("operation_id", operation)
            report["operation_id"] = operation
            try:
                evaluation = evaluate(engine.store, config, corpus, live=True, now=now, operation_id=operation)
                report["evaluation_digest"] = evaluation["evaluation_digest"]
                report["held_out"] = evaluation["held_out"]
                report["reserved_usd"] = evaluation.get("reserved_usd")
                report["request_count"] = evaluation.get("request_count")
                report["operational_error"] = next((row["error"]["code"] for row in evaluation["records"] if row.get("error")), None)
                report["retryable"] = evaluation.get("completion_status") == "INTERRUPTED"
                passing = bool(evaluation["records"]) and len(evaluation["records"]) == len(corpus["cases"]) and all(
                    row["classification"] in {"TP", "TN"} for row in evaluation["records"])
                report["reason"] = report["operational_error"] or ("CANARY_PASSED_ADVISORY" if passing else "CANARY_FAILED")
                if known and not report["retryable"] and known.get("corpus_digest") == evaluation.get("corpus_digest"):
                    report["comparison"] = paired(known, evaluation)
                # A small healthy canary need not requalify a 600-case holdout.
                # It may retain existing current authority, never create it.
                healthy = healthy and passing and not report["operational_error"]
            except SddError as error:
                healthy = False
                report["reason"] = error.code
                report["retryable"] = True
        # Revocation only removes authority. Offline health inspection can revoke
        # a stale binding; it cannot promote a model or attach a new digest.
        if old and (not healthy or report["drift"]["implementation_or_provider_changed"]):
            revocation = {"evaluation_digest": old, "reason": report.get("reason", "DRIFT"), "created_at": now,
                          "monitor_binding": expected}
            with engine.store.lock(): engine.store.write("evaluation_revocations", digest(revocation), revocation, immutable=True)
            report["current_qualification"] = False
            report["action"] = "REVOKED_TO_ADVISORY_MANUAL"
        else: report["action"] = "NO_AUTHORITY_CHANGE"
        if capture(Path(workspace)).digest != snapshot.digest:
            report["status"] = "STALE"
        with engine.store.lock(): engine.store.write("evaluation_monitors", identity, report)
        return report


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--interval-hours", type=int, default=24)
    args = parser.parse_args(argv)
    if args.corpus.resolve() == args.report.resolve(): parser.error("Report cannot overwrite the corpus")
    if args.corpus.stat().st_size > 20_000_000: parser.error("Corpus exceeds 20 MB")
    # Keep reports outside the specification inventory.
    if args.report.resolve().is_relative_to(args.workspace.resolve()): parser.error("Write reports outside the spec workspace")
    result = run(args.workspace, json.loads(args.corpus.read_text(encoding="utf-8")), live=args.live, force=args.force, interval_hours=args.interval_hours)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": result["status"], "reason": result.get("reason"), "action": result["action"]}))
    return 3  # A health/canary report never grants release qualification.


if __name__ == "__main__": raise SystemExit(main())
