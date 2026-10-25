"""Bounded live smoke cohort with persistent budget; never qualification."""
import hashlib
import json
import os
from pathlib import Path

from .evaluation_budget import ReservationLedger

DEFAULTS = {"endpoint": "https://api.typesafe.ai/v1/systemone", "model": "jev-1.14.0",
            "api_key_env": "JEV_API_KEY", "input_per_million": 1, "output_per_million": 1,
            "max_cost_usd": 5, "max_output_tokens": 256, "max_attempts": 1, "timeout_seconds": 15}
# Deliberately conservative price ceilings, not a current vendor price quotation.
JEV_REVIEW_DEFAULTS = DEFAULTS | {"type": "typesafe-jev", "max_output_tokens": 4000,
                                "max_attempts": 2, "timeout_seconds": 60}
# Explicit opt-in preset only. No default path calls this provider or falls back
# to it. The host author can repair drafts without another generative API.
OPTIONAL_REVIEW_PRESET = {"endpoint": "https://api.openai.com/v1/chat/completions", "model": "gpt-5.4-2026-03-05",
                   "api_key_env": "OPENAI_API_KEY", "input_per_million": 10, "output_per_million": 50,
                   "max_cost_usd": 5, "max_output_tokens": 4000, "max_attempts": 1, "timeout_seconds": 30}


def read_corpus(path):
    path = Path(path)
    if path.stat().st_size > 500_000: raise ValueError("Pilot corpus exceeds limit")
    corpus = json.loads(path.read_text(encoding="utf-8"))
    if corpus.get("version") != 1 or not isinstance(corpus.get("cases"), list) or not 1 <= len(corpus["cases"]) <= 30:
        raise ValueError("Use a version 1 pilot with 1 to 30 cases")
    seen = set()
    for case in corpus["cases"]:
        if not isinstance(case, dict) or set(case) != {"id", "state", "expected"} or not isinstance(case["id"], str) or not case["id"] or case["id"] in seen:
            raise ValueError("Duplicate or malformed pilot case")
        seen.add(case["id"])
        if not isinstance(case["state"], dict) or len(json.dumps(case["state"]).encode()) > 16_000 or case["expected"] not in {"clear", "review", "uncertain"}:
            raise ValueError("Pilot state or expected route is invalid")
    return corpus


def run(corpus, ledger, config=None, transport=None):
    from sdd_core.adapters.facade import JevScreen
    from sdd_core.model import SddError
    cfg = DEFAULTS | (config or {})
    binding = {k: v for k, v in cfg.items() if k != "api_key_env"}
    report = {"status": "INCOMPLETE", "kind": "live-smoke-pilot", "qualified": False,
              "authority": "None; synthetic expected routes are not independent human labels",
              "config_digest": hashlib.sha256(json.dumps(binding, sort_keys=True).encode()).hexdigest(),
              "corpus_digest": hashlib.sha256(json.dumps(corpus, sort_keys=True).encode()).hexdigest(),
              "records": [], "budget": ledger.report()}
    key_env = cfg["api_key_env"]
    has_key = bool(os.environ.get(key_env) or (
        (os.environ.get("JEV_API_KEY") or os.environ.get("JEV_KEY") or os.environ.get("SDD_JUDGE_API_KEY"))
        if key_env in {"JEV_API_KEY", "JEV_KEY", "SDD_JUDGE_API_KEY"} else None
    ))
    if not has_key:
        return report | {"blocker": "PROVIDER_NOT_CONFIGURED"}
    for case in corpus["cases"]:
        judge = JevScreen(cfg, reserve=ledger.reserve, transport=transport)
        try:
            result = judge.review(case["state"])
            row = {"id": case["id"], "route": result["route"], "confidence": result["confidence"],
                   "expected": case["expected"], "matches_synthetic_expectation": result["route"] == case["expected"],
                   "status": "COMPLETE"}
        except SddError as error:
            row = {"id": case["id"], "status": "INCOMPLETE", "code": error.code}
        row["attempts"] = len(judge.calls)
        row["http_status"] = judge.calls[-1].get("http_status") if judge.calls else None
        report["records"].append(row)
        if row["status"] != "COMPLETE": break  # Do not probe repeatedly on auth/transport/schema errors.
    report["budget"] = ledger.report()
    report["executed"] = len(report["records"])
    report["status"] = "PASS" if len(report["records"]) == len(corpus["cases"]) and all(r["status"] == "COMPLETE" for r in report["records"]) else "INCOMPLETE"
    return report


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--limit-usd", type=float, default=5)
    args = parser.parse_args(argv)
    if not 0 < args.limit_usd <= 5: parser.error("Pilot ceiling must be greater than zero and at most USD 5")
    corpus = read_corpus(args.corpus)
    ledger = ReservationLedger(args.ledger, args.limit_usd)
    report = run(corpus, ledger)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": report["status"], "qualified": False, "executed": report.get("executed", 0), "budget": report["budget"]}))
    return 0 if report["status"] == "PASS" else 3


if __name__ == "__main__": raise SystemExit(main())
