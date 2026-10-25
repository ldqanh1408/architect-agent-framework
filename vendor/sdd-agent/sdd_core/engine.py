from __future__ import annotations

from pathlib import Path
from datetime import timedelta
import uuid

from . import __version__
from .adapters.facade import build_provider, resolve_provider_config
from .changes import reconcile
from .freshness import freshness, latest_observations
from .graph import build_graph
from .model import Finding, SddError, Status, digest, instant, utc_now
from .policy import covering, effective_policy, valid_decisions
from .review import make_packet, obligations_for_review, verify_review
from .storage import Store
from .validation import check_snapshot
from .workspace import capture


class Engine:
    def __init__(self, workspace, clock=utc_now, fault=None, decision_verifier=None):
        self.workspace = Path(workspace).resolve()
        self.store = Store(self.workspace, decision_verifier=decision_verifier)
        self.clock = clock
        self.fault = fault or (lambda checkpoint: None)

    def context(self, change_id=None, check_live=True):
        change = self.store.read("changes", change_id) if change_id else reconcile(self.store, self.workspace)
        if change is None:
            raise SddError("CHANGE_UNKNOWN", str(change_id))
        snapshot = self.store.load_snapshot(change["snapshot_digest"])
        if snapshot.engine_version != __version__:
            raise SddError("ENGINE_VERSION_STALE", "Reconcile with the current engine", Status.STALE)
        baseline = self.store.baseline()
        if change["base_acceptance"] != (baseline["acceptance_id"] if baseline else None):
            raise SddError("BASELINE_CONFLICT", "Baseline changed since candidate creation", Status.STALE)
        if check_live and capture(self.workspace).digest != change["origin_snapshot"]:
            raise SddError("WORKSPACE_CHANGED", "Reconcile edits made after this candidate was captured", Status.STALE)
        before = self.store.load_snapshot(baseline["snapshot_digest"]) if baseline else None
        return change, snapshot, before

    def check(self, change_id=None, compare_incremental=False):
        change, snapshot, before = self.context(change_id)
        result = check_snapshot(snapshot, before, self.store.history(), compare_incremental)
        restored = set(change.get("restored_ids", []))
        result.findings = [f for f in result.findings if not (f.code == "RETIRED_ID_REUSE" and set(f.subjects) <= restored)]
        result.details["change_id"] = change["change_id"]
        return result

    def review(self, change_id=None, provider=None, force=False):
        change, snapshot, before = self.context(change_id)
        deterministic = self.check(change["change_id"])
        if deterministic.status != Status.PASS:
            return {"status": deterministic.status.value, "change_id": change["change_id"], "deterministic": deterministic.to_dict(), "jobs": []}
        observations = latest_observations(self.store, snapshot)
        shared_graph = build_graph(snapshot)
        jobs = []
        for obligation in obligations_for_review(snapshot, before):
            try:
                packet = make_packet(snapshot, obligation, before, observations, graph=shared_graph)
            except SddError as exc:
                jobs.append({"status": "INCOMPLETE", "obligation_id": obligation["id"], "error": exc.to_dict()})
                continue
            previous = self._review_for(packet["packet_digest"])
            if previous and previous["status"] == "COMPLETE" and self._review_current(previous, snapshot) and not force:
                jobs.append({**previous, "reused": True})
                continue
            rejected = [j for j in self.store.list("review_jobs")
                        if j["change_id"] == change["change_id"] and j["obligation_id"] == obligation["id"]
                        and any(c["status"] == "fail" for c in j.get("coverage", []))]
            if len(rejected) >= effective_policy(snapshot, before).get("max_rejected_rounds", 2):
                jobs.append({"status": "INCOMPLETE", "obligation_id": obligation["id"],
                             "error": {"code": "REVIEW_ROUND_LIMIT", "message": "Change the candidate or request human adjudication"}})
                continue
            job_id = "REV-" + uuid.uuid4().hex
            job = {"review_id": job_id, "snapshot_digest": snapshot.digest, "packet_digest": packet["packet_digest"],
                   "change_id": change["change_id"], "obligation_id": obligation["id"], "started_at": self.clock(), "status": "RUNNING",
                   "implementation_binding": self._implementation_binding(snapshot)}
            with self.store.lock():
                job["sequence"] = 1 + max((j.get("sequence", 0) for j in self.store.list("review_jobs")), default=0)
                self.store.write("packets", packet["packet_digest"], packet, immutable=True)
                self.store.write("review_jobs", job_id, job)
            selected = provider
            try:
                if selected is None:
                    config = resolve_provider_config(snapshot.config.get("provider"), self.workspace)
                    if not config:
                        raise SddError("PROVIDER_NOT_CONFIGURED", "Configure one judge provider in sdd-workspace.yml or set JEV_API_KEY / SDD_JUDGE_API_KEY in .env", Status.INCOMPLETE)

                    from .budget import Budget, candidate_root
                    budget = Budget(self.store, candidate_root(self.store, change), float(config.get("max_cost_usd", 5.0)))
                    selected = build_provider(config, reserve=budget.reserve)
                response = selected.review(packet)
                verdict = verify_review(response, packet)
                job.update(verdict)
            except SddError as exc:
                job.update({"status": "INCOMPLETE", "error": exc.to_dict(), "coverage": [], "findings": []})
            except Exception as exc:
                job.update({"status": "ERROR", "error": {"code": "JUDGE_INTERNAL_ERROR", "type": type(exc).__name__}, "coverage": [], "findings": []})
            job["finished_at"] = self.clock()
            job["telemetry"] = getattr(selected, "calls", [])
            with self.store.lock():
                try:
                    self.context(change["change_id"])
                    if observations != latest_observations(self.store, snapshot):
                        job["status"] = "STALE"
                except SddError:
                    job["status"] = "STALE"
                self.store.write("review_jobs", job_id, job)
            jobs.append(job)
        status = "PASS" if all(j["status"] == "COMPLETE" for j in jobs) else "INCOMPLETE"
        if status == "PASS":
            verdicts = [c["status"] for j in jobs for c in j.get("coverage", [])]
            if any(v in {"unknown", "intentionally_changed"} for v in verdicts):
                status = "INCOMPLETE"
            elif "fail" in verdicts:
                status = "FAIL"
        return {"status": status, "change_id": change["change_id"], "jobs": jobs}

    def _review_for(self, packet_digest):
        candidates = [j for j in self.store.list("review_jobs") if j["packet_digest"] == packet_digest]
        return max(candidates, key=lambda j: (j.get("sequence", 0), j.get("started_at", ""), j["review_id"]), default=None)

    def _implementation_binding(self, snapshot):
        from .evaluation import provider_binding
        return provider_binding(resolve_provider_config(snapshot.config.get("provider"), self.workspace))

    def _review_current(self, review, snapshot):
        if review.get("implementation_binding") != self._implementation_binding(snapshot):
            return False
        finished = review.get("finished_at")
        if not finished:
            return False
        time = instant(self.clock())
        return instant(finished) <= time < instant(finished) + timedelta(seconds=snapshot.config["policy"].get("max_review_age_seconds", 30 * 86400))

    def readiness(self, change_id=None):
        if change_id is None:
            baseline = self.store.baseline()
            if baseline and capture(self.workspace).digest == baseline["snapshot_digest"]:
                return self.baseline_readiness()
        change, snapshot, before = self.context(change_id)
        return self._readiness(change, snapshot, before)

    def baseline_readiness(self):
        baseline = self.store.baseline()
        if baseline is None:
            raise SddError("BASELINE_MISSING", "No accepted snapshot")
        certificate = self.store.read("acceptances", baseline["acceptance_id"])
        snapshot = self.store.load_snapshot(baseline["snapshot_digest"])
        if snapshot.engine_version != __version__:
            raise SddError("ENGINE_VERSION_STALE", "Reconcile and review with the current engine", Status.STALE)
        previous = self.store.read("acceptances", certificate["previous_acceptance"]) if certificate["previous_acceptance"] else None
        before = self.store.load_snapshot(previous["snapshot_digest"]) if previous else None
        change = self.store.read("changes", certificate["change_id"])
        if change is None:
            raise SddError("BASELINE_CORRUPT", "Acceptance has no change record")
        return self._readiness(change, snapshot, before)

    def _readiness(self, change, snapshot, before):
        result = check_snapshot(snapshot, before, self.store.history(), compare_incremental=True)
        restored = set(change.get("restored_ids", []))
        result.findings = [f for f in result.findings if not (f.code == "RETIRED_ID_REUSE" and set(f.subjects) <= restored)]
        result.details["change_id"] = change["change_id"]
        decisions = valid_decisions(self.store, snapshot, before, self.clock(), base_acceptance=change["base_acceptance"])
        policy = effective_policy(snapshot, before)
        if policy["mode"] == "enforce" and snapshot.config.get("provider"):
            from .evaluation import qualification_current
            if not qualification_current(self.store, snapshot.config["provider"], self.clock(), snapshot.config.get("workspace_profile_id")):
                result.findings.append(Finding("JUDGE_QUALIFICATION_REQUIRED", "Approve held-out labels and run a qualifying live evaluation before enforced API acceptance", (), Status.INCOMPLETE))
        observations = latest_observations(self.store, snapshot)
        historical = result.details["historical_changes"]
        for subject, delta in historical.items():
            if (delta["kind"] in {"contract_change", "policy_change"} or delta.get("source_fact_changes")) and not covering(decisions, "change_obligation", subject):
                result.findings.append(Finding("HISTORICAL_CHANGE_UNAPPROVED", f"Review the before/after change for {subject}",
                                               (subject,), Status.INCOMPLETE, obligation_id=subject))
        if before:
            for identifier in set(before.artifacts) & set(snapshot.artifacts):
                if before.artifacts[identifier].owner != snapshot.artifacts[identifier].owner and not covering(decisions, "transfer_owner", identifier):
                    result.findings.append(Finding("OWNERSHIP_TRANSFER_UNAPPROVED", identifier, (identifier,), Status.INCOMPLETE))
        shared_graph = build_graph(snapshot)
        coverage, risks, dispositions = [], [], []
        for obligation in obligations_for_review(snapshot, before):
            identifier = obligation["id"]
            manual = covering(decisions, "manual_review", identifier)
            try:
                packet = make_packet(snapshot, obligation, before, observations, graph=shared_graph)
            except SddError as exc:
                result.findings.append(Finding(exc.code, str(exc), (), exc.status, obligation_id=identifier))
                coverage.append({"obligation_id": identifier, "status": "UNKNOWN"})
                continue
            review = self._review_for(packet["packet_digest"])
            if review is None or review["status"] != "COMPLETE":
                # A later transport/schema failure does not erase the last
                # confirmed blocker, even when a manual review is supplied.
                completed = [j for j in self.store.list("review_jobs") if j["packet_digest"] == packet["packet_digest"] and j["status"] == "COMPLETE"]
                prior = max(completed, key=lambda j: j.get("sequence", 0), default=None)
                if prior and any(f["severity"] == "blocker" for f in prior.get("findings", [])):
                    review = prior | {"current_attempt_incomplete": True}
            if review is None or review["status"] != "COMPLETE":
                if manual:
                    coverage.append({"obligation_id": identifier, "status": "CURRENT", "via": "human", "decision_id": manual[-1]["decision_id"]})
                    continue
                result.findings.append(Finding("SEMANTIC_REVIEW_REQUIRED", f"Complete review or explicit human evidence for {identifier}", (), Status.INCOMPLETE, obligation_id=identifier))
                coverage.append({"obligation_id": identifier, "status": "UNKNOWN"})
                continue
            current_review = self._review_current(review, snapshot) and not review.get("current_attempt_incomplete", False)
            if not current_review and not manual:
                result.findings.append(Finding("SEMANTIC_REVIEW_REQUIRED", "Current review is incomplete or expired", (), Status.INCOMPLETE, obligation_id=identifier))
            verified = verify_review(review["response"], packet)
            if verified["status"] != "COMPLETE":
                if manual:
                    coverage.append({"obligation_id": identifier, "status": "CURRENT", "via": "human", "decision_id": manual[-1]["decision_id"]})
                    continue
                result.findings.append(Finding("REVIEW_RECORD_INVALID", identifier, (), Status.INCOMPLETE, obligation_id=identifier))
                continue
            verdict = verified["coverage"][0]["status"]
            blockers = [f for f in verified["findings"] if f["severity"] == "blocker"]
            unresolved = []
            for finding in blockers:
                dismissed = [d for d in covering(decisions, "false_positive", identifier)
                             if d.get("packet_digest") == packet["packet_digest"] and finding["finding_id"] in d.get("finding_ids", [])]
                waived = [d for d in covering(decisions, "waiver", identifier)
                          if policy.get("allow_waivers", False) and d.get("packet_digest") == packet["packet_digest"]
                          and finding["finding_id"] in d.get("finding_ids", [])]
                if dismissed:
                    dispositions.append({"finding": finding, "decision": dismissed[-1], "status": "FALSE_POSITIVE"})
                elif waived:
                    risks.append({"finding": finding, "decision": waived[-1], "status": "WAIVED"})
                else:
                    unresolved.append(finding)
                    result.findings.append(Finding(finding["code"], finding["message"], tuple(finding["subjects"]),
                                                   obligation_id=identifier, evidence=tuple(finding["evidence"])))
            if verdict == "unknown" and not manual:
                result.findings.append(Finding("JUDGE_UNKNOWN", identifier, (), Status.INCOMPLETE, obligation_id=identifier))
            elif verdict == "intentionally_changed" and not covering(decisions, "change_obligation", identifier):
                result.findings.append(Finding("HISTORICAL_CHANGE_UNAPPROVED", identifier, (), Status.INCOMPLETE, obligation_id=identifier))
            if policy["mode"] in {"shadow", "advisory"} and not manual:
                result.findings.append(Finding("HUMAN_SEMANTIC_REVIEW_REQUIRED", "Judge is advisory; record a manual review with evidence", (), Status.INCOMPLETE, obligation_id=identifier))
            passed = not unresolved and (bool(manual) or (verdict != "unknown" and policy["mode"] == "enforce" and current_review))
            coverage.append({"obligation_id": identifier, "status": "CURRENT" if passed else "UNKNOWN", "via": "human" if manual else "judge", "review_id": review["review_id"]})
        fresh_findings, fresh_details = freshness(self.store, snapshot, self.clock(), before)
        result.findings.extend(fresh_findings)
        if policy.get("require_human_acceptance", True) and not covering(decisions, "accept", snapshot.config["workspace_id"]):
            result.findings.append(Finding("HUMAN_ACCEPTANCE_REQUIRED", "Record acceptance for this exact snapshot", (), Status.INCOMPLETE))
        result.details.update({"semantic_coverage": coverage, "freshness": fresh_details,
                               "accepted_risks": risks, "dispositions": dispositions,
                               "decision_ids": [d["decision_id"] for d in decisions],
                               "clean": not risks and not dispositions and result.status == Status.PASS,
                               "next_action": "accept" if result.status == Status.PASS else "resolve_findings"})
        return result

    def accept(self, change_id, expected_snapshot, operation_id=None):
        operation_id = operation_id or "ACC-" + uuid.uuid4().hex
        with self.store.lock():
            journal = self.store.read("journal", operation_id)
            if journal:
                if journal["change_id"] != change_id or journal["snapshot_digest"] != expected_snapshot:
                    raise SddError("OPERATION_CONFLICT", operation_id, Status.STALE)
                if journal["phase"] == "COMMITTED":
                    return self.store.read("acceptances", operation_id)
                if journal["phase"] == "ABORTED":
                    raise SddError("OPERATION_ABORTED", "Use a new operation ID after an aborted transaction", Status.INCOMPLETE)
                self._recover_locked()
                journal = self.store.read("journal", operation_id)
                if journal["phase"] == "COMMITTED":
                    return self.store.read("acceptances", operation_id)
                if journal["phase"] == "ABORTED":
                    raise SddError("OPERATION_ABORTED", "Use a new operation ID after recovery", Status.INCOMPLETE)
            change, snapshot, before = self.context(change_id)
            if expected_snapshot != snapshot.digest:
                raise SddError("EXPECTED_REVISION_CONFLICT", "Accept requires the exact candidate digest", Status.STALE)
            readiness = self.readiness(change_id)
            if readiness.status != Status.PASS:
                raise SddError("ACCEPTANCE_BLOCKED", __import__("json").dumps(readiness.to_dict(), ensure_ascii=False), readiness.status)
            old = self.store.baseline()
            previous_ids = set(before.artifacts) if before else set()
            if before:
                previous_ids |= {c for a in before.artifacts.values() for c in a.clauses}
            current_ids = set(snapshot.artifacts) | {c for a in snapshot.artifacts.values() for c in a.clauses}
            certificate = {"acceptance_id": operation_id, "snapshot_digest": snapshot.digest,
                           "origin_snapshot": change["origin_snapshot"],
                           "previous_acceptance": old["acceptance_id"] if old else None,
                           "previous_certificate_digest": old["certificate_digest"] if old else None,
                           "accepted_at": self.clock(), "engine_version": __version__, "change_id": change_id,
                           "tombstones": sorted(previous_ids - current_ids),
                           "revision_ids": {i: operation_id + ":" + i for i in sorted(current_ids)},
                           "readiness": readiness.to_dict(), "observations": latest_observations(self.store, snapshot),
                           "verdict": "ACCEPTED_WITH_RISK" if readiness.details["accepted_risks"] else "ACCEPTED"}
            record = {"operation_id": operation_id, "change_id": change_id, "snapshot_digest": snapshot.digest,
                      "phase": "PREPARED", "previous_pointer": old, "certificate_digest": digest(certificate)}
            self.store.write("acceptances", operation_id, certificate, immutable=True)
            self.store.write("journal", operation_id, record)
            self.fault("prepared")
            # Reconcile again immediately before publication. This compares the
            # origin workspace; a proposal's separate frozen candidate may differ.
            self.context(change_id)
            if certificate["observations"] != latest_observations(self.store, snapshot):
                raise SddError("OBSERVATION_CHANGED", "External evidence changed", Status.STALE)
            record["phase"] = "COMMITTING"
            self.store.write("journal", operation_id, record)
            self.fault("committing")
            pointer = {"acceptance_id": operation_id, "snapshot_digest": snapshot.digest, "certificate_digest": digest(certificate)}
            self.store.write("state", "baseline", pointer)
            self.fault("published")
            record["phase"] = "COMMITTED"
            self.store.write("journal", operation_id, record)
            return certificate

    def _recover_locked(self):
        accepted = {c["acceptance_id"] for c in self.store.history()}
        recovered = []
        for record in self.store.list("journal"):
            if record["phase"] not in {"PREPARED", "COMMITTING"}:
                continue
            record["phase"] = "COMMITTED" if record["operation_id"] in accepted else "ABORTED"
            self.store.write("journal", record["operation_id"], record)
            recovered.append(record)
        return recovered

    def recover(self):
        with self.store.lock():
            return {"status": "PASS", "transactions": self._recover_locked()}
