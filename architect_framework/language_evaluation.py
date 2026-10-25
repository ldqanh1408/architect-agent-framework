"""Separate, resumable style and meaning evaluations over signed frozen labels.

Reports measure the declared project profile; they never certify ASD compliance,
install an accepted policy, or qualify the semantic document-review adapter.
"""
import hashlib
import json
from pathlib import Path
import uuid

from architect_framework.document_style import PROFILE, prose
from architect_framework.sdd_bridge import engine_for
from architect_framework.style_review import RULES, assess_jev, meaning_jev

MEANING = ("actors", "scope", "quantities", "normative", "order", "literals")


def validate(corpus):
    from sdd_core.model import SddError, canonical
    def invalid(): raise SddError("LANGUAGE_CORPUS_INVALID", "Use a bounded version 1 language corpus with complete frozen labels")
    if (not isinstance(corpus, dict) or corpus.get("version") != 1 or corpus.get("kind") != "language-evaluation"
            or corpus.get("profile_id") != PROFILE["id"] or not isinstance(corpus.get("cases"), list)
            or not 1 <= len(corpus["cases"]) <= 2000 or len(canonical(corpus)) > 20_000_000): invalid()
    ids = set()
    for case in corpus["cases"]:
        if not isinstance(case, dict): invalid()
        for name in ("id", "base_case_id", "source_group", "family", "language"):
            if not isinstance(case.get(name), str) or not 1 <= len(case[name]) <= 128: invalid()
        if case["id"] in ids or case.get("split") not in {"calibration", "held_out"}: invalid()
        ids.add(case["id"])
        if not isinstance(case.get("kind"), str) or case["kind"] not in {"style", "meaning"}: invalid()
        for name in (["markdown"] if case["kind"] == "style" else ["original", "candidate"]):
            if not isinstance(case.get(name), str) or not 1 <= len(case[name].encode()) <= 50_000: invalid()
        label = case.get("label")
        if not isinstance(label, dict): invalid()
        if case["kind"] == "style":
            sentences = prose(case["markdown"])
            labels = label.get("sentences")
            glossary = case.get("glossary", {})
            if (not 1 <= len(sentences) <= 64 or not isinstance(labels, list) or len(labels) != len(sentences)
                    or not isinstance(glossary, dict) or any(not isinstance(k, str) or not isinstance(v, dict) for k, v in glossary.items())): invalid()
            expected = labels
            keys = set(RULES)
        else:
            expected, keys = [label.get("checks")], set(MEANING)
        if any(not isinstance(row, dict) or set(row) != keys or any(not isinstance(value, str) or value not in {"PASS", "FAIL"} for value in row.values()) for row in expected): invalid()
    return corpus


def _classification(expected, actual):
    if actual not in {"PASS", "FAIL"}: return "UNKNOWN"
    return ("TP" if actual == "FAIL" else "FN") if expected == "FAIL" else ("FP" if actual == "FAIL" else "TN")


def evaluate(workspace, corpus, *, live=False, responses=None, operation_id=None, cancel=None):
    """Explicit live API or recorded fixtures; completed cases resume idempotently.

    A single invocation permits 128 calls / 120 seconds. Reservations survive
    interruption and retries. Reuse the operation ID to continue a larger cohort.
    """
    from sdd_core.adapters.typed_jev import JevSession
    from sdd_core.budget import Budget
    from sdd_core.evaluation import cluster_intervals, metrics, provider_binding
    from sdd_core.label_review import manifest_digest, verified_approvals
    from sdd_core.model import SddError, Status, digest, utc_now
    from sdd_core.workspace import capture
    from architect_framework.sdd_bridge.language import _safe_calls
    validate(corpus)  # Validate every label before a paid request.
    if live and responses is not None: raise SddError("EVAL_MODE_INVALID", "Live runs cannot inject recorded answers")
    from sdd_core.adapters.facade import resolve_provider_config
    engine = engine_for(workspace)
    snapshot = capture(Path(workspace)); config = snapshot.config.get("provider") or resolve_provider_config({}, Path(workspace))
    if live and config.get("type") != "typesafe-jev": raise SddError("PROVIDER_NOT_CONFIGURED", "Configure Jev explicitly", Status.INCOMPLETE)
    code = {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
            for name in ["language_evaluation.py", "style_review.py", "document_style.py"]}
    binding = digest({"manifest": manifest_digest(corpus), "provider": provider_binding(config),
                      "profile": PROFILE, "code": code, "live": live, "responses": responses})
    operation_id = operation_id or "LANG-EVAL-" + uuid.uuid4().hex
    with engine.store.lock("language-evaluation-" + operation_id):
        run = engine.store.read("language_evaluation_runs", operation_id)
        if run and run["binding"] != binding: raise SddError("OPERATION_CONFLICT", "The frozen evaluation inputs changed", Status.STALE)
        run = run or {"binding": binding, "records": [], "telemetry": [], "started_at": utc_now()}
        # Bind the operation before the first reservation or network request,
        # including an abrupt interruption with no completed case.
        with engine.store.lock(): engine.store.write("language_evaluation_runs", operation_id, run)
        ledger = Budget(engine.store, operation_id, config.get("max_cost_usd", 5))
        session = JevSession(config | {"timeout_seconds": min(config.get("timeout_seconds", 120), 120)},
                             cancel=cancel, reserve=ledger.reserve, max_calls=128) if live else None
        for case in corpus["cases"]:
            if any(row["case_id"] == case["id"] for row in run["records"]): continue
            error = None
            try:
                # Neither labels nor split/family metadata are sent to Jev.
                if live:
                    answer = (assess_jev(case["markdown"], config, ledger, case.get("glossary"), session=session)
                              if case["kind"] == "style" else meaning_jev(case["original"], case["candidate"], session))
                else: answer = (responses or {}).get(case["id"], {})
                expected = case["label"]["sentences"] if case["kind"] == "style" else [case["label"]["checks"]]
                actual = ([row["rules"] for row in answer.get("sentences", [])] if case["kind"] == "style" else [answer.get("checks", {})])
                if len(actual) != len(expected) or any(not isinstance(row, dict) or set(row) != set(expected[n]) or any(not isinstance(v, str) or v not in {"PASS", "FAIL", "UNKNOWN"} for v in row.values()) for n, row in enumerate(actual)):
                    actual = [{key: "UNKNOWN" for key in row} for row in expected]
            except SddError as exc:
                error = {"code": exc.code}
                # Deadline/cancellation/budget stops are resumable, not labels.
                run["last_error"] = error
                break
            run.pop("last_error", None)
            run["records"].append({"case_id": case["id"], "kind": case["kind"], "split": case["split"],
                "source_group": case["source_group"], "base_case_id": case["base_case_id"], "family": case["family"],
                "severity": case["label"].get("severity"), "expected": expected, "actual": actual, "error": error})
            with engine.store.lock(): engine.store.write("language_evaluation_runs", operation_id, run)
        if session: run["telemetry"].extend(_safe_calls(session.calls))
        run["budget"] = ledger.report()
        with engine.store.lock(): engine.store.write("language_evaluation_runs", operation_id, run)
        approvals = verified_approvals(engine.store, corpus)
        reports = {}
        for kind, keys in [("style", RULES), ("meaning", MEANING)]:
            cases = [case for case in corpus["cases"] if case["kind"] == kind and case["split"] == "held_out"]
            rows = [row for row in run["records"] if row["kind"] == kind and row["split"] == "held_out"]
            per_rule = {}
            for key in keys:
                scored = [{"classification": _classification(expected[key], row["actual"][n][key]),
                           "expected": expected[key].lower(), "source_group": row["source_group"], "severity": row["severity"]}
                          for row in rows for n, expected in enumerate(row["expected"])]
                measured = metrics(scored)
                per_rule[key] = measured | {"source_group_uncertainty": cluster_intervals(scored),
                    "disagreements": sum(r["classification"] not in {"TP", "TN"} for r in scored)}
            approved = bool(cases) and all(len({a["actor"] for a in approvals if case["id"] in a["case_ids"]}) >= 2 for case in cases)
            calibration = {case["source_group"] for case in corpus["cases"] if case["split"] == "calibration"}
            enough = (len({c["base_case_id"] for c in cases}) >= 600 and len({c["source_group"] for c in cases}) >= 30
                      and len({c["family"] for c in cases}) >= 12 and not calibration.intersection(c["source_group"] for c in cases))
            def confidence(row):
                bounds = row["source_group_uncertainty"].get("intervals_95", {})
                return (row["critical_sample_size"] >= 30 and row["abstention_rate"] == 0 and
                    all(row.get(k) is not None and row[k][0] >= .9 for k in ["precision_95_ci", "critical_recall_95_ci"]) and
                    row["false_blocker_95_ci"] is not None and row["false_blocker_95_ci"][1] <= .05 and
                    all(bounds.get(k) is not None and bounds[k][0] >= .9 for k in ["blocker_precision", "critical_recall"]) and
                    bounds.get("false_blocker_rate") is not None and bounds["false_blocker_rate"][1] <= .05)
            precise = all(confidence(row) for row in per_rule.values())
            qualified = live and len(run["records"]) == len(corpus["cases"]) and len(rows) == len(cases) and approved and enough and precise and not run.get("last_error")
            reports[kind] = {"status": "PASS" if qualified else "NOT_QUALIFIED", "qualified": bool(qualified),
                "scope": "project-profile-only", "per_rule": per_rule, "held_out_cases": len(rows),
                "requirements": {"live_api": live, "two_independent_signed_labels": approved,
                    "independent_sample_floor_and_splits": enough, "per_rule_confidence_bounds": precise}}
        report = {"kind": "language-evaluation", "operation_id": operation_id, "binding": binding,
            "manifest_digest": manifest_digest(corpus), "provider_binding": provider_binding(config),
            "mode": "live-api" if live else "recorded-fixture", "created_at": utc_now(),
            "status": "COMPLETE" if len(run["records"]) == len(corpus["cases"]) else "INCOMPLETE",
            "processed": len(run["records"]), "total": len(corpus["cases"]), "evaluations": reports,
            "error": run.get("last_error"), "records": run["records"], "telemetry": run["telemetry"], "budget": run["budget"],
            "qualified": False, "approval_authority": False, "published": False, "asd_certification": "NOT_CERTIFIED",
            "profile_mapping": PROFILE["mapping_review"], "expires_after_days": 30}
        if capture(Path(workspace)).digest != snapshot.digest:
            report["status"] = "STALE"
            for row in reports.values(): row.update(qualified=False, status="STALE")
        identity = digest(report)
        with engine.store.lock(): engine.store.write("language_evaluations", identity, report, immutable=True)
        return report | {"evaluation_digest": identity}


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--operation-id")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if args.report.resolve() == args.corpus.resolve() or args.report.resolve().is_relative_to(args.workspace.resolve()): parser.error("Write the report outside the workspace and corpus")
    if args.corpus.stat().st_size > 20_000_000: parser.error("Corpus exceeds 20 MB")
    from sdd_core.model import SddError
    try: result = evaluate(args.workspace, json.loads(args.corpus.read_text(encoding="utf-8")), live=args.live, operation_id=args.operation_id)
    except (SddError, ValueError) as exc:
        print(json.dumps({"status": "INCOMPLETE", "code": getattr(exc, "code", "INVALID_INPUT")})); return 3
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({key: result[key] for key in ["status", "processed", "total", "qualified"]}))
    return 3  # No evaluation report is a release approval.


if __name__ == "__main__": raise SystemExit(main())
