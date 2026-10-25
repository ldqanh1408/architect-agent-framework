"""specification / W-2 — `GATE-EVIDENCE-VOCAB`: the vocabulary and the manifests agree.

Native from birth (R-2). The gate answers one question: does every
`when: evidence.has('x')` in the 110 per-skill manifests resolve to a defined
token, and does every defined token have a consumer?

Both directions matter, and for different reasons:

  **UNDEFINED** — a manifest gating a slot on a token nobody defined. The slot's
  condition is then a string nobody can argue with, which is the state the
  vocabulary was built to end.

  **UNUSED** — a definition nothing consumes. It rots quietly, and the next reader
  cannot tell whether it is dead or merely early.

It also grades the vocabulary's own discipline, because a detector that disagrees
with its own examples is worse than no detector: it looks tested.
"""

from __future__ import annotations

import re

from architect_framework import contracts, skillpacks
from architect_framework.gates.base import Finding, GateContext, GateResult

#: Tokens the section 5b harvest introduces. They may be defined before a manifest gates
#: anything on them, because the slots they admit arrive in specification.
HARVEST = frozenset({
    "cross_module_mechanism", "release_surface", "visual_view_required", "feature_cluster",
})

_USES = re.compile(r"evidence\.has\('([a-z_]+)'\)")


def _fires(token: dict, text: str) -> bool:
    if any(re.search(p, text, re.I) for p in token["detector"].get("none") or []):
        return False
    return any(re.search(p, text, re.I) for p in token["detector"]["any"])


class EvidenceVocabularyGate:
    """`GATE-EVIDENCE-VOCAB`."""

    id = "GATE-EVIDENCE-VOCAB"

    def applies_to(self, ctx: GateContext) -> str | None:
        if not contracts.available("evidence-vocabulary"):
            # Not a skip. The vocabulary is the contract this gate exists to check;
            # its absence is the finding, not a reason to stay quiet.
            return None
        return None

    def run(self, ctx: GateContext) -> GateResult:
        findings: list[Finding] = []

        if not contracts.available("evidence-vocabulary"):
            return GateResult(
                gate_id=self.id, exit_code=1,
                findings=[Finding(
                    code="VOCAB-MISSING",
                    message=f"{contracts.path_of('evidence-vocabulary')} does not exist; "
                            "every manifest `when:` is unresolvable until it does",
                )],
            )

        try:
            vocab = contracts.evidence_tokens()
        except contracts.ContractError as exc:
            return GateResult(
                gate_id=self.id, exit_code=1,
                findings=[Finding(code="VOCAB-UNPARSEABLE", message=str(exc))],
            )

        used: dict[str, set[str]] = {}
        # The manifests are the core's generation, so a core install checks the
        # generated catalogue; the repository checks the pack it ships.
        catalog = ctx.catalog or skillpacks.installed_catalogue() or skillpacks.catalogue_root()
        for path in (catalog / "domains").glob("*/*/workspace-template.yml"):
            for token in _USES.findall(path.read_text(encoding="utf-8", errors="replace")):
                used.setdefault(token, set()).add(path.parent.name)

        for token in sorted(set(used) - set(vocab)):
            findings.append(Finding(
                code="VOCAB-UNDEFINED",
                message=f"{token!r} gates a slot in {len(used[token])} manifest(s) "
                        f"(e.g. {sorted(used[token])[0]}) but is defined nowhere",
            ))

        # specification: a `status: proposed` token is defined and tested but waits on a
        # named human decision before any slot may gate on it. Unused is its correct
        # state; used is the defect, because the decision was skipped.
        proposed = {t for t, row in vocab.items() if str(row.get("status") or "") == "proposed"}
        for token in sorted(proposed):
            if not str(vocab[token].get("decision") or "").strip():
                findings.append(Finding(
                    code="VOCAB-PROPOSED-NO-DECISION",
                    message=f"{token!r} is `status: proposed` but names no `decision:`; a token "
                            "waiting on nobody in particular is waiting forever",
                ))
            if token in used:
                findings.append(Finding(
                    code="VOCAB-PROPOSED-IN-USE",
                    message=f"{token!r} gates a slot in {len(used[token])} manifest(s) "
                            f"(e.g. {sorted(used[token])[0]}) while still awaiting "
                            f"{vocab[token].get('decision') or 'its decision'}",
                ))

        for token in sorted(set(vocab) - set(used) - HARVEST - proposed):
            findings.append(Finding(
                code="VOCAB-UNUSED",
                message=f"{token!r} is defined but no manifest gates anything on it. "
                        "Either a slot should, or the definition is dead",
            ))

        for token_id, token in sorted(vocab.items()):
            examples = token.get("examples") or {}
            positive = examples.get("positive") or []
            negative = examples.get("negative") or []
            if len(positive) < 2 or len(negative) < 2:
                findings.append(Finding(
                    code="VOCAB-EXAMPLES-THIN",
                    message=f"{token_id}: {len(positive)} positive / {len(negative)} negative "
                            "examples; a detector with only positives has been demonstrated, "
                            "not tested",
                ))
            for text in positive:
                if not _fires(token, text):
                    findings.append(Finding(
                        code="VOCAB-EXAMPLE-DISAGREES",
                        message=f"{token_id}: its own positive example does not fire — {text[:90]!r}",
                    ))
            for text in negative:
                if _fires(token, text):
                    findings.append(Finding(
                        code="VOCAB-EXAMPLE-DISAGREES",
                        message=f"{token_id}: its own negative example fires — {text[:90]!r}",
                    ))
            if set(token.get("detector") or {}) - {"any", "none"}:
                findings.append(Finding(
                    code="VOCAB-DETECTOR-SHAPE",
                    message=f"{token_id}: a detector has only `any` and `none`. There is no way to "
                            "express 'fire when this is missing', and that is deliberate",
                ))

        errors = sum(1 for f in findings if f.severity == "error")
        summary = (
            f"{self.id}\n"
            f"tokens defined: {len(vocab)} (proposed {len(proposed)}) · used by manifests: {len(used)} · "
            f"UNDEFINED {sum(1 for f in findings if f.code == 'VOCAB-UNDEFINED')} · "
            f"UNUSED {sum(1 for f in findings if f.code == 'VOCAB-UNUSED')}\n"
            f"findings: {errors} error(s)"
        )
        return GateResult(
            gate_id=self.id,
            exit_code=0 if errors == 0 else 1,
            findings=findings,
            stdout=summary,
        )
