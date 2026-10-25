"""MOD-1: the per-skill concern-module vocabularies, as data.

`specification` section 4 states the rule this file encodes: **the
module set is per skill, not global.** A frontend skill has no event surface in
the backend sense; a data-platform skill has no UI state. A global slot list would
force every skill to carry slots it never fills, which is the empty-folder disease
the `when:` field exists to prevent.

section 2 states when a concern earns its own module:

    A concern becomes its own module when at least two of these three differ from
    the neighbouring concern: its consumers, its change cadence, or its approver.

That is why `consumers`, `cadence` and `approver` are fields here rather than
prose in a design doc: they are the recorded evidence for the test, so a later
proposal to merge or split two modules has to argue against data instead of taste.

Resolution order, and why the fallback is loud
----------------------------------------------
1. `SKILL_ARCHETYPE[(cluster_id, skill_id)]` -- the skill is declared against one
   of the ten archetypes.
2. `CLUSTER_DEFAULT_ARCHETYPE[cluster_id]` -- nothing claims the skill, so its
   cluster's stated default applies.

The second case is recorded on the resolution (`basis="cluster-default"`) and
rendered into the skill's own `output-contract.md`, because a fallback nobody can
see is indistinguishable from a decision nobody made. 87 of the 110 domain skills
resolve this way today; each one says so on its own page.

ID prefixes
-----------
section 3.2 fixes the prefix per concern module for the backend archetype and nothing
else, so the other nine archetypes need a rule rather than a table. The rule used
here maps a module to a prefix by *the kind of thing the module names*, drawing
only on prefixes the shared validator already accepts:

| Prefix   | The module names ...                                              |
|----------|-------------------------------------------------------------------|
| `API`    | a synchronous inbound surface someone calls                        |
| `MSG`    | an asynchronous message, event, hook or replay semantic            |
| `ENTITY` | owned state: an entity, dataset, artifact or term                  |
| `DEP`    | an outbound dependency, external provider or topology edge         |
| `SEC`    | a control obligation audited by a named reviewer                   |
| `OBS`    | a measured signal, budget or quality gate                          |
| `RES`    | failure behaviour: degradation, continuity, deprecation            |
| `ADR`    | a policy choice that could have gone the other way                 |
| `REQ`    | a normative constraint stated so it can be falsified               |

`SEC` `OBS` `RES` `DEP` were the four prefixes MOD-4 added to
`check_output_docs.py`'s stable-ID regex; `API` `MSG` `ENTITY` `ADR` `REQ` were
already there. MOD-4 has landed, so a page whose only stable IDs are `SEC-` reads
as specified rather than as "missing stable ID".

MOD-4 also reads this table the other way round: the leaf folder of each module's
`path` is rendered into the shipped validator as `CONCERN_MODULE_PREFIX`, so a
page under `12-events/` citing `API-007` is a `MODULE-PREFIX-MISMATCH`. That
rendering is generated from this dict (`SkillPackageGenerator.
_concern_module_prefix_literal`), never retyped -- which is why two modules of one
archetype may not share a prefix *and* why two archetypes may not give one folder
name two prefixes.

Prefixes are unique *within* an archetype (asserted at import), because a module
that shares a namespace with its sibling has not actually been separated.
"""

from __future__ import annotations

from dataclasses import dataclass

# Kept in step with ``production_package_generator.SHARED_DIR``; duplicated rather
# than imported so this module stays a leaf with no import cycle back into the
# generator that consumes it.
SHARED_DIR = "_shared"

# A page class resolves to exactly one B-template (T3). Adding a page class
# without a template here fails at import rather than emitting a contract that
# names a shape nobody authored.
# `contract` is gone from this table, and that is the point: section 7.3 measured it as
# **one name doing four jobs** across 23 concern modules, and a shared template is
# how four jobs come to look like one. Each successor names the shape its pages
# actually have, and the file is generated from that class's `required_sections`
# rather than hand-written — a template whose headings disagree with the contract
# its pages are graded against is a trap laid for the author.
PAGE_CLASS_TEMPLATE: dict[str, str] = {
    name: f"{SHARED_DIR}/assets/output-template-{name.replace('_', '-')}.md"
    for name in (
        "api_contract",
        "artifact",
        "data_entity",
        "decision",
        "diagram",
        "event_message",
        "mechanism",
        "overview",
        "requirement",
        "test_strategy",
        "viewpoint",
    )
}

# Prefixes the shared validator's stable-ID regex accepts (MOD-4 added the last
# four). A module may not invent one outside this set.
ALLOWED_ID_PREFIXES: frozenset[str] = frozenset(
    # specification added `CRYPTO` and `THREAT`. The alternative was to reuse `SEC`, which
    # `secrets` already holds — and `_validate` refuses that, correctly: two concerns
    # sharing a prefix share an ID namespace, so `SEC-004` would name a key rotation
    # rule on one page and a threat on another. The refusal is the reason these two
    # names exist rather than a convenience.
    # specification's five new archetypes add five more, for the same reason: a concern
    # whose ids share a namespace with a sibling has not been separated.
    {"REQ", "ADR", "API", "MSG", "ENTITY", "FIT", "PROMPT", "SEC", "OBS", "RES", "DEP",
     "CRYPTO", "THREAT", "MEMORY", "EVAL", "CAP", "STREAM", "STAGE"}
)


@dataclass(frozen=True)
class OutputModule:
    """One concern module of one skill's output tree.

    The field list is section 4's YAML declaration verbatim, so the same object serves
    both landing sites named in decision 3: this generator's `output-contract.md`
    section (MOD-2) and `workspace-template.yml`'s `output_modules:` (MOD-3).
    """

    id: str
    path: str
    page_class: str
    id_prefix: str
    when: str
    consumers: tuple[str, ...]
    cadence: str
    approver: str
    checklist: str
    obligation: str = "required_seam"
    downgrade_reason: str = ""
    fitness_rule: str = ""

    @property
    def template(self) -> str:
        return PAGE_CLASS_TEMPLATE[self.page_class]

    def as_dict(self) -> dict[str, object]:
        """section 4's YAML shape, field order included."""
        d: dict[str, object] = {
            "id": self.id,
            "path": self.path,
            "page_class": self.page_class,
            "template": self.template,
            "id_prefix": self.id_prefix,
            "obligation": self.obligation,
            "when": self.when,
            "consumers": list(self.consumers),
            "cadence": self.cadence,
            "approver": self.approver,
            "checklist": self.checklist,
        }
        if self.downgrade_reason:
            d["downgrade_reason"] = self.downgrade_reason
        return d

    def as_contract_dict(self) -> dict[str, object]:
        """Shape for contracts/archetype-vocabulary.yml."""
        d = self.as_dict()
        d["fitness_rule"] = self.fitness_rule or "none: informational artifact"
        return d


def _m(
    module_id: str,
    path: str,
    page_class: str,
    id_prefix: str,
    when: str,
    consumers: tuple[str, ...],
    cadence: str,
    approver: str,
    checklist: str,
    obligation: str = "required_seam",
    downgrade_reason: str = "",
    fitness_rule: str = "",
) -> OutputModule:
    if obligation != "required_seam" and obligation != "mandatory" and not downgrade_reason:
        raise ValueError(
            f"OutputModule {module_id!r} has downgraded obligation {obligation!r} without a downgrade_reason"
        )
    return OutputModule(
        module_id, path, page_class, id_prefix, when, consumers, cadence, approver, checklist, obligation, downgrade_reason, fitness_rule
    )


# The ten archetypes of section 4. `{module}` is the business module the concern belongs
# to (rule R4); the numeric folder prefix is the sort key the site and the
# scaffolder both read, which is why it is part of the path rather than a
# separate field.
ARCHETYPE_MODULES: dict[str, tuple[OutputModule, ...]] = {
    "backend-service": (
        _m("api", "01-{module}/11-api/{module}-api.md", "api_contract", "API",
           "evidence.has('inbound_port')",
           ("caller-teams",), "caller-driven", "api-architect",
           "every operation names its errors, idempotency rule and compatibility rule"),
        _m("events", "01-{module}/12-events/{module}-events.md", "event_message", "MSG",
           "evidence.has('published_event') or evidence.has('consumed_event')",
           ("subscriber-teams", "data-governance"), "domain-fact-driven", "event-driven-architect",
           "every event names its schema, ordering scope and deduplication key"),
        _m("clients", "01-{module}/13-clients/{module}-clients.md", "api_contract", "DEP",
           "evidence.has('outbound_call')",
           ("dependency-owners", "operators"), "dependency-driven", "integration-adapter-architect",
           "every outbound call names its timeout, retry budget and fallback"),
        _m("data", "01-{module}/14-data/{module}-data.md", "artifact", "ENTITY",
           "evidence.has('owned_state')",
           ("data-governance", "reporting-consumers"), "schema-driven", "database-architect",
           "every entity names its owner, grain, lifecycle and retention"),
        _m("security", "01-{module}/20-security/{module}-security.md", "mechanism", "SEC",
           "evidence.has('trust_boundary')",
           ("security-review",), "threat-driven", "security-architect",
           "every trust boundary names its authentication, authorization and audit rule"),
        _m("observability", "01-{module}/21-observability/{module}-observability.md", "mechanism", "OBS",
           "evidence.has('runtime_signal')",
           ("operators", "sre"), "incident-driven", "observability-architect",
           "every signal names its emitter, cardinality bound and the question it answers"),
        _m("resilience", "01-{module}/22-resilience/{module}-resilience.md", "mechanism", "RES",
           "evidence.has('external_dependency')",
           ("operators",), "dependency-behaviour-driven", "reliability-architect",
           "every dependency names its timeout, retry policy and degraded mode"),
    ),
    "frontend": (
        _m("ui-surface", "01-{module}/11-ui-surface/{module}-ui-surface.md", "api_contract", "API",
           "evidence.has('user_facing_view')",
           ("product-owners", "design-system-owners"), "user-journey-driven", "frontend-architect",
           "every view names its entry route, required data and empty/error state"),
        _m("state", "01-{module}/12-state/{module}-state.md", "artifact", "ENTITY",
           "evidence.has('client_state')",
           ("frontend-maintainers",), "interaction-driven", "frontend-architect",
           "every state atom names its owner, lifetime and invalidation trigger"),
        _m("api-consumption", "01-{module}/13-api-consumption/{module}-api-consumption.md", "api_contract", "DEP",
           "evidence.has('backend_call')",
           ("backend-teams",), "provider-driven", "api-architect",
           "every call names its provider contract, failure rendering and retry rule"),
        _m("accessibility", "01-{module}/20-accessibility/{module}-accessibility.md", "mechanism", "SEC",
           "evidence.has('interactive_control')",
           ("accessibility-review", "compliance"), "standard-driven", "accessibility-reviewer",
           "every interactive control names its role, keyboard path and conformance criterion"),
        _m("performance", "01-{module}/21-performance/{module}-performance.md", "mechanism", "OBS",
           "evidence.has('render_budget')",
           ("operators", "product-owners"), "budget-driven", "performance-architect",
           "every budget names its metric, threshold and the measurement that proves it"),
    ),
    "integration-adapter": (
        _m("provider-contract", "01-{module}/11-provider-contract/{module}-provider-contract.md", "api_contract", "DEP",
           "evidence.has('external_provider')",
           ("caller-teams", "provider-owners"), "provider-driven", "integration-adapter-architect",
           "every provider operation names its version, quota and breaking-change route"),
        _m("translation", "01-{module}/12-translation/{module}-translation.md", "artifact", "ENTITY",
           "evidence.has('field_mapping')",
           ("domain-owners",), "schema-driven", "domain-model-architect",
           "every mapped field names its source, target, unit and lossy case"),
        _m("failure-mapping", "01-{module}/13-failure-mapping/{module}-failure-mapping.md", "mechanism", "RES",
           "evidence.has('provider_error')",
           ("caller-teams", "operators"), "provider-behaviour-driven", "reliability-architect",
           "every provider error maps to one local error, one retry verdict and one operator action"),
        _m("credentials", "01-{module}/20-credentials/{module}-credentials.md", "mechanism", "SEC",
           "evidence.has('provider_credential')",
           ("security-review",), "rotation-driven", "secret-management-architect",
           "every credential names its store, scope, rotation period and revocation path"),
        _m("idempotency", "01-{module}/21-idempotency/{module}-idempotency.md", "mechanism", "MSG",
           "evidence.has('non_idempotent_call')",
           ("caller-teams", "operators"), "replay-driven", "event-driven-architect",
           "every replayable call names its idempotency key, window and duplicate outcome"),
    ),
    "data-platform": (
        _m("ingest", "01-{module}/11-ingest/{module}-ingest.md", "event_message", "MSG",
           "evidence.has('source_feed')",
           ("platform-operators", "source-owners"), "source-driven", "data-pipeline-architect",
           "every feed names its source of record, arrival contract and late-data rule"),
        _m("storage", "01-{module}/12-storage/{module}-storage.md", "artifact", "ENTITY",
           "evidence.has('persisted_dataset')",
           ("data-governance",), "schema-driven", "database-architect",
           "every dataset names its grain, partitioning and schema-evolution rule"),
        _m("serving", "01-{module}/13-serving/{module}-serving.md", "api_contract", "API",
           "evidence.has('query_consumer')",
           ("analytics-consumers", "application-teams"), "consumer-driven", "api-architect",
           "every served surface names its freshness guarantee, shape and access path"),
        _m("lineage", "01-{module}/14-lineage/{module}-lineage.md", "artifact", "DEP",
           "evidence.has('derived_dataset')",
           ("auditors", "data-governance"), "topology-driven", "metadata-architect",
           "every derived dataset names its upstreams, transform and rebuild command"),
        _m("retention", "01-{module}/20-retention/{module}-retention.md", "mechanism", "SEC",
           "evidence.has('regulated_field')",
           ("compliance", "privacy-review"), "regulation-driven", "privacy-architect",
           "every retained field names its legal basis, retention period and deletion proof"),
        _m("quality", "01-{module}/21-quality/{module}-quality.md", "mechanism", "OBS",
           "evidence.has('quality_expectation')",
           ("data-consumers", "platform-operators"), "incident-driven", "data-governance-architect",
           "every expectation names its assertion, threshold and the action on breach"),
    ),
    "library-sdk": (
        _m("public-api", "01-{module}/11-public-api/{module}-public-api.md", "api_contract", "API",
           "evidence.has('exported_symbol')",
           ("integrating-teams",), "consumer-driven", "library-sdk-architect",
           "every exported symbol names its stability tier, errors and threading contract"),
        _m("extension-points", "01-{module}/12-extension-points/{module}-extension-points.md", "api_contract", "DEP",
           "evidence.has('extension_point')",
           ("extension-authors",), "capability-driven", "plugin-extension-architect",
           "every extension point names the contract the caller must satisfy and what it may not assume"),
        _m("packaging", "01-{module}/13-packaging/{module}-packaging.md", "artifact", "ENTITY",
           "evidence.has('distribution_artifact')",
           ("integrating-teams", "release-engineering"), "release-driven", "release-architect",
           "every artifact names its coordinates, dependency closure and signature"),
        _m("versioning", "01-{module}/20-versioning/{module}-versioning.md", "decision", "ADR",
           "evidence.has('release_channel')",
           ("integrating-teams", "release-engineering"), "policy-driven", "library-sdk-architect",
           "the scheme names what a major, minor and patch bump mean and who may declare one"),
        _m("compatibility", "01-{module}/21-compatibility/{module}-compatibility.md", "mechanism", "RES",
           "evidence.has('supported_version_range')",
           ("integrating-teams",), "deprecation-driven", "modernization-architect",
           "every supported range names its test matrix, deprecation window and migration path"),
    ),
    "plugin-extension": (
        _m("host-contract", "01-{module}/11-host-contract/{module}-host-contract.md", "api_contract", "API",
           "evidence.has('host_capability')",
           ("plugin-authors",), "capability-driven", "plugin-extension-architect",
           "every host capability names its arguments, errors and permission requirement"),
        _m("lifecycle", "01-{module}/12-lifecycle/{module}-lifecycle.md", "mechanism", "MSG",
           "evidence.has('lifecycle_hook')",
           ("host-operators", "plugin-authors"), "runtime-driven", "plugin-extension-architect",
           "every hook names its ordering, re-entrancy rule and behaviour on failure"),
        _m("sandboxing", "01-{module}/20-sandboxing/{module}-sandboxing.md", "mechanism", "SEC",
           "evidence.has('untrusted_code')",
           ("host-operators", "security-review"), "threat-driven", "application-security-architect",
           "every capability the sandbox grants names its limit and the escape it prevents"),
        _m("distribution", "01-{module}/21-distribution/{module}-distribution.md", "artifact", "DEP",
           "evidence.has('plugin_registry')",
           ("plugin-authors", "release-engineering"), "release-driven", "release-architect",
           "every published plugin names its compatibility range, signature and revocation route"),
    ),
    "observability": (
        _m("signals", "01-{module}/11-signals/{module}-signals.md", "event_message", "OBS",
           "evidence.has('emitted_signal')",
           ("operators", "sre"), "instrumentation-driven", "observability-architect",
           "every signal names its type, labels, cardinality bound and retention"),
        _m("slo", "01-{module}/12-slo/{module}-slo.md", "requirement", "RES",
           "evidence.has('user_journey')",
           ("product-owners", "service-owners"), "objective-driven", "reliability-architect",
           "every objective names its SLI query, target, window and error-budget policy"),
        _m("alerting", "01-{module}/20-alerting/{module}-alerting.md", "mechanism", "MSG",
           "evidence.has('actionable_condition')",
           ("on-call",), "incident-driven", "sre-architect",
           "every alert names its condition, the action it demands and its runbook"),
        _m("retention", "01-{module}/21-retention/{module}-retention.md", "mechanism", "SEC",
           "evidence.has('stored_telemetry')",
           ("compliance", "cost-owners"), "regulation-and-cost-driven", "data-governance-architect",
           "every telemetry class names its retention period, cost basis and redaction rule"),
    ),
    "domain-capability": (
        _m("aggregates", "01-{module}/11-aggregates/{module}-aggregates.md", "artifact", "ENTITY",
           "evidence.has('consistency_boundary')",
           ("domain-owners", "implementing-teams"), "model-driven", "domain-model-architect",
           "every aggregate names its root, boundary and the transaction it must complete alone"),
        _m("domain-events", "01-{module}/12-domain-events/{module}-domain-events.md", "event_message", "MSG",
           "evidence.has('domain_fact')",
           ("data-governance", "subscriber-contexts"), "domain-fact-driven", "domain-event-architect",
           "every event names the fact it records, its payload and its ordering scope"),
        _m("invariants", "01-{module}/13-invariants/{module}-invariants.md", "mechanism", "REQ",
           "evidence.has('business_rule')",
           ("domain-owners", "quality-engineering"), "rule-driven", "ddd-architect",
           "every invariant is stated so it can be falsified, with the failure it prevents"),
        _m("policies", "01-{module}/20-policies/{module}-policies.md", "decision", "ADR",
           "evidence.has('reactive_rule')",
           ("compliance", "domain-owners"), "policy-driven", "rule-engine-architect",
           "every policy names its trigger, decision, owner and the review that can revoke it"),
    ),
    "infra-platform": (
        _m("topology", "01-{module}/11-topology/{module}-topology.md", "diagram", "DEP",
           "evidence.has('deployable_unit')",
           ("platform-operators", "service-owners"), "environment-driven", "infra-platform-architect",
           "every node names what runs on it, what it depends on and its failure domain"),
        _m("provisioning", "01-{module}/12-provisioning/{module}-provisioning.md", "mechanism", "ENTITY",
           "evidence.has('managed_resource')",
           ("platform-operators",), "change-driven", "iac-architect",
           "every resource names its declaration source, drift check and destroy consequence"),
        _m("networking", "01-{module}/13-networking/{module}-networking.md", "mechanism", "API",
           "evidence.has('network_path')",
           ("network-security-review", "service-owners"), "reachability-driven", "network-architect",
           "every path names its ingress, egress, protocol and the rule that denies the rest"),
        _m("secrets", "01-{module}/20-secrets/{module}-secrets.md", "mechanism", "SEC",
           "evidence.has('credential_or_key')",
           ("security-review",), "rotation-driven", "secret-management-architect",
           "every secret names its store, consumer, rotation period and blast radius"),
        _m("cost", "01-{module}/21-cost/{module}-cost.md", "artifact", "OBS",
           "evidence.has('billable_resource')",
           ("cost-owners", "finance"), "budget-driven", "cost-optimization-architect",
           "every billable resource names its driver, unit cost and the signal that flags overrun"),
    ),
    "appendix": (
        _m("glossary", "01-{module}/11-glossary/{module}-glossary.md", "artifact", "ENTITY",
           "evidence.has('ambiguous_term')",
           ("all-readers",), "language-driven", "documentation-architect",
           "every term names one definition, its owning context and the terms it is not"),
        _m("alternatives", "01-{module}/12-alternatives/{module}-alternatives.md", "decision", "ADR",
           "evidence.has('rejected_option')",
           ("future-maintainers", "reviewers"), "decision-driven", "architecture-decision-architect",
           "every rejected option names why it lost and the evidence that would reverse it"),
        _m("deprecations", "01-{module}/20-deprecations/{module}-deprecations.md", "mechanism", "RES",
           "evidence.has('superseded_element')",
           ("consumers-of-the-superseded-element",), "removal-driven", "modernization-architect",
           "every deprecation names its replacement, removal date and migration command"),
    ),
    "identity-access": (
        _m("authn", "01-{module}/11-authn/{module}-authn.md", "mechanism", "API",
           "evidence.has('authentication_rule') or evidence.has('identity_provider')",
           ("caller-teams", "security-review"), "authn-driven", "identity-access-architect",
           "every authentication flow names its identity provider, token format, lifetime and revocation path"),
        _m("authz", "01-{module}/12-authz/{module}-authz.md", "mechanism", "REQ",
           "evidence.has('authorization_policy') or evidence.has('access_control') or evidence.has('tenancy_boundary')",
           ("security-review", "auditors"), "policy-driven", "identity-access-architect",
           "every permission names its subject, resource, action, context and evaluation point"),
        _m("session", "01-{module}/13-session/{module}-session.md", "mechanism", "ENTITY",
           "evidence.has('session_management') or evidence.has('token_lifecycle')",
           ("frontend-teams", "security-review"), "session-driven", "identity-access-architect",
           "every session state names its store, idle timeout, max lifetime and binding mechanism"),
        _m("secrets", "01-{module}/20-secrets/{module}-secrets.md", "mechanism", "SEC",
           "evidence.has('credential_or_key')",
           ("security-review", "platform-operators"), "rotation-driven", "secret-management-architect",
           "every signing key or secret names its store, rotation schedule and emergency revocation protocol"),
        _m("audit", "01-{module}/21-audit/{module}-audit.md", "mechanism", "OBS",
           "evidence.has('audit_trail') or evidence.has('security_log')",
           ("compliance", "auditors", "security-review"), "compliance-driven", "compliance-architect",
           "every access event names its actor, target, timestamp, decision and tamper-evident log target"),
        # specification (plan section 5). These two exist because a measurement refused the design
        # above them. The plan proposed a whole new `security-control` archetype on
        # the premise that the security cluster ran on `infra-platform` and so had
        # nowhere to put RBAC or a threat model. Measured: 10 of its 11 skills already
        # run on `identity-access`, and the five concerns above already house 8 of the
        # 12 artifacts `10_security_design` produces — oauth2/oidc/jwt/mtls under
        # `authn`, rbac/abac under `authz`, secrets-management under `secrets`,
        # audit-logging under `audit`.
        #
        # The four with no home were `pki-architecture-spec` and the three from
        # `threat-modeling-task`. Four artifacts across two subjects is two concerns,
        # not a thirteenth archetype — and adding them here costs no skill an
        # archetype change, where `security-control` would have moved ten.
        _m("crypto", "01-{module}/14-crypto/{module}-crypto.md", "mechanism", "CRYPTO",
           "evidence.has('credential_or_key') or evidence.has('trust_boundary')",
           ("security-review", "platform-operators"), "trust-chain-driven", "security-architect",
           "every trust chain names its root, issuance path, algorithm, expiry and revocation check"),
        _m("threat-model", "01-{module}/22-threat-model/{module}-threat-model.md", "mechanism", "THREAT",
           "evidence.has('trust_boundary')",
           ("security-review", "auditors"), "threat-driven", "security-architect",
           "every threat names the boundary it crosses, its STRIDE category, and the control that answers it"),
    ),
    "storage": (
        _m("storage-class", "01-{module}/11-storage-class/{module}-storage-class.md", "data_entity", "ENTITY",
           "evidence.has('storage_tier')",
           ("platform-operators", "cost-owners"), "tier-driven", "storage-architect",
           "every storage class names its durability target, availability SLA and IOPS budget"),
        _m("presigned-access", "01-{module}/12-presigned-access/{module}-presigned-access.md", "mechanism", "API",
           "evidence.has('presigned_url') or evidence.has('access_delegation')",
           ("application-teams", "security-review"), "delegation-driven", "storage-architect",
           "every delegated access path names its token scope, expiration window and signature algorithm"),
        _m("quota", "01-{module}/13-quota/{module}-quota.md", "mechanism", "OBS",
           "evidence.has('storage_quota')",
           ("cost-owners", "operators"), "capacity-driven", "capacity-planning-architect",
           "every quota names its soft limit, hard limit, enforcement point and alert threshold"),
        _m("lifecycle", "01-{module}/20-lifecycle/{module}-lifecycle.md", "mechanism", "RES",
           "evidence.has('lifecycle_policy')",
           ("storage-operators", "cost-owners"), "policy-driven", "storage-architect",
           "every lifecycle policy names its transition triggers, tier progression and purge rule"),
        _m("retention", "01-{module}/21-retention/{module}-retention.md", "mechanism", "SEC",
           "evidence.has('retention_policy')",
           ("compliance", "legal-review"), "regulation-driven", "privacy-architect",
           "every retained object class names its immutability period, legal hold rule and destruction proof"),
    ),
    # ---------------------------------------------------------------------- #
    # specification (plan section 5). Five archetypes, each because a cluster's artifacts had
    # nowhere to land in the archetype its skills were borrowing.
    #
    # The `when:` clauses were written before the vocabulary had an AI family and
    # used the nearest tokens that existed. specification accepted specification's eleven, and each
    # `ai` token now leads the slot it names. The old approximation stays as an
    # added `or`: dropping it would remove pages from workspaces that already
    # have them, and that is a regeneration someone must own, not a side effect.
    # ---------------------------------------------------------------------- #
    "ai-system": (
        _m("model-invocation", "01-{module}/11-model-invocation/{module}-model-invocation.md", "api_contract", "DEP",
           "evidence.has('model_invocation') or evidence.has('outbound_call') or evidence.has('external_provider')",
           ("application-teams", "cost-owners"), "provider-driven", "ai-system-architect",
           "every model call names its provider, version pin, timeout, retry budget and fallback model"),
        _m("prompt-assets", "01-{module}/12-prompt-assets/{module}-prompt-assets.md", "artifact", "PROMPT",
           "evidence.has('prompt_asset') or evidence.has('external_provider') or evidence.has('derived_dataset')",
           ("application-teams", "evaluation-owners"), "prompt-revision-driven", "prompt-architect",
           "every prompt names its template id, variables, version and the eval that guards a change to it"),
        _m("retrieval", "01-{module}/13-retrieval/{module}-retrieval.md", "mechanism", "ENTITY",
           "evidence.has('retrieval_corpus') or evidence.has('embedding_space') or evidence.has('derived_dataset') or evidence.has('query_consumer')",
           ("application-teams", "data-governance"), "corpus-driven", "rag-architect",
           "every corpus names its chunking rule, embedding model, index refresh cadence and staleness bound"),
        _m("memory", "01-{module}/14-memory/{module}-memory.md", "mechanism", "MEMORY",
           "evidence.has('owned_state') or evidence.has('retention_policy')",
           ("application-teams", "privacy-review"), "session-driven", "memory-architect",
           "every retained turn names its scope, eviction rule, retention window and redaction boundary"),
        _m("guardrails", "01-{module}/20-guardrails/{module}-guardrails.md", "mechanism", "SEC",
           "evidence.has('agent_autonomy') or evidence.has('tool_surface') or evidence.has('untrusted_code') or evidence.has('access_control')",
           ("security-review", "application-teams"), "threat-driven", "ai-system-architect",
           "every guardrail names what it refuses, how it decides, and what the caller sees on a refusal"),
        _m("evaluation", "01-{module}/21-evaluation/{module}-evaluation.md", "mechanism", "EVAL",
           "evidence.has('eval_criterion') or evidence.has('quality_expectation')",
           ("evaluation-owners", "application-teams"), "release-driven", "evaluation-architect",
           "every eval names its dataset, metric, passing threshold and what a regression blocks"),
        _m("token-budget", "01-{module}/22-token-budget/{module}-token-budget.md", "mechanism", "FIT",
           "evidence.has('token_budget') or evidence.has('billable_resource') or evidence.has('render_budget')",
           ("cost-owners", "operators"), "cost-driven", "cost-optimization-architect",
           "every budget names its unit, ceiling per request, measurement point and the action on breach"),
    ),
    "business-capability": (
        _m("capabilities", "01-{module}/11-capabilities/{module}-capabilities.md", "overview", "CAP",
           "evidence.has('business_rule') or evidence.has('domain_fact')",
           ("business-owners", "architecture-review"), "strategy-driven", "business-capability-architect",
           "every capability names what the business can do, who owns it, and the system that realises it"),
        _m("value-streams", "01-{module}/12-value-streams/{module}-value-streams.md", "mechanism", "STREAM",
           "evidence.has('user_journey') or evidence.has('feature_cluster')",
           ("business-owners", "product"), "journey-driven", "business-capability-architect",
           "every stream names its trigger, the handoffs in order, and where value waits"),
        _m("org-topology", "01-{module}/13-org-topology/{module}-org-topology.md", "artifact", "DEP",
           "evidence.has('external_dependency')",
           ("business-owners", "engineering-leads"), "reorg-driven", "business-capability-architect",
           "every team names what it owns, who it depends on, and the interaction mode between them"),
    ),
    "quality-assurance": (
        _m("test-levels", "01-{module}/11-test-levels/{module}-test-levels.md", "mechanism", "FIT",
           "evidence.has('quality_expectation')",
           ("engineering-teams", "release-managers"), "risk-driven", "testing-architect",
           "every level names the risk it covers, its environment, and what a failure at that level blocks"),
        _m("performance", "01-{module}/12-performance/{module}-performance.md", "mechanism", "OBS",
           "evidence.has('render_budget') or evidence.has('emitted_signal') or evidence.has('capacity_limit')",
           ("operators", "sre"), "budget-driven", "performance-architect",
           "every budget names its percentile, measurement point, ceiling and the alert on breach"),
        _m("resilience-drills", "01-{module}/13-resilience-drills/{module}-resilience-drills.md", "mechanism", "RES",
           "evidence.has('provider_error') or evidence.has('external_dependency')",
           ("sre", "operators"), "incident-driven", "resilience-architect",
           "every drill names the failure it injects, the blast radius, the expected degradation and the abort rule"),
        _m("quality-gates", "01-{module}/20-quality-gates/{module}-quality-gates.md", "test_strategy", "REQ",
           "evidence.has('quality_expectation')",
           ("release-managers", "engineering-teams"), "release-driven", "testing-architect",
           "every gate names its command, its passing exit code, and what it refuses to let through"),
    ),
    "delivery-pipeline": (
        _m("pipeline", "01-{module}/11-pipeline/{module}-pipeline.md", "mechanism", "STAGE",
           "evidence.has('distribution_artifact') or evidence.has('release_surface')",
           ("engineering-teams", "release-managers"), "commit-driven", "deployment-architect",
           "every stage names its input artifact, its gate, its output, and who may re-run it"),
        _m("environments", "01-{module}/12-environments/{module}-environments.md", "artifact", "ENTITY",
           "evidence.has('deployable_unit') or evidence.has('managed_resource')",
           ("operators", "engineering-teams"), "topology-driven", "deployment-architect",
           "every environment names its purpose, its data class, who may deploy, and how it differs from production"),
        _m("release-strategy", "01-{module}/13-release-strategy/{module}-release-strategy.md", "decision", "ADR",
           "evidence.has('release_channel') or evidence.has('release_surface')",
           ("release-managers", "product"), "release-driven", "release-architect",
           "the chosen strategy names its exposure ramp, its health signal, and the option it was chosen over"),
        _m("rollback", "01-{module}/20-rollback/{module}-rollback.md", "mechanism", "RES",
           "evidence.has('release_surface') or evidence.has('provider_error') or evidence.has('cutover_step')",
           ("operators", "release-managers"), "incident-driven", "release-architect",
           "every rollback names its trigger condition, its time bound, and what it cannot undo"),
    ),
    "documentation-surface": (
        _m("audience", "01-{module}/11-audience/{module}-audience.md", "viewpoint", "REQ",
           "evidence.has('ambiguous_term') or evidence.has('user_journey')",
           ("documentation-owners", "engineering-teams"), "reader-driven", "documentation-architect",
           "every audience names what it already knows, what it needs to do, and the page that serves it"),
        _m("information-architecture", "01-{module}/12-information-architecture/{module}-information-architecture.md", "artifact", "ENTITY",
           "evidence.has('ambiguous_term')",
           ("documentation-owners",), "structure-driven", "documentation-architect",
           "every section names its owner, its page class, and the question a reader arrives with"),
        _m("freshness", "01-{module}/20-freshness/{module}-freshness.md", "mechanism", "OBS",
           "evidence.has('superseded_element') or evidence.has('stored_telemetry')",
           ("documentation-owners", "engineering-teams"), "drift-driven", "documentation-architect",
           "every page names its source, the check that proves it still matches, and what stale means here"),
        # Carried over from `appendix`, which `documentation-surface` supersedes for
        # all eight of its skills. Dropping it would have orphaned the
        # `rejected_option` token — `test_evidence_vocabulary` catches exactly that,
        # and an unreachable token is a detector nobody will ever see fire.
        _m("alternatives", "01-{module}/21-alternatives/{module}-alternatives.md", "decision", "ADR",
           "evidence.has('rejected_option')",
           ("documentation-owners", "architecture-review"), "decision-driven", "architecture-decision-architect",
           "every rejected option names why it lost and the evidence under which it would win"),
    ),
}


# ---------------------------------------------------------------------------
# MOD-6 -- renamed concern-module folders
# ---------------------------------------------------------------------------
# section 3.1 split `11-communication/` -- one folder holding the inbound surface, the
# asynchronous surface and the outbound calls -- into `11-api/`, `12-events/` and
# `13-clients/`. Per the alias rule (`specification` section 10.3) a
# rename produces an alias, never a new identity, so every path and deep link
# already written against the old name keeps resolving.
#
# Which sibling inherits the name is not arbitrary: the old folder *was* the API
# slot (section 9 grounding: `11-communication/` <- `08_api_design`), so the synchronous
# inbound surface is its continuation and the other two are new modules.
#
# Aliases are append-only and never garbage-collected (section 10.3 rule 3). Deleting a
# row here is not a cleanup; it is breaking every link the row keeps alive. That
# is why the shape is asserted at import instead of trusted to a future editor,
# and why `since`/`reason` are required fields rather than a comment.


@dataclass(frozen=True)
class ModuleFolderAlias:
    """One recorded rename of a concern-module folder (section 10.3's alias record)."""

    was: str
    now: str
    since: str
    reason: str

    def as_dict(self) -> dict[str, str]:
        return {"was": self.was, "now": self.now, "since": self.since, "reason": self.reason}


MODULE_FOLDER_ALIASES: tuple[ModuleFolderAlias, ...] = (
    ModuleFolderAlias(
        was="11-communication",
        now="11-api",
        since="2026-08-08",
        reason=(
            "Split the conflated communication folder "
            "into 11-api / 12-events / 13-clients; the synchronous inbound surface kept the slot"
        ),
    ),
)


def declared_module_folders() -> frozenset[str]:
    """Every concern-module folder some archetype declares -- the live names."""
    return frozenset(
        module.path.split("/")[-2] for modules in ARCHETYPE_MODULES.values() for module in modules
    )


def resolve_module_folder(folder: str) -> str:
    """The folder a written path *means today*, following the alias chain.

    Resolution is **total and idempotent**: a live folder resolves to itself and
    `resolve(resolve(x)) == resolve(x)`, so a caller may run any path segment
    through it without first asking whether it is an alias. An unknown segment
    comes back unchanged -- this function answers "was this renamed", not "is this
    a concern module"; the caller's own table answers the second question.

    The chain is followed rather than looked up once because aliases are
    append-only: a folder renamed twice leaves two rows, and the first row must
    still land on the folder that exists now, not on the intermediate name.
    """
    aliases = {alias.was: alias.now for alias in MODULE_FOLDER_ALIASES}
    seen: set[str] = set()
    current = folder
    while current in aliases and current not in seen:
        seen.add(current)
        current = aliases[current]
    return current


def module_folder_alias_map() -> dict[str, str]:
    """`was -> live folder` for every alias, sorted, as the rendering input.

    Each `was` is resolved through the whole chain, so a consumer that cannot
    import this module (the validator shipped inside the catalog) gets a flat
    one-hop table and never has to know that chains exist.
    """
    return {alias.was: resolve_module_folder(alias.was) for alias in sorted(MODULE_FOLDER_ALIASES, key=lambda a: a.was)}


# Every cluster states one default, so no skill can fall through to nothing. The
# default is a *stated fallback*, not a claim that the archetype fits the skill
# well -- which is why `resolve_output_modules` marks it and the generated
# contract prints it. Clusters 07/08/09 have no eponymous archetype in section 4 and
# take the nearest vocabulary; those are the rows most worth reviewing.
CLUSTER_DEFAULT_ARCHETYPE: dict[str, str] = {
    "01_business_architecture": "business-capability",
    "02_domain_architecture": "domain-capability",
    "03_application_architecture": "backend-service",
    "04_ai_architecture": "ai-system",
    "05_data_architecture": "data-platform",
    "06_infrastructure_architecture": "infra-platform",
    "07_security_architecture": "infra-platform",  # fallback for zero-trust-architect; 10/11 security skills map explicitly to identity-access in SKILL_ARCHETYPE and CORE_ARCHETYPE_CLUSTERS
    "08_quality_attribute_architecture": "quality-assurance",
    "09_delivery_architecture": "delivery-pipeline",
    "10_documentation_architecture": "documentation-surface",
}

# Explicit fitness notes for skills that deliberately resolve via CLUSTER_DEFAULT_ARCHETYPE.
# R4.3: Every note must cite at least one concern module id (aggregates, domain-events, invariants, policies)
# that the domain-capability default archetype genuinely provides.
CLUSTER_DEFAULT_FITNESS_NOTES: dict[tuple[str, str], str] = {
    ("01_business_architecture", "business-architect"): "Provides capabilities and value-streams: what the business can do and where value waits, from the business-capability archetype.",
    ("01_business_architecture", "business-process-architect"): "Provides value-streams and capabilities: the ordered handoffs a process runs through, from the business-capability archetype.",
    ("01_business_architecture", "enterprise-architect"): "Provides capabilities and org-topology: capability ownership across teams, from the business-capability archetype.",
    ("01_business_architecture", "industry-architecture"): "Provides capabilities and value-streams: the industry-standard capability set and its streams, from the business-capability archetype.",
    ("01_business_architecture", "organization-architect"): "Provides capabilities, value-streams and org-topology: the business capability set, its streams and who owns them, from the business-capability archetype.",
    ("01_business_architecture", "product-architect"): "Provides capabilities, value-streams and org-topology: the business capability set, its streams and who owns them, from the business-capability archetype.",
    ("01_business_architecture", "reference-architecture"): "Provides capabilities, value-streams and org-topology: the business capability set, its streams and who owns them, from the business-capability archetype.",
    ("01_business_architecture", "solution-architect"): "Provides capabilities, value-streams and org-topology: the business capability set, its streams and who owns them, from the business-capability archetype.",
    ("01_business_architecture", "value-stream-architect"): "Provides capabilities, value-streams and org-topology: the business capability set, its streams and who owns them, from the business-capability archetype.",
}

# Skills declared against a named archetype: either the eponymous skill of section 4's
# table, or a skill whose output genuinely has that archetype's module set.
# Everything absent here resolves through CLUSTER_DEFAULT_ARCHETYPE and says so.
SKILL_ARCHETYPE: dict[tuple[str, str], str] = {
    # 01_business_architecture
    ("01_business_architecture", "business-capability-architect"): "business-capability",

    # 02_domain_architecture
    ("02_domain_architecture", "aggregate-architect"): "domain-capability",
    ("02_domain_architecture", "bounded-context-architect"): "domain-capability",
    ("02_domain_architecture", "context-mapping-architect"): "integration-adapter",
    ("02_domain_architecture", "ddd-architect"): "domain-capability",
    ("02_domain_architecture", "domain-capability-architect"): "domain-capability",
    ("02_domain_architecture", "domain-event-architect"): "domain-capability",
    ("02_domain_architecture", "domain-model-architect"): "domain-capability",
    ("02_domain_architecture", "rule-engine-architect"): "domain-capability",
    ("02_domain_architecture", "workflow-architect"): "domain-capability",

    # 03_application_architecture
    ("03_application_architecture", "api-architect"): "backend-service",
    ("03_application_architecture", "backend-service-architect"): "backend-service",
    ("03_application_architecture", "bff-architect"): "frontend",
    ("03_application_architecture", "desktop-architect"): "frontend",
    ("03_application_architecture", "edge-architect"): "integration-adapter",
    ("03_application_architecture", "event-driven-architect"): "backend-service",
    ("03_application_architecture", "frontend-architect"): "frontend",
    # specification. These two were assigned in a way that INVERTED the routing signal.
    # `gateway-architect` held `integration-adapter` — provider-contract,
    # credentials, failure-mapping — which is the vocabulary of a thing that proxies
    # a third party. `ai-system-architect` held `backend-service` — api, events,
    # data — which is the vocabulary of a service that owns state. An "AI gateway
    # that proxies ChatGPT behind one interface, holds provider credentials and
    # fails over by model policy" therefore routed to `gateway-architect`, and a
    # WebSocket gateway that authenticates and forwards routed anywhere but there.
    #
    # Swapped, because that is what each skill actually is: an edge gateway owns an
    # inbound surface, security at the line and resilience toward what it fronts;
    # an AI system architect owns provider contracts, credentials and failover.
    ("03_application_architecture", "gateway-architect"): "backend-service",
    ("03_application_architecture", "integration-adapter-architect"): "integration-adapter",
    ("03_application_architecture", "library-sdk-architect"): "library-sdk",
    ("03_application_architecture", "microservice-architect"): "backend-service",
    ("03_application_architecture", "mobile-architect"): "frontend",
    ("03_application_architecture", "modular-monolith-architect"): "backend-service",
    ("03_application_architecture", "monolith-architect"): "backend-service",
    ("03_application_architecture", "plugin-extension-architect"): "plugin-extension",
    ("03_application_architecture", "workflow-orchestration-architect"): "backend-service",

    # 04_ai_architecture
    ("04_ai_architecture", "agent-architect"): "ai-system",
    ("04_ai_architecture", "ai-system-architect"): "ai-system",
    ("04_ai_architecture", "evaluation-architect"): "ai-system",
    ("04_ai_architecture", "mcp-architect"): "ai-system",
    ("04_ai_architecture", "memory-architect"): "ai-system",
    ("04_ai_architecture", "model-serving-architect"): "ai-system",
    ("04_ai_architecture", "prompt-architect"): "ai-system",
    ("04_ai_architecture", "rag-architect"): "ai-system",
    ("04_ai_architecture", "tool-calling-architect"): "ai-system",
    ("04_ai_architecture", "vector-search-architect"): "ai-system",

    # 05_data_architecture
    ("05_data_architecture", "cache-architect"): "data-platform",
    ("05_data_architecture", "cdc-architect"): "data-platform",
    ("05_data_architecture", "data-governance-architect"): "data-platform",
    ("05_data_architecture", "data-lake-architect"): "data-platform",
    ("05_data_architecture", "data-pipeline-architect"): "data-platform",
    ("05_data_architecture", "data-platform-architect"): "data-platform",
    ("05_data_architecture", "data-warehouse-architect"): "data-platform",
    ("05_data_architecture", "database-architect"): "data-platform",
    ("05_data_architecture", "etl-architect"): "data-platform",
    ("05_data_architecture", "lakehouse-architect"): "data-platform",
    ("05_data_architecture", "master-data-architect"): "data-platform",
    ("05_data_architecture", "metadata-architect"): "data-platform",
    ("05_data_architecture", "search-architect"): "data-platform",
    ("05_data_architecture", "streaming-architect"): "data-platform",
    ("05_data_architecture", "vector-database-architect"): "data-platform",

    # 06_infrastructure_architecture
    ("06_infrastructure_architecture", "cloud-architect"): "infra-platform",
    ("06_infrastructure_architecture", "container-architect"): "infra-platform",
    ("06_infrastructure_architecture", "devops-architect"): "infra-platform",
    ("06_infrastructure_architecture", "edge-infrastructure-architect"): "infra-platform",
    ("06_infrastructure_architecture", "gitops-architect"): "infra-platform",
    ("06_infrastructure_architecture", "iac-architect"): "infra-platform",
    ("06_infrastructure_architecture", "infra-platform-architect"): "infra-platform",
    ("06_infrastructure_architecture", "kubernetes-architect"): "infra-platform",
    ("06_infrastructure_architecture", "network-architect"): "infra-platform",
    ("06_infrastructure_architecture", "platform-engineering-architect"): "infra-platform",
    ("06_infrastructure_architecture", "runtime-architect"): "infra-platform",
    ("06_infrastructure_architecture", "serverless-architect"): "infra-platform",
    ("06_infrastructure_architecture", "service-mesh-architect"): "infra-platform",
    ("06_infrastructure_architecture", "storage-architect"): "storage",

    # 07_security_architecture
    ("07_security_architecture", "application-security-architect"): "identity-access",
    ("07_security_architecture", "cloud-security-architect"): "identity-access",
    ("07_security_architecture", "compliance-architect"): "identity-access",
    ("07_security_architecture", "identity-access-architect"): "identity-access",
    ("07_security_architecture", "key-management-architect"): "identity-access",
    ("07_security_architecture", "network-security-architect"): "infra-platform",
    ("07_security_architecture", "privacy-architect"): "identity-access",
    ("07_security_architecture", "secret-management-architect"): "identity-access",
    ("07_security_architecture", "security-architect"): "identity-access",
    ("07_security_architecture", "threat-modeling-architect"): "identity-access",
    ("07_security_architecture", "zero-trust-architect"): "identity-access",

    # 08_quality_attribute_architecture
    ("08_quality_attribute_architecture", "availability-architect"): "quality-assurance",
    ("08_quality_attribute_architecture", "capacity-planning-architect"): "quality-assurance",
    ("08_quality_attribute_architecture", "cost-optimization-architect"): "infra-platform",
    ("08_quality_attribute_architecture", "disaster-recovery-architect"): "quality-assurance",
    ("08_quality_attribute_architecture", "observability-architect"): "observability",
    ("08_quality_attribute_architecture", "performance-architect"): "quality-assurance",
    ("08_quality_attribute_architecture", "reliability-architect"): "quality-assurance",
    ("08_quality_attribute_architecture", "resilience-architect"): "quality-assurance",
    ("08_quality_attribute_architecture", "scalability-architect"): "quality-assurance",
    ("08_quality_attribute_architecture", "sustainability-architect"): "quality-assurance",

    # 09_delivery_architecture
    ("09_delivery_architecture", "deployment-architect"): "delivery-pipeline",
    ("09_delivery_architecture", "migration-architect"): "delivery-pipeline",
    ("09_delivery_architecture", "modernization-architect"): "delivery-pipeline",
    ("09_delivery_architecture", "operability-architect"): "delivery-pipeline",
    ("09_delivery_architecture", "release-architect"): "delivery-pipeline",
    ("09_delivery_architecture", "sre-architect"): "delivery-pipeline",
    ("09_delivery_architecture", "testing-architect"): "delivery-pipeline",

    # 10_documentation_architecture
    ("10_documentation_architecture", "appendix-architect"): "documentation-surface",
    ("10_documentation_architecture", "architecture-decision-architect"): "documentation-surface",
    ("10_documentation_architecture", "checklist-architect"): "documentation-surface",
    ("10_documentation_architecture", "diagram-architect"): "documentation-surface",
    ("10_documentation_architecture", "documentation-architect"): "documentation-surface",
    ("10_documentation_architecture", "review-architect"): "documentation-surface",
    ("10_documentation_architecture", "specification-architect"): "documentation-surface",
    ("10_documentation_architecture", "template-architect"): "documentation-surface",
}

ARCHETYPE_QUALITY_ATTRIBUTES: dict[str, tuple[str, ...]] = {
    "backend-service": ("latency", "availability", "data_integrity", "idempotency", "observability", "security"),
    "frontend": ("responsiveness", "accessibility", "state_consistency", "render_performance"),
    "integration-adapter": ("resilience", "fault_isolation", "credential_security", "idempotency"),
    "data-platform": ("freshness", "data_quality", "lineage_traceability", "retention_compliance"),
    "library-sdk": ("api_stability", "backward_compatibility", "package_integrity", "thread_safety"),
    "plugin-extension": ("isolation", "sandbox_security", "lifecycle_determinism", "re_entrancy"),
    "observability": ("signal_cardinality", "detection_latency", "query_performance", "sampling_fidelity"),
    "domain-capability": ("semantic_cohesion", "invariant_protection", "boundary_integrity"),
    "infra-platform": ("blast_radius", "cost_efficiency", "provisioning_latency", "access_control"),
    "appendix": ("navigability", "traceability", "freshness"),
    "identity-access": ("revocation_latency", "token_lifetime", "session_integrity", "auditability"),
    "storage": ("durability", "throughput", "partition_tolerance", "replication_lag"),
    # specification. Each set names what the archetype's pages are judged on, which is
    # also the shortest honest answer to "why is this a separate archetype".
    "ai-system": ("answer_quality", "grounding_rate", "inference_latency", "token_cost"),
    "business-capability": ("capability_coverage", "handoff_latency", "ownership_clarity"),
    "quality-assurance": ("defect_escape_rate", "coverage_of_named_risk", "feedback_latency"),
    "delivery-pipeline": ("lead_time", "change_failure_rate", "rollback_time", "deployment_frequency"),
    "documentation-surface": ("freshness_lag", "answer_findability", "source_traceability"),
}

NAMED_ARCHETYPE = "named-archetype"
CLUSTER_DEFAULT = "cluster-default"


@dataclass(frozen=True)
class ModuleResolution:
    """How one skill got its module vocabulary, and what that vocabulary is."""

    archetype: str
    basis: str
    basis_note: str
    modules: tuple[OutputModule, ...]
    quality_attributes: tuple[str, ...] = ()


def resolve_output_modules(cluster_id: str, skill_id: str) -> ModuleResolution:
    """Resolve `(cluster, skill)` to its concern modules, recording *how*.

    Raises `KeyError` for a cluster with no stated default: a new cluster must
    declare one rather than silently emitting a skill with no modules.
    """
    archetype = SKILL_ARCHETYPE.get((cluster_id, skill_id))
    if archetype is not None:
        note = f"`{skill_id}` is declared against the `{archetype}` archetype."
        basis = NAMED_ARCHETYPE
    elif (cluster_id, skill_id) in CLUSTER_DEFAULT_FITNESS_NOTES:
        archetype = CLUSTER_DEFAULT_ARCHETYPE[cluster_id]
        basis = CLUSTER_DEFAULT
        note = CLUSTER_DEFAULT_FITNESS_NOTES[(cluster_id, skill_id)]
    else:
        raise ValueError(
            f"Skill ({cluster_id!r}, {skill_id!r}) has no declared archetype in SKILL_ARCHETYPE "
            f"and no fitness note in CLUSTER_DEFAULT_FITNESS_NOTES"
        )
    modules = tuple(sorted(ARCHETYPE_MODULES[archetype], key=lambda m: (m.path, m.id)))
    quality_attrs = ARCHETYPE_QUALITY_ATTRIBUTES.get(archetype, ())
    return ModuleResolution(archetype, basis, note, modules, quality_attrs)


def _validate() -> None:
    """Fail at import, not at generation time, on a malformed vocabulary."""
    # The twelve of PLAN section 4, plus the five specification adds. The set is pinned rather
    # than derived so that adding an archetype is a decision someone had to write
    # down here, next to the reason — which is what stopped `security-control`
    # from being the thirteenth (plan section 5): measuring first showed its cluster
    # already ran on `identity-access`, and two concerns on that closed the gap.
    expected = {
        "appendix", "backend-service", "data-platform", "domain-capability", "frontend",
        "identity-access", "infra-platform", "integration-adapter", "library-sdk",
        "observability", "plugin-extension", "storage",
        "ai-system", "business-capability", "delivery-pipeline", "documentation-surface",
        "quality-assurance",
    }
    if set(ARCHETYPE_MODULES) != expected:
        raise ValueError(f"archetype set drifted from expected catalog: {sorted(set(ARCHETYPE_MODULES) ^ expected)}")
    if set(ARCHETYPE_QUALITY_ATTRIBUTES) != expected:
        raise ValueError(f"ARCHETYPE_QUALITY_ATTRIBUTES drifted: {sorted(set(ARCHETYPE_QUALITY_ATTRIBUTES) ^ expected)}")
    for arch, qas in ARCHETYPE_QUALITY_ATTRIBUTES.items():
        if not qas:
            raise ValueError(f"archetype {arch!r} declares no quality attributes")
    for archetype, modules in sorted(ARCHETYPE_MODULES.items()):
        if not modules:
            raise ValueError(f"archetype {archetype!r} has no modules")
        ids = [m.id for m in modules]
        if len(set(ids)) != len(ids):
            raise ValueError(f"archetype {archetype!r} repeats a module id")
        prefixes = [m.id_prefix for m in modules]
        if len(set(prefixes)) != len(prefixes):
            raise ValueError(f"archetype {archetype!r} repeats an ID prefix; modules would share a namespace")
        for module in modules:
            if module.page_class not in PAGE_CLASS_TEMPLATE:
                raise ValueError(f"{archetype}.{module.id}: unknown page class {module.page_class!r}")
            if module.id_prefix not in ALLOWED_ID_PREFIXES:
                raise ValueError(f"{archetype}.{module.id}: prefix {module.id_prefix!r} outside the validator vocabulary")
            if not module.consumers or not module.cadence or not module.approver or not module.checklist:
                raise ValueError(f"{archetype}.{module.id}: missing the required module evidence fields")

    # R4.3: Validate that every cluster default fitness note cites a concern the default genuinely provides
    for (cluster_id, skill_id), note in CLUSTER_DEFAULT_FITNESS_NOTES.items():
        default_arch = CLUSTER_DEFAULT_ARCHETYPE[cluster_id]
        arch_mod_ids = {m.id for m in ARCHETYPE_MODULES[default_arch]}
        if not any(mod_id in note for mod_id in arch_mod_ids):
            raise ValueError(
                f"CLUSTER_DEFAULT_FITNESS_NOTES for ({cluster_id!r}, {skill_id!r}) does not cite any concern "
                f"module id from default archetype {default_arch!r} (available: {sorted(arch_mod_ids)}): {note!r}"
            )

    # MOD-6: an alias table that can point at nothing is worse than no alias table,
    # because the link it was written to keep alive fails silently instead of loudly.
    declared = declared_module_folders()
    chain = {}
    for alias in MODULE_FOLDER_ALIASES:
        if not (alias.was and alias.now and alias.since and alias.reason):
            raise ValueError(f"module folder alias {alias.was!r} is missing a required alias record field")
        if alias.was in declared:
            raise ValueError(
                f"alias {alias.was!r} is also a live concern-module folder; an alias may not shadow a module"
            )
        if alias.was in chain:
            raise ValueError(f"alias {alias.was!r} is recorded twice; one old name resolves to one new name")
        chain[alias.was] = alias.now
    for was in chain:
        seen, current = [], was
        while current in chain:
            if current in seen:
                raise ValueError(f"alias chain from {was!r} cycles through {current!r}")
            seen.append(current)
            current = chain[current]
        if current not in declared:
            raise ValueError(f"alias {was!r} resolves to {current!r}, which no archetype declares")
    unknown = {name for name in CLUSTER_DEFAULT_ARCHETYPE.values()} - set(ARCHETYPE_MODULES)
    if unknown:
        raise ValueError(f"cluster default names unknown archetype(s): {sorted(unknown)}")
    unknown = set(SKILL_ARCHETYPE.values()) - set(ARCHETYPE_MODULES)
    if unknown:
        raise ValueError(f"skill declaration names unknown archetype(s): {sorted(unknown)}")


_validate()
