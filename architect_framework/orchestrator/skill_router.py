from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

from architect_framework.registry.domain_registry import DomainRegistry
from architect_framework.registry.task_registry import TaskRegistry


ORCHESTRATOR_SKILL_ID = "architect-skill-orchestrator"

CLUSTER_ALIASES: dict[str, str] = {
    "01_frontend_architecture": "03_application_architecture",
    "02_mobile_edge": "03_application_architecture",
    "05_data_analytics": "05_data_architecture",
    "06_cloud_infrastructure": "06_infrastructure_architecture",
}

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "a", "an", "and", "architecture", "architect", "design", "for", "in", "of",
    "or", "the", "to", "with", "system", "technical", "task", "skill",
    # Function words. Measured 2026-09-24: once specification gave the ten AI skills one
    # shared module set, `that`/`one` against `by` decided who owned the AI gateway
    # (10 to 9). A word that carries no domain meaning must not break a tie.
    "that", "one", "by", "over", "behind", "on", "is", "it", "as", "at",
}


class RoutingError(ValueError):
    """Fail-closed routing error with candidates for explicit user/agent choice."""


@dataclass(frozen=True)
class RouteCandidate:
    domain_skill_id: str
    task_skill_id: str
    domain_score: int
    task_score: int
    combined_score: int


@dataclass(frozen=True)
class RouteDecision:
    status: str
    query: str
    selected_domain: str | None
    selected_task: str | None
    candidates: tuple[RouteCandidate, ...]
    load_paths: tuple[str, ...]
    reason: str

    def to_dict(self) -> dict:
        data = asdict(self)
        data["candidates"] = [asdict(item) for item in self.candidates]
        return data


#: Two words that mean one thing together (specification). "C4 container diagram" is a diagram level,
#: not a Docker container; collapsing the pair to a single token, on the query and on every
#: name and description alike, keeps the word "container" from matching the wrong skill.
_PHRASES = re.compile(r"\bc4[\s-]+(container|context|component|code)s?\b")

#: Abbreviations a person types that no skill name spells out (specification). Applied to the QUERY
#: only: a skill's own words are never expanded. Each value is vocabulary the skill's own name
#: or description already carries, so nothing is invented to make one prompt pass.
QUERY_ALIASES: dict[str, tuple[str, ...]] = {
    "adr": ("decision", "record", "documentation"),
    "adrs": ("adr", "decision", "record", "documentation"),
    "rfc": ("decision", "documentation"),
    "agents": ("agent",),
    "c4container": ("diagram", "c4"),
    "c4context": ("diagram", "c4"),
    "c4component": ("diagram", "c4"),
}


def _tokens(values: Iterable[str], collapse: bool = False) -> set[str]:
    tokens: set[str] = set()
    for value in values:
        text = str(value).lower()
        if collapse:
            text = _PHRASES.sub(lambda m: "c4" + m.group(1), text)
        tokens.update(token for token in _TOKEN_RE.findall(text) if token not in _STOPWORDS and len(token) > 1)
    return tokens


def _query_tokens(query: str) -> set[str]:
    """The tokens of a request, with its abbreviations expanded."""
    text = re.sub(r"\bhand\s+work\s+to\s+each\s+other\b", "handoff workflow", query.lower())
    tokens = _tokens((text,), collapse=True)
    for token in sorted(tokens):
        tokens.update(QUERY_ALIASES.get(token, ()))
    if "agent" in tokens and re.search(r"\bhand\s+work\s+to\s+each\s+other\b", query.lower()):
        tokens.update(("workflow", "handoff", "orchestration"))
    return tokens


# --------------------------------------------------------------------------- #
# specification — the routing corpus
#
# A domain's routing vocabulary was three `concerns`, one `viewpoint` and a
# one-line description: roughly fifteen tokens for each of 110 skills. Far too
# thin to discriminate, and the scores showed it — `gateway-architect` and
# `backend-service-architect` both scored 5 on a query full of "WebSocket
# gateway", because one name token plus one description token is all either could
# match.
#
# Measured on the seven Crosstalk module intents: 3 of 7 owners correct.
#
# The fix reuses vocabulary that is ALREADY AUTHORED and already has an owner —
# each package's `workspace-template.yml` (archetype, concern-module ids,
# consumers, cadence, approver) and the opening of its `SKILL.md`. Nothing new to
# maintain, and no keyword list invented to make one workspace green. That took
# the same seven intents to 5 of 7, fixing mobile-architect (which had been
# unreachable), storage-architect and microservice-architect.
# --------------------------------------------------------------------------- #

_CORPUS_CACHE: dict[str, tuple[str, ...]] = {}


def _slot_homes_map() -> dict[str, Path]:
    from architect_framework import skillpacks
    homes = {k: p.home for k, p in skillpacks.shipped().items()}
    for k, p in skillpacks.installed().items():
        if p.contract is not None:
            homes[k] = p.home
    return homes


def _package_corpus(skill_id: str, homes: dict[str, Path] | None = None) -> tuple[str, ...]:
    """Authored routing vocabulary from a skill's installed package.

    A skill whose pack is not installed has no corpus; it is still routable on
    its catalogue name and fields, which is what `_score` weighs most.
    """
    if skill_id in _CORPUS_CACHE:
        return _CORPUS_CACHE[skill_id]
    import yaml as _yaml

    from architect_framework import skillpacks

    out: list[str] = []
    found = homes.get(skill_id) if homes is not None else skillpacks.slot_home(skill_id)
    if found is not None:
        package = found
        manifest = package / "workspace-template.yml"
        if manifest.is_file():
            try:
                _loader = getattr(_yaml, "CSafeLoader", _yaml.SafeLoader)
                data = _yaml.load(manifest.read_text(encoding="utf-8"), Loader=_loader) or {}
            except Exception:
                data = {}
            resolution = data.get("output_module_resolution") or {}
            out.append(str(resolution.get("archetype") or ""))
            for module in data.get("output_modules") or []:
                out.append(str(module.get("id", "")))
                out.extend(str(c) for c in (module.get("consumers") or []))
                out.append(str(module.get("cadence", "")))
                out.append(str(module.get("approver", "")))
        skill_md = package / "SKILL.md"
        if skill_md.is_file():
            words = skill_md.read_text(encoding="utf-8", errors="replace").split()
            out.append(" ".join(words[:180]))
    _CORPUS_CACHE[skill_id] = tuple(x for x in out if x)
    return _CORPUS_CACHE[skill_id]


def _score(query_tokens: set[str], name: str, identifier: str, fields: Iterable[str], collapse: bool = False) -> int:
    name_tokens = _tokens((name, identifier), collapse)
    field_tokens = _tokens(fields, collapse)
    return 4 * len(query_tokens & name_tokens) + len(query_tokens & field_tokens)


class ProgressiveSkillRouter:
    """Route from compact registry metadata without loading leaf SKILL.md bodies."""

    def __init__(
        self,
        domain_registry: DomainRegistry | None = None,
        task_registry: TaskRegistry | None = None,
    ):
        self.domain_registry = domain_registry or DomainRegistry()
        self.task_registry = task_registry or TaskRegistry()

    def catalog(self, cluster_id: str | None = None, family_id: str | None = None) -> dict:
        cluster_id = CLUSTER_ALIASES.get(cluster_id or '', cluster_id)
        domains = [
            {
                "id": skill.id,
                "name": skill.name,
                "cluster_id": skill.cluster_id,
                "description": skill.description,
                "concerns": skill.concerns,
                "compatible_task_families": skill.compatible_task_families,
            }
            for skill in self.domain_registry.list_all_skills()
            if cluster_id is None or skill.cluster_id == cluster_id
        ]
        tasks = []
        for task in self.task_registry.list_all_tasks():
            family = self.task_registry.get_family_for_task(task.id)
            if family_id is not None and family.id != family_id:
                continue
            tasks.append({
                "id": task.id,
                "name": task.name,
                "family_id": family.id,
                "description": task.description,
                "compatible_domain_clusters": task.compatible_domain_clusters,
            })
        return {"domains": domains, "tasks": tasks}

    def route(
        self,
        query: str,
        domain_skill_id: str | None = None,
        task_skill_id: str | None = None,
        candidate_limit: int = 5,
        cluster_id: str | None = None,
        *,
        open_families: bool = False,
    ) -> RouteDecision:
        """Rank execution points for a request.

        `open_families` is for a person's request (`route-skills`, specification): a task family no domain
        names is compatible with every domain, and a tie that one domain's own name breaks is broken.
        The charter, which records this ranking as evidence, leaves it off, so the committed charters
        and the decisions signed over them keep reproducing.
        """
        query_tokens = _query_tokens(query) if open_families else _tokens((query,))
        if not query_tokens and not (domain_skill_id and task_skill_id):
            return RouteDecision("blocked", query, None, None, (), (), "query has no discriminating routing terms")

        cluster_id = CLUSTER_ALIASES.get(cluster_id or '', cluster_id)
        explicit_domain = self.domain_registry.get_skill(domain_skill_id) if domain_skill_id else None
        explicit_task = self.task_registry.get_task(task_skill_id) if task_skill_id else None
        if domain_skill_id and explicit_domain is None:
            raise RoutingError(f"unknown domain skill: {domain_skill_id}")
        if task_skill_id and explicit_task is None:
            raise RoutingError(f"unknown task skill: {task_skill_id}")
        if cluster_id and explicit_domain and explicit_domain.cluster_id != cluster_id:
            raise RoutingError(
                f"domain skill {domain_skill_id} belongs to cluster {explicit_domain.cluster_id}, not {cluster_id}"
            )

        # G-A (specification section 9.1): hop-1 narrowing (slug→tier→cluster) must be
        # enforceable through the router's API, not just documented. When cluster_id
        # is given, only domain skills in that cluster are scored.
        domains = [explicit_domain] if explicit_domain else [
            s for s in self.domain_registry.list_all_skills()
            if cluster_id is None or s.cluster_id == cluster_id
        ]
        tasks = [explicit_task] if explicit_task else self.task_registry.list_all_tasks()
        if not domains and not domain_skill_id and not cluster_id and open_families:
            ranked_tasks=sorted(((1000 if explicit_task else _score(query_tokens,t.name,t.id,
                (t.description,*t.procedural_steps,*t.expected_outputs,*t.inputs_required),True),t) for t in tasks),
                key=lambda item:(-item[0],item[1].id))
            ranked_tasks=[(score,t) for score,t in ranked_tasks if score>=2]
            shortlist=tuple(RouteCandidate('',t.id,0,score,score) for score,t in ranked_tasks[:candidate_limit])
            if not ranked_tasks:return RouteDecision('blocked',query,None,None,(),(),'no installed task matched; install the required package')
            if len(ranked_tasks)>1 and ranked_tasks[0][0]==ranked_tasks[1][0]:
                return RouteDecision('ambiguous',query,None,None,shortlist,(),'installed tasks are tied; select an explicit ID')
            winner=ranked_tasks[0][1];family=self.task_registry.get_family_for_task(winner.id)
            paths=(f'tasks/{family.id}/{winner.id}/SKILL.md',f'tasks/{family.id}/{winner.id}/skill-contract.yml')
            return RouteDecision('selected',query,None,winner.id,shortlist,paths,'installed task selected; no domain owner is inferred')
        candidates: list[RouteCandidate] = []
        # A task family no domain names (documentation, system modelling, testing, ...) has no
        # compatibility to enforce: every domain would be "incompatible" and its tasks, among
        # them the free `adr-authoring`, could never be selected (specification).
        declared_families = ({f for s in self.domain_registry.list_all_skills() for f in s.compatible_task_families}
                             if open_families else None)
        _homes = None if explicit_domain else _slot_homes_map()
        for domain in domains:
            domain_score = 1000 if explicit_domain else _score(
                query_tokens,
                domain.name,
                domain.id,
                (*domain.concerns, *domain.viewpoints, domain.description,
                 *_package_corpus(domain.id, _homes)),
                open_families,
            )
            for task in tasks:
                family = self.task_registry.get_family_for_task(task.id)
                if domain.compatible_task_families and family.id not in domain.compatible_task_families and (
                        declared_families is None or family.id in declared_families):
                    continue
                if task.compatible_domain_clusters and domain.cluster_id not in task.compatible_domain_clusters:
                    continue
                task_score = 1000 if explicit_task else _score(
                    query_tokens,
                    task.name,
                    task.id,
                    (task.description, *task.procedural_steps, *task.expected_outputs, *task.inputs_required),
                    open_families,
                )
                if not explicit_domain and domain_score == 0:
                    continue
                if not explicit_task and task_score == 0:
                    continue
                candidates.append(RouteCandidate(domain.id, task.id, domain_score, task_score, domain_score + task_score))

        ranked = sorted(candidates, key=lambda item: (-item.combined_score, item.domain_skill_id, item.task_skill_id))
        shortlist = tuple(ranked[:candidate_limit])
        if not ranked:
            return RouteDecision("blocked", query, None, None, (), (), "no compatible domain-task execution point matched")
        if len(ranked) > 1 and ranked[0].combined_score == ranked[1].combined_score:
            # Tied on score, one domain whose own name the request uses: that is the owner
            # ("C4 container diagram" names `diagram-architect`, not `container-architect`, specification).
            tied = [c for c in ranked if c.combined_score == ranked[0].combined_score]
            named = sorted(((len(query_tokens & _tokens((c.domain_skill_id,), True)), c) for c in tied),
                           key=lambda item: -item[0])
            if open_families and len({c.task_skill_id for c in tied}) == 1 and named[0][0] > named[1][0]:
                ranked = [named[0][1], *[c for c in ranked if c is not named[0][1]]]
                shortlist = tuple(ranked[:candidate_limit])
            else:
                return RouteDecision("ambiguous", query, None, None, shortlist, (), "top execution points are tied; select explicit IDs")
        winner = ranked[0]
        if winner.combined_score < (2000 if explicit_domain and explicit_task else 2):
            return RouteDecision("blocked", query, None, None, shortlist, (), "routing confidence below deterministic threshold")
        load_paths = (
            f"domains/{self.domain_registry.get_skill(winner.domain_skill_id).cluster_id}/{winner.domain_skill_id}/SKILL.md",
            f"domains/{self.domain_registry.get_skill(winner.domain_skill_id).cluster_id}/{winner.domain_skill_id}/skill-contract.yml",
            f"tasks/{self.task_registry.get_family_for_task(winner.task_skill_id).id}/{winner.task_skill_id}/SKILL.md",
            f"tasks/{self.task_registry.get_family_for_task(winner.task_skill_id).id}/{winner.task_skill_id}/skill-contract.yml",
        )
        return RouteDecision("selected", query, winner.domain_skill_id, winner.task_skill_id, shortlist, load_paths, "unique compatible execution point selected")

def rank_domains(query: str, registry=None) -> list[tuple[int, str]]:
    """`[(score, domain_skill_id)]`, best first, scored on the DOMAIN only.

    specification. `route()` ranks **execution points** by `domain_score + task_score`,
    which lets *task* vocabulary decide the *owner*. Those are different questions,
    and the charter asks the narrower one: who owns this module. Measured on the
    seven Crosstalk intents, ranking on the domain alone gets 5 of 7 owners right
    where the combined ranking gets 4 — and the two it still misses are the pair
    that share the word "gateway", which is a vocabulary problem in those two
    packages rather than a scoring one.

    Kept separate from `route()` on purpose: nothing that already asks for an
    execution point changes behaviour.
    """
    from architect_framework.registry.domain_registry import DomainRegistry

    registry = registry or DomainRegistry()
    tokens = _tokens((query,))
    _homes = _slot_homes_map()
    scored = [
        (
            _score(tokens, domain.name, domain.id,
                   (*domain.concerns, *domain.viewpoints, domain.description,
                    *_package_corpus(domain.id, _homes))),
            domain.id,
        )
        for domain in registry.list_all_skills()
    ]
    return sorted(scored, key=lambda item: (-item[0], item[1]))


# --------------------------------------------------------------------------- #
# specification — the module-owner policy, stated once
#
# `route()` answers "which (domain, task) execution point runs". A module charter
# asks a narrower question: "which domain skill OWNS this module". Until specification the
# answer lived only in `gates/charter.py`, so `charter build` and an agent reading
# the orchestrator's SKILL.md could disagree on the same intent and nothing would
# notice. Both now call `select_module_owner`: `charter build` in-process, the
# agent through `scripts/route.py owner`. The rules are moved, not changed.
# --------------------------------------------------------------------------- #

#: Kept for the charter's re-export; `domain-unanimity` itself was removed by specification.
UNANIMITY_WINDOW = 3


def module_owner_verdict(intent: str, router: ProgressiveSkillRouter | None = None) -> dict:
    """The router verdict for one module intent, with the owner rules applied.

    The verdict is returned whole, not summarised. With one refinement, and it is a
    refinement rather than a workaround. The router reports `ambiguous` when the top
    **execution point** — a (domain, task) pair — is tied. The owner question needs
    only the **domain**, and the router was answering the harder one:

        query "API gateway routing and rate limiting"
        status ambiguous
        top 3  gateway-architect / gateway-architect / gateway-architect

    Rules, first match wins:

      ``domain-rank``       the domain ranking alone has a clear leader → `selected`,
                            with the router's own status kept as `router_status`.
      ``domain-rank-tie``   two or more domains tie at the top → `ambiguous`; the
                            tool names the tie and does not choose a boundary.

    Otherwise the router's own verdict stands, with no `resolved_by`: no domain
    scored above 0, and `route()` proposes a candidate only for a domain that
    does, so it cannot have selected. specification (2026-09-26) removed the two rules
    that handled that case, `router` and `domain-unanimity`: measured over the
    305 skill descriptions of the catalogue they fired 0 times.

    Whenever a rule overrides the router, the original status and the whole
    candidate list stay in the record, so a reader can see the rule was applied
    and disagree with it.
    """
    active_router = router or ProgressiveSkillRouter()
    verdict = dict(active_router.route(query=intent).to_dict())

    # Rank the domain alone and require a clear margin; on the seven Crosstalk
    # intents that is 5 of 7 against 4 of 7 for the combined ranking.
    ranked = rank_domains(intent, registry=active_router.domain_registry)
    if ranked and ranked[0][0] > 0 and (len(ranked) < 2 or ranked[0][0] > ranked[1][0]):
        verdict["router_status"] = verdict.get("status")
        verdict["status"] = "selected"
        verdict["selected_domain"] = ranked[0][1]
        verdict["resolved_by"] = "domain-rank"
        verdict["domain_ranking"] = [{"score": s, "domain": d} for s, d in ranked[:5]]
        return verdict

    # A TIE AT THE TOP OF THE DOMAIN RANKING IS A REAL AMBIGUITY, and it must not
    # fall through to `route()`. Falling through hands the decision back to the
    # execution-point ranking — the exact confound `rank_domains` was added to
    # remove — and that is how "the realtime WebSocket gateway that authenticates a
    # session and forwards messages" came to be owned by `service-mesh-architect`.
    # Three domains tied at 6 there, which is honest: the intent as written does
    # describe something any of the three could be. The tool's job is to say so and
    # name the tie, so the architect sharpens the description. Choosing for them
    # would be the tool inventing a boundary decision.
    if ranked and len(ranked) >= 2 and ranked[0][0] > 0 and ranked[0][0] == ranked[1][0]:
        tied = [d for s, d in ranked if s == ranked[0][0]]
        verdict["router_status"] = verdict.get("status")
        verdict["status"] = "ambiguous"
        verdict["selected_domain"] = None
        verdict["resolved_by"] = "domain-rank-tie"
        verdict["tied"] = tied
        verdict["reason"] = (
            f"{len(tied)} domains tie at {ranked[0][0]} on the domain ranking: "
            f"{', '.join(tied)}. Sharpen the module intent so one of them is clearly the owner; "
            "the tool will not choose a boundary for you"
        )
        verdict["domain_ranking"] = [{"score": s, "domain": d} for s, d in ranked[:5]]
        return verdict

    return verdict


def apply_owner_tiebreak(verdict: dict, owner: str, reason: str) -> tuple[dict, str]:
    """Apply an architect's `owner:` to a verdict. Returns `(verdict, refusal)`.

    The tool names a tie and refuses to choose (see :func:`module_owner_verdict`);
    this is the other half — where the architect chooses, in writing. It is
    accepted **only** inside the tie the tool named. An `owner:` that contradicts a
    clear selection is refused: that is an old decision the ranking has since
    moved away from, and silently honouring it would be the B-1 laundering the
    charter exists to stop.
    """
    if not reason:
        return verdict, f"`owner: {owner}` has no `owner_reason`; a boundary chosen by hand says why"
    ranking = verdict.get("domain_ranking") or []
    if verdict.get("resolved_by") == "domain-rank-tie":
        top = ranking[0]["score"] if ranking else None
        tied = list(verdict.get("tied") or [row["domain"] for row in ranking if row["score"] == top])
        if owner not in tied:
            return verdict, f"`owner: {owner}` is not among the tied domains {tied}"
        verdict = dict(verdict)
        verdict.update({
            "status": "selected",
            "selected_domain": owner,
            "resolved_by": "architect-tiebreak",
            "tied": tied,
            "owner_reason": reason,
        })
        return verdict, ""
    selected = str(verdict.get("selected_domain") or "")
    if verdict.get("status") == "selected" and selected == owner:
        return verdict, ""
    return verdict, (
        f"`owner: {owner}` but the router selected {selected or verdict.get('status')!r} with no tie. "
        "Re-read the intent: the declared owner no longer matches what the module is described as"
    )


def select_module_owner(
    intent: str,
    owner: str = "",
    owner_reason: str = "",
    router: ProgressiveSkillRouter | None = None,
) -> tuple[dict, str]:
    """specification: the one function that decides who owns a module.

    Returns `(verdict, refusal)`. `refusal` is empty unless the caller named an
    `owner` the policy will not accept. `charter build` and `route.py owner` both
    call this, so the two cannot disagree on `status`, `selected_domain` or
    `resolved_by` for the same intent.
    """
    verdict = module_owner_verdict(intent, router=router)
    if owner:
        return apply_owner_tiebreak(verdict, owner, owner_reason)
    return verdict, ""
