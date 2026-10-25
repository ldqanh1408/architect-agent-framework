"use strict";
(function () {
  const SVG_NS = "http://www.w3.org/2000/svg";

  const FORBIDDEN_CODES = [
    ["consumesApi", "calls API of"],
    ["providesApi", "provides API to"],
    ["api_contract", "API contract"],
    ["required_seam", "required obligation"],
    ["chưa có chủ", "unassigned owner"],
    ["what does this", "scope question"],
    ["slot khung", "khung trống"],
    ["còn khuôn", "chưa điền mẫu"],
    ["_application_", " application "],
  ];

  function safeText(input) {
    let out = String(input == null ? "" : input);
    for (const [bad, good] of FORBIDDEN_CODES) {
      out = out.split(bad).join(good);
    }
    out = out.replace(/\b(\d{2})_([a-z0-9_]+)\b/g, (_, d, rest) => `${d} · ${rest.replace(/_/g, " ")}`);
    return out;
  }

  function el(tag, text, className, attrs) {
    const node = document.createElement(tag);
    if (text !== undefined && text !== null && text !== "") {
      node.textContent = safeText(text);
    }
    if (className) {
      node.className = className;
    }
    if (attrs) {
      for (const [k, v] of Object.entries(attrs)) {
        if (v !== undefined && v !== null) {
          node.setAttribute(k, String(v));
        }
      }
    }
    return node;
  }

  function svgEl(tag, attrs, text) {
    const node = document.createElementNS(SVG_NS, tag);
    if (attrs) {
      for (const [k, v] of Object.entries(attrs)) {
        if (v !== undefined && v !== null) {
          node.setAttribute(k, String(v));
        }
      }
    }
    if (text !== undefined && text !== null && text !== "") {
      node.textContent = safeText(text);
    }
    return node;
  }

  function humanizeSlug(raw) {
    const base = String(raw || "")
      .replace(/\.(md|yml|yaml|feature|json)$/i, "")
      .replace(/^(\d{2,4}-)/, "");
    const ACRONYMS = new Set([
      "api", "adr", "urd", "c1", "c2", "c3", "c4", "uml", "bpmn", "ddd",
      "slo", "sla", "iam", "jwt", "mtls", "rag", "mcp", "cdc", "etl",
      "bff", "sdk", "sre", "uc", "scn", "fit", "cr", "tkt", "id", "ui", "ux", "ai",
    ]);
    return base
      .split(/[-_]+/)
      .filter(Boolean)
      .map((w) =>
        ACRONYMS.has(w.toLowerCase())
          ? w.toUpperCase()
          : w.charAt(0).toUpperCase() + w.slice(1)
      )
      .join(" ");
  }

  function inferV3SlotMeta(rawPath, kind) {
    const cleanPath = String(rawPath || "").replace(/^\/+|\/+$/g, "");
    const rawParts = cleanPath.split("/").filter(Boolean);
    let parts = rawParts.slice();
    if (parts[0] === "documents") parts = parts.slice(1);
    if (parts[0] === "architecture") parts = parts.slice(1);

    let band = "root";
    let bandColor = "var(--accent)";
    let bandLabel = "Workspace Root";
    if (parts.length > 0) {
      const p0 = parts[0];
      if (p0.startsWith("00-")) {
        band = "00-system-views";
        bandColor = "var(--b00)";
        bandLabel = "00 · System Views";
      } else if (p0.startsWith("01-") || p0 === "requirements") {
        band = "01-global-strategy";
        bandColor = "var(--b01)";
        bandLabel = "01 · Global Strategy";
      } else if (p0.startsWith("02-") || p0 === "domains") {
        band = "02-domains";
        bandColor = "var(--b02)";
        bandLabel = "02 · Domains";
      } else if (p0.startsWith("03-")) {
        band = "03-cross-cutting";
        bandColor = "var(--b03)";
        bandLabel = "03 · Cross-Cutting";
      } else if (p0.startsWith("04-")) {
        band = "04-delivery";
        bandColor = "var(--b04)";
        bandLabel = "04 · Delivery";
      }
    }

    const basename = rawParts[rawParts.length - 1] || "";
    const derivedSet = new Set([
      "index.md",
      "00-index.md",
      "00-scenario-index.md",
      "use-case-matrix.md",
      "container-module-mapping.md",
      "atomic-requirements-register.md",
      "traceability-matrix.md",
      "urd-coverage-ledger.md",
      "domains-index.md",
    ]);
    let slotCode = "M";
    if (derivedSet.has(basename) || rawParts.includes("generated")) {
      slotCode = "D";
    } else if (
      parts.some((seg) => /^(1[1-9]|2[0-9])-/.test(seg)) ||
      parts.includes("02-security") ||
      parts.includes("00-planning")
    ) {
      slotCode = "S";
    } else if (
      parts.some((seg) =>
        [
          "activities",
          "processes",
          "classes",
          "components",
          "environments",
          "05-information",
          "sequences",
          "style-assessments",
          "change-requests",
          "gap-register",
          "reviews",
          "routing",
          "_shared-adapters",
          "_shared-contracts",
          "_shared-kernel",
          "01-mechanisms",
          "03-infrastructure",
          "05-exceptions",
          "06-reference-library",
          "tickets",
          "02-release",
          "03-ops",
        ].includes(seg)
      ) ||
      /^(SCN-|CR-|FIT-|TKT-)/.test(basename) ||
      ["uml-overview.md", "cost-model.md", "technical-debt.md", "composition-root.md"].includes(basename)
    ) {
      slotCode = "C";
    }

    const arc42Info = inferArc42Section(rawPath, kind);
    return {
      band,
      bandColor,
      bandLabel,
      slotCode,
      arc42: arc42Info.code,
      arc42TitleEn: arc42Info.titleEn,
      arc42TitleVi: arc42Info.titleVi,
      arc42Order: arc42Info.order,
    };
  }

  const ARC42_SECTIONS = [
    { order: 1, code: "§1", titleEn: "§1 · Introduction & Goals", titleVi: "§1 · Giới thiệu, Mục tiêu & Yêu cầu (Goals & Requirements)" },
    { order: 2, code: "§2", titleEn: "§2 · Architecture Constraints", titleVi: "§2 · Ràng buộc & Giả định Kiến trúc (Constraints)" },
    { order: 3, code: "§3", titleEn: "§3 · System Scope & Context (C1)", titleVi: "§3 · Phạm vi & Ngữ cảnh Hệ thống (C1 Context)" },
    { order: 4, code: "§4", titleEn: "§4 · Solution Strategy", titleVi: "§4 · Chiến lược Giải pháp & Tiêu chuẩn (Strategy)" },
    { order: 5, code: "§5", titleEn: "§5 · Building Block View (C2 & Whiteboxes)", titleVi: "§5 · Khối Xây dựng (C2 Containers & Domain Whiteboxes)" },
    { order: 6, code: "§6", titleEn: "§6 · Runtime View (Scenarios)", titleVi: "§6 · Góc nhìn Thực thi & Luồng Kịch bản (Runtime)" },
    { order: 7, code: "§7", titleEn: "§7 · Deployment View (Infra & Mesh)", titleVi: "§7 · Góc nhìn Triển khai & Hạ tầng (Deployment)" },
    { order: 8, code: "§8", titleEn: "§8 · Cross-cutting Concepts", titleVi: "§8 · Khái niệm Xuyên suốt (Security, Idempotency, Resilience)" },
    { order: 9, code: "§9", titleEn: "§9 · Architecture Decisions (ADRs)", titleVi: "§9 · Quyết định Kiến trúc (ADRs)" },
    { order: 10, code: "§10", titleEn: "§10 · Quality Requirements & Fitness", titleVi: "§10 · Yêu cầu Chất lượng (SLOs) & Fitness Functions" },
    { order: 11, code: "§11", titleEn: "§11 · Risks, Technical Debt & Delivery", titleVi: "§11 · Rủi ro, Nợ kỹ thuật & Bàn giao (Risks & Delivery)" },
    { order: 12, code: "§12", titleEn: "§12 · Glossary & Workspace Index", titleVi: "§12 · Từ điển Thuật ngữ & Mục lục (Glossary)" },
  ];

  function inferArc42Section(rawPath, kind) {
    const p = String(rawPath || "").toLowerCase();
    const k = String(kind || "").toLowerCase();
    const byOrder = (n) => ARC42_SECTIONS[n - 1] || ARC42_SECTIONS[4];

    if (p.includes("glossary.md") || p === "readme.md" || p.endsWith("/index.md") || p === "documents/index.md" || p.includes("visual-source-map")) {
      return byOrder(12);
    }
    if (p.includes("constraints.md") || p.includes("assumptions.md")) {
      return byOrder(2);
    }
    if (p.includes("01-context") || p.includes("c1-context") || p.includes("c0-landscape") || p.includes("system-scope")) {
      return byOrder(3);
    }
    if (
      p.includes("problem-brief") ||
      p.includes("goals-non-goals") ||
      p.includes("01-requirements/requirements.md") ||
      p.includes("atomic-requirements") ||
      p.includes("00-viewpoints") ||
      p.includes("02-functional") ||
      k === "use_case" ||
      k === "viewpoint"
    ) {
      return byOrder(1);
    }
    if (
      p.includes("quality-attributes") ||
      p.includes("traceability-matrix") ||
      p.includes("urd-coverage") ||
      p.includes("04-fitness-functions") ||
      p.includes("08_quality_attribute_architecture")
    ) {
      return byOrder(10);
    }
    if (p.includes("02-strategy") || p.includes("03-standards") || p.endsWith("01-global-strategy/architecture.md")) {
      return byOrder(4);
    }
    if (p.includes("05-governance/decisions") || k === "adr") {
      return byOrder(9);
    }
    if (p.includes("04-risks") || p.includes("05-governance") || p.includes("04-delivery") || p.includes("09_delivery_architecture")) {
      return byOrder(11);
    }
    if (p.includes("06-runtime") || k === "flow" || k === "runtime_scenario") {
      return byOrder(6);
    }
    if (p.includes("04-deployment") || p.includes("03-infrastructure") || p.includes("06_infrastructure_architecture")) {
      return byOrder(7);
    }
    if (p.includes("03-cross-cutting")) {
      return byOrder(8);
    }
    if (p.includes("03-structure") || p.includes("05-information") || p.includes("02-domains") || p.includes("composition-root")) {
      return byOrder(5);
    }
    return byOrder(5);
  }

  function summarizeArtifactNode(nodeObj) {
    if (nodeObj.summary) return safeText(nodeObj.summary);
    const p = String(nodeObj.path || "").toLowerCase();
    if (p.includes("correspondence-rules")) return "ISO-42010 cross-view consistency invariants (C1↔C2↔L2↔Runtime)";
    if (p.includes("stakeholder-concern")) return "Maps 14 stakeholder roles to architectural viewpoints & gates";
    if (p.includes("viewpoint-catalog")) return "Defines 6 canonical viewpoints: Context, Functional, Structure, Data, Runtime, Ops";
    if (p.includes("c1-context")) return "System boundary, external payment rails, card networks & regulator actors";
    if (p.includes("c2-container")) return "Deployable containers, Kafka event mesh, Ledger DB & HSM vault boundaries";
    if (p.includes("logical-l2-submodules")) return "Decomposition of L2 domain submodules, ownership & seam dependencies";
    if (p.includes("requirements.md") || p.includes("requirement.md")) return "Authoritative functional & SLA requirements (REQ-021..REQ-029)";
    if (p.includes("quality-attributes")) return "99.995% availability, p99 <= 280ms gateway latency, RPO=0 ledger durability";
    if (p.includes("solution-strategy")) return "Hexagonal ports, async webhook reconciliation & double-entry ledger strategy";
    if (p.includes("context-map")) return "DDD Bounded Context relationships (Conformist, ACL, Customer-Supplier, OHS)";
    if (p.includes("security-and-auth")) return "Zero-Trust SPIFFE/SPIRE mTLS, FIDO2 WebAuthn passkeys & scoped JWTs";
    if (p.includes("threat-model")) return "STRIDE threat matrix: replay mitigation, webhook signature & key rotation";
    if (p.includes("fitness-functions")) return "Executable architectural fitness checks enforcing acyclic dependencies & SLA";
    if (p.includes("routing.md")) return "Edge ingress rate-limiting, SHA-256 Idempotency-Key lock & canary routing";
    if (p.includes("api.md") || p.includes("-api.md")) return "REST/gRPC contract, 30000ms timeout ceiling & UNKNOWN state machine";
    if (p.includes("flow.md") || p.includes("scn-")) return "End-to-end runtime sequence: ingress lock -> authorization -> webhook ledger commit";
    if (p.includes("adapter-pattern") || p.includes("decisions/")) return "ADR: Isolate third-party acquirer SDKs behind vendor-neutral port contracts";
    if (p.includes("-design.md")) return `Core internal domain design & invariant enforcement (${nodeObj.owner})`;
    if (p.includes("-overview.md")) return `Submodule scope, bounded context boundaries & owned seams (${nodeObj.owner})`;
    return `${humanizeSlug(nodeObj.label || nodeObj.id)} (${nodeObj.kind} · ${nodeObj.owner})`;
  }

  let cachedV3Model = null;
  function getMaximalV3CatalogueModel() {
    if (cachedV3Model) return cachedV3Model;

    const rawEntries = [
      ["documents/architecture/00-system-views/00-viewpoints/correspondence-rules.md", "M", "viewpoint", "01-system-architect", ["V3-VIEW-01"], "ISO-42010 model correspondence rules linking C1/C2 containers to L2 domain ports"],
      ["documents/architecture/00-system-views/00-viewpoints/stakeholder-concern-matrix.md", "M", "viewpoint", "01-system-architect", ["V3-VIEW-01"], "Maps Principal Architect, SecOps, SRE, and Compliance concerns to verification views"],
      ["documents/architecture/00-system-views/00-viewpoints/viewpoint-catalog.md", "M", "viewpoint", "01-system-architect", ["V3-VIEW-01"], "Canonical catalog of 6 architectural viewpoints and required notation standards"],
      ["documents/architecture/00-system-views/01-context/c1-context.md", "M", "diagram", "01-system-architect", ["V3-CTX-01"], "C4 Level 1 System Context: OmniPay Core, Acquirer Rails, Fraud AI & Central Bank"],
      ["documents/architecture/00-system-views/02-functional/activities/uc-001-checkout/uml-activity-diagram.md", "C", "diagram", "activity-diagram", ["V3-UC-01"], "Swimlane activity flow for multi-tender checkout & fallback routing"],
      ["documents/architecture/00-system-views/02-functional/processes/settlement-clearing/bpmn-2-0-process-diagram.md", "C", "diagram", "business-process-modeling", ["V3-UC-01"], "BPMN 2.0 T+0 instant merchant settlement and dispute reserve workflow"],
      ["documents/architecture/00-system-views/02-functional/use-cases/UC-001-instant-checkout.md", "M", "use_case", "00-requirement-clarifier", ["V3-UC-01"], "Primary actor preconditions, postconditions & timeout recovery guarantees"],
      ["documents/architecture/00-system-views/02-functional/use-case-matrix.md", "D", "use_case", "01-system-architect", [], "Derived cross-reference matrix mapping 18 Use Cases to L2 Domain Modules"],
      ["documents/architecture/00-system-views/03-structure/classes/payment-kernel/uml-class-diagram.md", "C", "diagram", "class-diagram", [], "Domain aggregate root entities: PaymentIntent, LedgerEntry, IdempotencyLease"],
      ["documents/architecture/00-system-views/03-structure/components/payment-orchestrator/c4-component-diagram-mermaid-plantuml.md", "C", "diagram", "component-diagram", [], "C4 L3 internal components of the Payment Orchestrator container"],
      ["documents/architecture/00-system-views/03-structure/c2-container.md", "M", "diagram", "01-system-architect", ["V3-C2-01"], "C4 Level 2 Container topology: Edge BFF, Orchestrator, Risk AI, CockroachDB, Kafka"],
      ["documents/architecture/00-system-views/03-structure/container-module-mapping.md", "D", "overview", "01-system-architect", [], "Derived deployment mapping from logical L2 submodules to runtime containers"],
      ["documents/architecture/00-system-views/03-structure/logical-l2-submodules.md", "M", "overview", "01-system-architect", ["V3-L2-01"], "Authoritative decomposition of 10 Domain Families & 92 specialized submodules"],
      ["documents/architecture/00-system-views/03-structure/uml-overview.md", "C", "diagram", "01-system-architect", [], "High-level package dependency graph enforcing strict acyclic layering"],
      ["documents/architecture/00-system-views/04-deployment/environments/prod-multi-region/network-architecture-diagram.md", "C", "diagram", "network-architect", [], "Multi-AZ VPC transit gateway, private link acquirer tunnels & WAF perimeter"],
      ["documents/architecture/00-system-views/04-deployment/environments/prod-multi-region/uml-deployment-diagram.md", "C", "diagram", "deployment-architect", [], "Active-Active EKS cluster topology across ap-southeast-1 and eu-central-1"],
      ["documents/architecture/00-system-views/04-deployment/c4-deployment.md", "M", "diagram", "deployment-architect", [], "Production infrastructure bill of materials, HSM enclaves & DR failover"],
      ["documents/architecture/00-system-views/05-information/payment-ledger-dataset.md", "C", "data_entity", "database-architect", [], "Immutable double-entry journal schema, partitioning key & PII tokenization"],
      ["documents/architecture/00-system-views/06-runtime/sequences/saga-capture-settlement/saga-step-sequence-diagram.md", "C", "diagram", "workflow-orchestration-architect", [], "Distributed saga orchestration with compensating ledger reversal steps"],
      ["documents/architecture/00-system-views/06-runtime/sequences/scn-001-timeout-webhook/uml-sequence-diagram.md", "C", "diagram", "01-system-architect", [], "Sequence interactions when provider times out at 30000ms and webhook resolves"],
      ["documents/architecture/00-system-views/06-runtime/00-scenario-index.md", "D", "runtime_scenario", "01-system-architect", [], "Derived catalog of runtime scenarios and chaos failure injection paths"],
      ["documents/architecture/00-system-views/06-runtime/SCN-001-timeout-reconciliation.md", "C", "runtime_scenario", "01-system-architect", ["V3-SCN-01"], "Runtime trace for REQ-021 ambiguous timeout state & out-of-order webhook"],
      ["documents/architecture/00-system-views/visual-source-map.md", "M", "overview", "01-system-architect", [], "Bindings between Mermaid/PlantUML diagram blocks and canonical model IDs"],

      ["documents/architecture/01-global-strategy/00-context/assumptions.md", "M", "overview", "00-requirement-clarifier", [], "Operational assumptions on acquirer webhook SLA (<15m) & clock skew (<50ms)"],
      ["documents/architecture/01-global-strategy/00-context/glossary.md", "M", "overview", "00-requirement-clarifier", [], "Ubiquitous language definitions: PaymentIntent, Obligation Seam, Snapshot Digest"],
      ["documents/architecture/01-global-strategy/00-context/goals-non-goals.md", "M", "overview", "00-requirement-clarifier", [], "Strategic objectives (99.995% uptime, zero double-charge) & explicit non-goals"],
      ["documents/architecture/01-global-strategy/00-context/problem-brief.md", "M", "overview", "00-requirement-clarifier", [], "Executive problem statement: eliminating split-brain state during payment timeouts"],
      ["documents/architecture/01-global-strategy/00-context/system-scope-specification.md", "M", "requirement", "01-system-architect", ["V3-SCOPE-01"], "In-scope vs out-of-scope system boundaries and external regulatory interfaces"],
      ["documents/architecture/01-global-strategy/01-requirements/atomic-requirements-register.md", "D", "requirement", "00-requirement-clarifier", [], "Derived atomic clause ledger with SHA-256 revision bindings and owners"],
      ["documents/architecture/01-global-strategy/01-requirements/constraints.md", "M", "requirement", "00-requirement-clarifier", [], "PCI-DSS v4.0 Level 1, SBV circular data residency & zero-outbound sandbox rules"],
      ["documents/architecture/01-global-strategy/01-requirements/quality-attributes.md", "M", "requirement", "01-system-architect", ["V3-NFR-01"], "Quantitative quality attribute scenarios: latency, throughput, RPO=0, RTO<60s"],
      ["documents/architecture/01-global-strategy/01-requirements/requirements.md", "M", "requirement", "00-requirement-clarifier", ["V3-REQ-001", "V3-REQ-002"], "Primary functional requirements specification (REQ-021 Timeout, REQ-022 Idempotency)"],
      ["documents/architecture/01-global-strategy/01-requirements/traceability-matrix.md", "D", "verification", "02-spec-critic", [], "End-to-end forward & backward traceability from clauses to APIs and fitness tests"],
      ["documents/architecture/01-global-strategy/01-requirements/urd-coverage-ledger.md", "D", "verification", "02-spec-critic", [], "Verification ledger proving 100% URD clause coverage across domain contracts"],
      ["documents/architecture/01-global-strategy/02-strategy/style-assessments/modular-hexagonal-event-mesh.md", "C", "decision", "01-system-architect", [], "Trade-off evaluation of Hexagonal Ports + Transactional Outbox vs Sync RPC"],
      ["documents/architecture/01-global-strategy/02-strategy/architecture-principles.md", "M", "decision", "01-system-architect", [], "10 foundational principles: Explicit Seams, Immutable Ledger, Fail-Closed Auth"],
      ["documents/architecture/01-global-strategy/02-strategy/solution-strategy.md", "M", "decision", "01-system-architect", ["V3-STRAT-01"], "Core architectural approach for deterministic state transitions & auditability"],
      ["documents/architecture/01-global-strategy/02-strategy/technology-selection.md", "M", "decision", "01-system-architect", [], "Approved tech radar: Rust/Go core services, PostgreSQL/CockroachDB, Kafka, WebAuthn"],
      ["documents/architecture/01-global-strategy/03-standards/standards-register.md", "M", "standard_entry", "01-system-architect", ["V3-STD-01"], "Enterprise coding, API versioning, RFC-9457 problem details & OpenTelemetry standards"],
      ["documents/architecture/01-global-strategy/03-standards/idempotency-and-retry-standards.md", "C", "standard_entry", "01-system-architect", [], "Normative standard for SHA-256 payload fingerprinting & exponential backoff"],
      ["documents/architecture/01-global-strategy/04-risks/cost-model.md", "C", "governance_record", "cost-optimization-architect", [], "Unit economics per 1M transactions: compute, cross-AZ egress & HSM crypto ops"],
      ["documents/architecture/01-global-strategy/04-risks/risk-register.md", "M", "governance_record", "01-system-architect", [], "Top architectural risks, severity scores, mitigation owners & contingency plans"],
      ["documents/architecture/01-global-strategy/04-risks/technical-debt.md", "C", "governance_record", "01-system-architect", [], "Tracked architectural debt items, interest rate impact & remediation milestones"],
      ["documents/architecture/01-global-strategy/05-governance/change-requests/CR-014-timeout-reconciliation.md", "C", "change_request", "01-system-architect", [], "Change request introducing UNKNOWN state and async webhook resolution"],
      ["documents/architecture/01-global-strategy/05-governance/decisions/0000-deferred-register.md", "M", "adr", "adr-authoring", [], "Ledger of consciously deferred architectural decisions and trigger thresholds"],
      ["documents/architecture/01-global-strategy/05-governance/decisions/0001-hexagonal-payment-gateway-port.md", "C", "adr", "adr-authoring", ["V3-ADR-001"], "ADR-0001: Decouple core payment state machine from external provider SDKs"],
      ["documents/architecture/01-global-strategy/05-governance/gap-register/GAP-003-webhook-replay-window.md", "C", "governance_record", "02-spec-critic", [], "Resolved specification gap on 300-second HMAC timestamp tolerance window"],
      ["documents/architecture/01-global-strategy/05-governance/reviews/REV-20261020-candidate-gate.md", "C", "audit_report", "02-spec-critic", [], "Independent semantic critique & completeness audit report for candidate snapshot"],
      ["documents/architecture/01-global-strategy/05-governance/routing/verdict-candidate-ready.md", "C", "decision", "01-system-architect", [], "Governance routing verdict certifying obligation closure for human review"],
      ["documents/architecture/01-global-strategy/architecture.md", "M", "overview", "01-system-architect", ["V3-ARCH-01"], "Master Executive Architecture Overview synthesizing strategy, views & governance"],
      ["documents/architecture/01-global-strategy/composition-root.md", "C", "mechanism", "01-system-architect", [], "Dependency injection assembly & startup lifecycle wiring for production runtime"],

      ["documents/architecture/02-domains/00-overview/context-map.md", "M", "overview", "bounded-context-architect", ["V3-DDD-01"], "Enterprise DDD Context Map across Checkout, Payments, Ledger, Risk AI & IAM"],
      ["documents/architecture/02-domains/00-overview/domains-index.md", "D", "overview", "01-system-architect", [], "Derived registry of all active domain families, bounded contexts & seam owners"],
      ["documents/architecture/02-domains/_shared-adapters/acquirer-iso8583-adapter.md", "C", "mechanism", "integration-adapter-architect", [], "Anti-corruption layer translating ISO-8583 financial messages to domain events"],
      ["documents/architecture/02-domains/_shared-contracts/00-core/money-and-currency-types.md", "C", "data_entity", "01-system-architect", [], "Shared kernel value objects: MinorUnitMoney, ISO4217Currency, SnapshotDigest"],
      ["documents/architecture/02-domains/_shared-contracts/01-data/payment-intent-entity.md", "C", "data_entity", "domain-model-architect", [], "Canonical state machine & schema for PaymentIntent across domain boundaries"],
      ["documents/architecture/02-domains/_shared-contracts/02-apis/payment-intents-v1/payment-intents-v1.md", "C", "api", "api-architect", ["V3-API-01"], "OpenAPI 3.1 / gRPC contract for POST /v1/payments/intents (30000ms SLA)"],
      ["documents/architecture/02-domains/_shared-contracts/02-apis/rest-problem-details-standard.md", "C", "api", "api-architect", [], "RFC-9457 error envelope standard with deterministic retryable classification"],
      ["documents/architecture/02-domains/_shared-contracts/03-messages/payment-state-transition-event.md", "C", "event_message", "event-driven-architect", [], "CloudEvents 1.0 Avro/JSON schema for PaymentIntentStateChanged topic"],
      ["documents/architecture/02-domains/_shared-contracts/04-external/stripe-adyen-webhook-contract.md", "C", "api", "integration-adapter-architect", [], "External provider webhook ingress signature verification & payload contract"],
      ["documents/architecture/02-domains/_shared-contracts/05-state-machines/payment-intent/uml-state-diagram.md", "C", "diagram", "workflow-architect", [], "Formal state machine diagram: CREATED -> AUTHORIZING -> UNKNOWN -> CAPTURED/FAILED"],
      ["documents/architecture/02-domains/_shared-contracts/05-state-machines/payment-intent/payment-intent.md", "C", "mechanism", "workflow-architect", [], "Transition guard invariants & idempotent replay rules for PaymentIntent"],
      ["documents/architecture/02-domains/_shared-kernel/idempotency-fingerprint.md", "C", "data_entity", "ddd-architect", [], "Shared deterministic SHA-256 request canonicalization algorithm"],

      ["documents/architecture/03-cross-cutting/00-overview.md", "M", "overview", "01-system-architect", [], "Cross-cutting platform mechanisms: observability, resilience, security & fitness"],
      ["documents/architecture/03-cross-cutting/01-mechanisms/distributed-idempotency-locking.md", "C", "mechanism", "01-system-architect", [], "Redis Cluster + PostgreSQL advisory lease mechanism preventing concurrent execution"],
      ["documents/architecture/03-cross-cutting/02-security/ai-token-masking-strategy.md", "C", "mechanism", "security-architect", [], "Zero-leakage PAN/PII redaction pipeline before LLM/agent context injection"],
      ["documents/architecture/03-cross-cutting/02-security/secrets-and-key-management.md", "M", "mechanism", "secret-management-architect", ["V3-SEC-01"], "Envelope encryption with AWS KMS / HashiCorp Vault & 90-day automated rotation"],
      ["documents/architecture/03-cross-cutting/02-security/security-and-auth.md", "M", "mechanism", "identity-access-architect", ["V3-SEC-02"], "Zero-Trust workload identity (SPIFFE) and FIDO2 passkey human gate signatures"],
      ["documents/architecture/03-cross-cutting/02-security/threat-model.md", "M", "mechanism", "threat-modeling-architect", [], "Comprehensive STRIDE threat analysis and cryptographic control verification"],
      ["documents/architecture/03-cross-cutting/03-infrastructure/multi-region-active-active.md", "C", "mechanism", "infra-platform-architect", [], "Cell-based regional isolation, deterministic shard routing & BGP anycast"],
      ["documents/architecture/03-cross-cutting/04-fitness-functions/00-overview.md", "M", "verification", "02-spec-critic", ["V3-FIT-01"], "Continuous architecture governance catalog & CI gate enforcement rules"],
      ["documents/architecture/03-cross-cutting/04-fitness-functions/FIT-001-timeout-obligation-guard.md", "C", "verification", "02-spec-critic", [], "Automated contract test verifying 30000ms SLA & UNKNOWN state preservation"],
      ["documents/architecture/03-cross-cutting/05-exceptions/circuit-breaker-and-bulkhead.md", "C", "mechanism", "resilience-architect", [], "Adaptive concurrency limits and acquirer-specific bulkhead isolation pools"],
      ["documents/architecture/03-cross-cutting/06-reference-library/transactional-outbox-pattern.md", "C", "overview", "reference-architecture", [], "Reference implementation for atomic DB commit + Kafka CDC event publication"],

      ["documents/architecture/04-delivery/00-planning/tickets/TKT-101-payment-port-timeout.md", "C", "planning", "release-architect", [], "Implementation work package for PaymentIntentsPort 30s timeout & webhook queue"],
      ["documents/architecture/04-delivery/00-planning/q4-payment-modernization-plan.md", "C", "planning", "release-architect", ["DELIV-PLAN-01"], "Phased delivery roadmap, critical path dependencies & canary rollout waves"],
      ["documents/architecture/04-delivery/01-quality/chaos-and-contract-test-strategy.md", "C", "verification", "testing-architect", [], "Jepsen network partition drills, Pact contract tests & holdout corpus evaluation"],
      ["documents/architecture/04-delivery/02-release/progressive-canary-playbook.md", "C", "planning", "release-architect", [], "Automated 1% -> 10% -> 50% -> 100% traffic shift with SLO burn-rate rollback"],
      ["documents/architecture/04-delivery/03-ops/webhook-reconciliation-runbook.md", "C", "mechanism", "sre-architect", [], "On-call SRE playbook for stuck UNKNOWN intents and acquirer settlement lag"],
      ["documents/architecture/04-delivery/04-audit/qualification-readiness-audit.md", "C", "audit_report", "02-spec-critic", [], "Release qualification dossier verifying zero unresolved obligations & passkey signoff"],

      ["documents/index.md", "D", "overview", "01-system-architect", [], "Root SDD Workspace Manifest & Navigation Index across all 5 Architectural Pillars"],
    ];

    const domainFamilies = [
      {
        folder: "01_business_architecture",
        submodule: "merchant-commerce",
        module: "checkout-value-stream",
        seams: [
          "11-capabilities/checkout-capabilities.md",
          "12-value-streams/checkout-value-streams.md",
          "13-org-topology/checkout-org-topology.md",
        ],
        skills: [
          "business-architect", "business-capability-architect", "business-process-architect",
          "enterprise-architect", "industry-architecture", "organization-architect",
          "product-architect", "reference-architecture", "solution-architect", "value-stream-architect",
        ],
      },
      {
        folder: "02_domain_architecture",
        submodule: "payment-kernel",
        module: "ledger-settlement",
        seams: [
          "11-aggregates/ledger-aggregates.md",
          "12-domain-events/ledger-domain-events.md",
          "13-invariants/ledger-invariants.md",
          "20-policies/ledger-policies.md",
        ],
        skills: [
          "aggregate-architect", "bounded-context-architect", "context-mapping-architect",
          "ddd-architect", "domain-capability-architect", "domain-event-architect",
          "domain-model-architect", "rule-engine-architect", "workflow-architect",
        ],
      },
      {
        folder: "03_application_architecture",
        submodule: "payment-orchestration",
        module: "payment-intents",
        seams: [
          "11-api/payment-intents-api.md",
          "12-events/payment-intents-events.md",
          "13-clients/acquirer-gateway-clients.md",
          "14-data/payment-intents-data.md",
          "20-security/payment-intents-security.md",
          "21-observability/payment-intents-observability.md",
          "22-resilience/payment-intents-resilience.md",
        ],
        skills: [
          "api-architect", "backend-service-architect", "bff-architect", "desktop-architect",
          "edge-architect", "event-driven-architect", "frontend-architect", "gateway-architect",
          "integration-adapter-architect", "library-sdk-architect", "microservice-architect",
          "mobile-architect", "modular-monolith-architect", "monolith-architect",
          "plugin-extension-architect", "workflow-orchestration-architect",
        ],
      },
      {
        folder: "04_ai_architecture",
        submodule: "fraud-risk-intelligence",
        module: "anomaly-scoring-agent",
        seams: [
          "11-model-invocation/anomaly-model-invocation.md",
          "12-prompt-assets/anomaly-prompt-assets.md",
          "13-retrieval/feature-store-retrieval.md",
          "14-memory/session-risk-memory.md",
          "20-guardrails/pii-redaction-guardrails.md",
          "21-evaluation/holdout-auc-evaluation.md",
          "22-token-budget/inference-latency-budget.md",
        ],
        skills: [
          "agent-architect", "ai-system-architect", "evaluation-architect", "mcp-architect",
          "memory-architect", "model-serving-architect", "prompt-architect", "rag-architect",
          "tool-calling-architect", "vector-search-architect",
        ],
      },
      {
        folder: "05_data_architecture",
        submodule: "financial-ledger-store",
        module: "journal-pipeline",
        seams: [
          "11-ingest/journal-cdc-ingest.md",
          "12-storage/cockroach-journal-storage.md",
          "13-serving/reconciliation-olap-serving.md",
          "14-lineage/journal-audit-lineage.md",
          "20-retention/ten-year-regulatory-retention.md",
          "21-quality/zero-imbalance-quality.md",
        ],
        skills: [
          "cache-architect", "cdc-architect", "data-governance-architect", "data-lake-architect",
          "data-pipeline-architect", "data-platform-architect", "data-warehouse-architect",
          "database-architect", "etl-architect", "lakehouse-architect", "master-data-architect",
          "metadata-architect", "search-architect", "streaming-architect", "vector-database-architect",
        ],
      },
      {
        folder: "06_infrastructure_architecture",
        submodule: "cloud-runtime-mesh",
        module: "multi-region-eks",
        seams: [
          "11-topology/multi-region-topology.md",
          "12-provisioning/terraform-gitops-provisioning.md",
          "13-networking/cilium-ebpf-networking.md",
          "20-secrets/kms-hsm-secrets.md",
          "21-cost/finops-autoscale-cost.md",
        ],
        skills: [
          "cloud-architect", "container-architect", "devops-architect", "edge-infrastructure-architect",
          "gitops-architect", "iac-architect", "infra-platform-architect", "kubernetes-architect",
          "network-architect", "platform-engineering-architect", "runtime-architect",
          "serverless-architect", "service-mesh-architect", "storage-architect",
        ],
      },
      {
        folder: "07_security_architecture",
        submodule: "zero-trust-perimeter",
        module: "passkey-and-mtls",
        seams: [
          "11-authn/webauthn-passkey-authn.md",
          "12-authz/opa-policy-authz.md",
          "13-session/short-lived-token-session.md",
          "14-crypto/ed25519-hsm-crypto.md",
          "20-secrets/vault-rotation-secrets.md",
          "21-audit/tamper-evident-audit.md",
          "22-threat-model/payment-stride-threat-model.md",
        ],
        skills: [
          "application-security-architect", "cloud-security-architect", "compliance-architect",
          "identity-access-architect", "key-management-architect", "network-security-architect",
          "privacy-architect", "secret-management-architect", "security-architect",
          "threat-modeling-architect", "zero-trust-architect",
        ],
      },
      {
        folder: "08_quality_attribute_architecture",
        submodule: "reliability-engineering",
        module: "slo-and-chaos",
        seams: [
          "11-test-levels/contract-and-chaos-levels.md",
          "12-performance/p99-latency-benchmark.md",
          "13-resilience-drills/acquirer-blackout-drills.md",
          "20-quality-gates/release-readiness-gates.md",
        ],
        skills: [
          "availability-architect", "capacity-planning-architect", "cost-optimization-architect",
          "disaster-recovery-architect", "observability-architect", "performance-architect",
          "reliability-architect", "resilience-architect", "scalability-architect", "sustainability-architect",
        ],
      },
      {
        folder: "09_delivery_architecture",
        submodule: "progressive-delivery",
        module: "canary-pipeline",
        seams: [
          "11-pipeline/signed-provenance-pipeline.md",
          "12-environments/ephemeral-staging-environments.md",
          "13-release-strategy/blue-green-canary-strategy.md",
          "20-rollback/automated-slo-rollback.md",
        ],
        skills: [
          "deployment-architect", "migration-architect", "modernization-architect",
          "operability-architect", "release-architect", "sre-architect", "testing-architect",
        ],
      },
      {
        folder: "10_documentation_architecture",
        submodule: "architecture-governance",
        module: "sdd-knowledge-graph",
        seams: [
          "11-audience/architect-reviewer-audience.md",
          "12-information-architecture/v3-taxonomy-ia.md",
          "20-freshness/drift-detection-freshness.md",
          "21-alternatives/rejected-design-alternatives.md",
        ],
        skills: [
          "appendix-architect", "architecture-decision-architect", "checklist-architect",
          "diagram-architect", "documentation-architect", "review-architect",
          "specification-architect", "template-architect",
        ],
      },
    ];

    const fullSeamSkills = new Set([
      "business-capability-architect",
      "aggregate-architect",
      "bounded-context-architect",
      "api-architect",
      "gateway-architect",
      "workflow-orchestration-architect",
      "integration-adapter-architect",
      "ai-system-architect",
      "model-serving-architect",
      "database-architect",
      "cdc-architect",
      "kubernetes-architect",
      "zero-trust-architect",
      "identity-access-architect",
      "threat-modeling-architect",
      "resilience-architect",
      "release-architect",
      "specification-architect",
    ]);
    for (const fam of domainFamilies) {
      fam.skills.slice(0, 6).forEach((skill, sIdx) => {
        const base = `documents/architecture/02-domains/${fam.folder}/${fam.submodule}/${skill}`;
        rawEntries.push([
          `${base}/00-overview/${skill}-overview.md`,
          "M",
          "overview",
          skill,
          [],
          `Submodule architecture overview, bounded context responsibilities & seam catalogue (${skill})`,
        ]);
        rawEntries.push([
          `${base}/01-${fam.module}/${fam.module}-design.md`,
          "M",
          "mechanism",
          skill,
          [],
          `Detailed internal component design, state invariants & error recovery for ${fam.module}`,
        ]);
        const seamsToInclude = fullSeamSkills.has(skill) || sIdx === 0 ? fam.seams : fam.seams.slice(0, 1);
        for (const seam of seamsToInclude) {
          const seamTitle = humanizeSlug(seam.split("/").pop());
          rawEntries.push([
            `${base}/01-${fam.module}/${seam}`,
            "S",
            "api",
            skill,
            [],
            `Required Obligation Seam [S]: ${seamTitle} contract & cross-module SLA verification`,
          ]);
        }
        rawEntries.push([
          `${base}/tests/submodule.feature`,
          "M",
          "verification",
          skill,
          [],
          `Executable Gherkin BDD acceptance scenarios verifying ${skill} seam obligations`,
        ]);
        rawEntries.push([
          `${base}/verification/fitness-self-check.md`,
          "M",
          "verification",
          skill,
          [],
          `Automated architectural fitness check & dependency cycle attestation for ${skill}`,
        ]);
        rawEntries.push([
          `${base}/README.md`,
          "M",
          "document",
          skill,
          [],
          `Developer quickstart, local verification commands & artifact inventory for ${skill}`,
        ]);
        rawEntries.push([
          `${base}/self-audit.md`,
          "M",
          "audit_report",
          skill,
          [],
          `Pre-commit SDD completeness self-audit & evidence links for ${skill}`,
        ]);
        rawEntries.push([
          `${base}/source-map.yml`,
          "M",
          "document",
          skill,
          [],
          `Deterministic mapping from ${skill} specification clauses to code paths & tests`,
        ]);
      });
    }

    const nodes = [];
    const clauseNodes = [];
    const artifacts = [];
    const slotCounts = { M: 0, C: 0, D: 0, S: 0 };

    for (const fam of domainFamilies) {
      fam.skills.slice(6).forEach((skill) => {
        if (rawEntries.length >= 690) return;
        const base = `documents/architecture/02-domains/${fam.folder}/${fam.submodule}/${skill}`;
        rawEntries.push([
          `${base}/00-overview/${skill}-overview.md`,
          "M",
          "overview",
          skill,
          [],
          `Submodule architecture overview & bounded context responsibilities (${skill})`,
        ]);
        rawEntries.push([
          `${base}/01-${fam.module}/${fam.module}-design.md`,
          "M",
          "mechanism",
          skill,
          [],
          `Internal component design & state invariants for ${fam.module}`,
        ]);
      });
    }
    rawEntries.splice(690);
    rawEntries.forEach(([path, slotCode, kind, owner, clauses, summaryText], idx) => {
      const id = `V3-${String(idx + 1).padStart(3, "0")}`;
      const meta = inferV3SlotMeta(path, kind);
      meta.slotCode = slotCode;
      slotCounts[slotCode] = (slotCounts[slotCode] || 0) + 1;
      const parts = path.split("/");
      const label = parts[parts.length - 1];
      const rank =
        meta.band === "01-global-strategy"
          ? 0
          : meta.band === "00-system-views"
          ? 1
          : meta.band === "02-domains"
          ? 2
          : meta.band === "03-cross-cutting"
          ? 2
          : 3;

      const cObjs = (clauses || []).map((cid) => ({ id: cid, anchor: cid.toLowerCase() }));
      for (const cid of clauses || []) {
        clauseNodes.push({
          id: cid,
          node_type: "clause",
          artifact_id: id,
          path,
          anchor: cid.toLowerCase(),
          owner: safeText(owner),
          kind: "clause",
          summary: `Normative architectural clause ${cid} enforced by ${label}`,
          upstream: [id],
          downstream: [],
        });
      }

      const nodeObj = {
        id,
        node_type: "artifact",
        path,
        label,
        display_title: humanizeSlug(label),
        summary: summaryText || summarizeArtifactNode({ path, label, kind, owner }),
        kind: safeText(kind),
        owner: safeText(owner),
        revision: `f4db034f07fa-${String(idx + 1).padStart(4, "0")}`,
        folder: safeText(parts.slice(0, -1).join("/")),
        group: meta.bandLabel,
        band: meta.band,
        band_color: meta.bandColor,
        band_label: meta.bandLabel,
        arc42: meta.arc42,
        arc42_order: meta.arc42Order,
        arc42_title_en: meta.arc42TitleEn,
        arc42_title_vi: meta.arc42TitleVi,
        slot_code: slotCode,
        rank,
        clauses: cObjs,
        anchors: ["summary", "traceability", "verification"],
        changed: slotCode === "S" && idx % 9 === 0,
        upstream: [],
        downstream: [],
        upstream_artifacts: [],
        downstream_artifacts: [],
        in_degree: 0,
        out_degree: 0,
      };
      nodes.push(nodeObj);
      artifacts.push({
        id,
        path,
        kind: safeText(kind),
        owner: safeText(owner),
        revision: nodeObj.revision,
        slot_code: slotCode,
      });
    });

    const byPathSub = (substr) => nodes.find((n) => n.path.includes(substr));
    const reqNode = byPathSub("01-requirements/requirements.md") || nodes[0];
    const nfrNode = byPathSub("01-requirements/quality-attributes.md") || nodes[0];
    const stratNode = byPathSub("02-strategy/solution-strategy.md") || nodes[0];
    const adrNode = byPathSub("0001-hexagonal-payment-gateway-port.md") || nodes[0];
    const c1Node = byPathSub("01-context/c1-context.md") || nodes[0];
    const c2Node = byPathSub("03-structure/c2-container.md") || nodes[0];
    const l2Node = byPathSub("03-structure/logical-l2-submodules.md") || nodes[0];
    const scnNode = byPathSub("SCN-001-timeout-reconciliation.md") || nodes[0];
    const ctxMapNode = byPathSub("02-domains/00-overview/context-map.md") || nodes[0];
    const sharedApiNode = byPathSub("payment-intents-v1.md") || nodes[0];
    const secNode = byPathSub("03-cross-cutting/02-security/security-and-auth.md") || nodes[0];
    const fitNode = byPathSub("03-cross-cutting/04-fitness-functions/00-overview.md") || nodes[0];
    const planNode = byPathSub("q4-payment-modernization-plan.md") || nodes[0];

    const edgePairs = [
      [stratNode.id, reqNode.id, "satisfies"],
      [adrNode.id, reqNode.id, "references"],
      [c1Node.id, reqNode.id, "satisfies"],
      [c2Node.id, c1Node.id, "implements_contract"],
      [c2Node.id, stratNode.id, "implements_contract"],
      [l2Node.id, c2Node.id, "implements_contract"],
      [scnNode.id, reqNode.id, "satisfies"],
      [ctxMapNode.id, c2Node.id, "references"],
      [sharedApiNode.id, ctxMapNode.id, "implements_contract"],
      [sharedApiNode.id, adrNode.id, "implements_contract"],
      [secNode.id, nfrNode.id, "satisfies"],
      [fitNode.id, nfrNode.id, "satisfies"],
      [planNode.id, fitNode.id, "references"],
    ];

    const edges = edgePairs.map(([from, to, relation]) => ({ from, to, relation }));
    const artifactEdges = edgePairs.map(([from, to, relation]) => ({
      from,
      to,
      relations: [relation],
      via_clauses: [],
      primary_relation: relation,
    }));

    const nodeById = new Map(nodes.map((n) => [n.id, n]));
    for (const e of artifactEdges) {
      const f = nodeById.get(e.from);
      const tNode = nodeById.get(e.to);
      if (f && tNode) {
        if (!f.upstream.includes(tNode.id)) f.upstream.push(tNode.id);
        if (!f.upstream_artifacts.includes(tNode.id)) f.upstream_artifacts.push(tNode.id);
        if (!tNode.downstream.includes(f.id)) tNode.downstream.push(f.id);
        if (!tNode.downstream_artifacts.includes(f.id)) tNode.downstream_artifacts.push(f.id);
        f.out_degree += 1;
        tNode.in_degree += 1;
      }
    }

    cachedV3Model = {
      workspace: "OMNIPAY-V3-MAXIMAL-CATALOGUE (f4db034f)",
      change_id: "V3-MAXIMAL-PROFILE",
      artifacts,
      document_graph: {
        nodes,
        clause_nodes: clauseNodes,
        edges,
        artifact_edges: artifactEdges,
        obligations: [
          {
            id: "OBL-V3-SEAM-CLOSURE",
            source: "V3-REQ-001",
            source_artifact: reqNode.id,
            consumers: [c2Node.id, sharedApiNode.id],
            owner: "01-system-architect",
            criticality: "critical",
            checks_count: 5,
          },
          {
            id: "OBL-V3-ZERO-TRUST",
            source: "V3-NFR-01",
            source_artifact: nfrNode.id,
            consumers: [secNode.id, fitNode.id],
            owner: "security-architect",
            criticality: "high",
            checks_count: 4,
          },
        ],
        clusters: [],
        stats: {
          artifacts: nodes.length,
          clauses: clauseNodes.length,
          edges: edges.length,
          artifact_edges: artifactEdges.length,
          obligations: 2,
          changed: nodes.filter((n) => n.changed).length,
          slot_counts: slotCounts,
          kinds: Array.from(new Set(nodes.map((n) => n.kind))).sort(),
          owners: Array.from(new Set(nodes.map((n) => n.owner))).sort(),
          relations: ["implements_contract", "references", "satisfies"],
        },
      },
    };
    return cachedV3Model;
  }

  function synthesizeV3Markdown(nodeObj, originMode) {
    const meta = inferV3SlotMeta(nodeObj.path, nodeObj.kind);
    const slotCode = nodeObj.slot_code || meta.slotCode;
    const slotDesc =
      slotCode === "M"
        ? "Mandatory [M] when profile applies"
        : slotCode === "S"
        ? "Required Obligation Seam [S] (Contract & SLA)"
        : slotCode === "D"
        ? "Derived [D] from upstream authority"
        : "Conditional [C] on architectural evidence";
    const title = nodeObj.display_title || humanizeSlug(nodeObj.label || nodeObj.id);
    const summary = summarizeArtifactNode(nodeObj);
    const provenanceTag =
      originMode === "synthetic" || graphState.datasetMode === "v3-maximal"
        ? "SYNTHETIC_V3_CATALOGUE_TEMPLATE"
        : "PREVIEW_READONLY_SAMPLE";

    return [
      "---",
      `artifact_id: ${nodeObj.id}`,
      `source_provenance: "${provenanceTag}"`,
      `slot_contract: "${slotDesc}"`,
      `pillar: "${meta.bandLabel}"`,
      `page_class: ${nodeObj.kind}`,
      `owner_skill: ${nodeObj.owner}`,
      `revision: ${nodeObj.revision}`,
      "---",
      `# ${title} [${slotCode}]`,
      "",
      `> **Architectural Purpose**: ${summary}`,
      "",
      "## 1. Executive Summary & Architectural Scope",
      `This specification governs **${title}** (\`${nodeObj.path}\`) within pillar **${meta.bandLabel}**, authored and maintained by \`${nodeObj.owner}\`. In the V3 Architecture Contract Catalogue, this slot is classified as **${slotDesc}**.`,
      "",
      "## 2. Normative Contract & Invariants",
      "| Dimension | Specification Requirement | Verification Mechanism |",
      "| :--- | :--- | :--- |",
      `| **Timeout & Ambiguity** | Enforce \`30000 ms\` upper bound; transition ambiguous calls to \`UNKNOWN\` | Automated chaos & contract test (\`FIT-001\`) |`,
      `| **Idempotency Guarantee** | Require deterministic \`Idempotency-Key\` bound to payload SHA-256 digest | Edge gateway & advisory lock check (\`REQ-022\`) |`,
      `| **Security & Zero-Trust** | Mutual TLS (SPIFFE) for service-to-service; FIDO2 passkey for human gates | Policy-as-code OPA & KMS key audit |`,
      `| **Observability & Audit** | Emit structured W3C TraceContext spans and immutable outbox events | OpenTelemetry collector & ledger reconciliation |`,
      "",
      "## 3. Upstream & Downstream Traceability",
      `- **Upstream Authorities**: ${(nodeObj.upstream_artifacts || []).join(", ") || "Root Pillar Authority (01-global-strategy)"}`,
      `- **Downstream Consumers**: ${(nodeObj.downstream_artifacts || []).join(", ") || "Verified by Submodule Fitness Suite"}`,
      `- **Canonical Template Binding**: \`vendor/sdd-agent/contracts/workspace-skeleton.yml\``,
      "",
      "## 4. Executable Verification Criteria",
      "- **Schema & Spine Gate**: Passes 4-part SDD structural spine (`Summary`, `Normative Contract`, `Traceability`, `Verification`).",
      "- **Seam Obligation Closure**: Zero unresolved debtor seams or unverified cross-context API calls.",
    ].join("\n");
  }

  function buildFolderTreeFromNodes(nodes) {
    const root = { name: "/", path: "", segments: [], dirs: new Map(), files: [], nodes: [] };
    for (const n of nodes) {
      const parts = String(n.path || "").split("/").filter(Boolean);
      let cur = root;
      let walked = "";
      for (let i = 0; i < parts.length - 1; i++) {
        const part = parts[i];
        walked = walked ? `${walked}/${part}` : part;
        if (!cur.dirs.has(part)) {
          cur.dirs.set(part, {
            name: safeText(part),
            rawName: part,
            path: walked,
            segments: [part],
            dirs: new Map(),
            files: [],
            nodes: [],
          });
        }
        cur = cur.dirs.get(part);
      }
      cur.files.push(n.path);
      cur.nodes.push(n);
    }

    function finish(dirNode) {
      let dirsList = Array.from(dirNode.dirs.entries())
        .sort((a, b) => a[0].localeCompare(b[0]))
        .map(([, d]) => finish(d));

      while (dirsList.length === 1 && dirNode.files.length === 0 && dirNode.path !== "") {
        const only = dirsList[0];
        dirNode = {
          ...dirNode,
          name: `${dirNode.name} / ${only.name}`,
          path: only.path,
          segments: [...dirNode.segments, ...only.segments],
          files: only.files,
          nodes: only.nodes,
        };
        dirsList = only.dirs_list;
      }

      const deep = dirNode.files.length + dirsList.reduce((acc, d) => acc + d.deep, 0);
      const slotCounts = { M: 0, C: 0, D: 0, S: 0 };
      for (const n of dirNode.nodes) {
        const sc = n.slot_code || inferV3SlotMeta(n.path, n.kind).slotCode;
        slotCounts[sc] = (slotCounts[sc] || 0) + 1;
      }
      for (const d of dirsList) {
        for (const k of ["M", "C", "D", "S"]) {
          slotCounts[k] += d.slotCounts?.[k] || 0;
        }
      }

      return {
        name: dirNode.name,
        path: dirNode.path,
        segments: dirNode.segments,
        files: dirNode.files.slice().sort(),
        nodes: dirNode.nodes,
        dirs_list: dirsList,
        deep,
        slotCounts,
      };
    }

    return finish(root);
  }

  const graphState = {
    datasetMode: "workspace", // "workspace" | "v3-maximal"
    layoutMode: "c4-map",     // "c4-map" (DEFAULT: C1 -> C2 -> Container Document Tree & Related Docs) | "drilldown" | "doc-dag" | "radial"
    c4Level: "C2",            // "C1" | "C2" | "CONTAINER_DOCS" (Container Document Tree & Related Specs)
    c1FocusedSystem: "sys.omnipay-core",
    c4FocusedContainer: "ctr.payment-orchestrator",
    c4GuidedFlow: "all",      // "all" | "checkout" | "timeout-webhook" | "fraud-ledger"
    sidebarScope: "container", // "system" (C1 System Docs by arc42) | "container" (C2 Container Docs by arc42) | "hg1" (HG-1 Clauses)
    showAllContainersInPassport: false,
    rightInspectorTab: "node-docs", // "node-docs" (Container Docs) | "system-docs" (System Docs) | "hg1" (HG-1 Clauses)
    activeLeafPath: "documents/architecture/02-domains/03_application_architecture/payment-orchestration/api-architect/01-payment-intents/11-api/payment-intents-api.md",
    activeLeafNode: null,
    traceMode: "all",         // "all" | "upstream" | "downstream"
    relationFilter: "all",
    ownerFilter: "all",
    slotFilter: "all",        // "all" | "M" | "S" | "C" | "D"
    showClauses: true,
    zoom: 1,
    expandedCanvas: false,
    selectedNodeId: null,
    hoveredNodeId: null,
    drillPath: "",
    page: 0,
    pageSize: 15,
    customPositions: new Map(),
    readerMode: "rendered",   // "rendered" | "raw" | "split"
    pendingDocPath: null,
  };

  function getSiblingDocuments(targetDocOrPath, graphData) {
    const v3Nodes = getMaximalV3CatalogueModel().document_graph.nodes || [];
    const wsNodes = (graphData && graphData.nodes) || [];
    const rawPath =
      typeof targetDocOrPath === "string"
        ? targetDocOrPath
        : (targetDocOrPath && targetDocOrPath.path) || graphState.activeLeafPath || "";

    const activeDoc =
      (typeof targetDocOrPath === "object" && targetDocOrPath) ||
      wsNodes.find((n) => n.path === rawPath) ||
      v3Nodes.find((n) => n.path === rawPath) ||
      wsNodes.find((n) => n.id === "API") ||
      wsNodes[0] ||
      v3Nodes[0];

    if (!activeDoc) {
      return {
        activeDoc: null,
        parentFolder: "",
        submoduleFolder: "",
        siblings: [],
        currentIndex: 0,
      };
    }

    const parts = String(activeDoc.path || "").split("/").filter(Boolean);
    const parentFolder = parts.slice(0, -1).join("/");
    const lastDir = parts.length >= 2 ? parts[parts.length - 2] : "";
    let submoduleFolder = parentFolder;
    if (
      /^(00-|01-|1[1-9]-|2[0-9]-|tests$|verification$)/.test(lastDir) &&
      parts.length >= 3
    ) {
      submoduleFolder = parts.slice(0, -2).join("/");
    }

    const combinedByPath = new Map();
    for (const n of wsNodes) {
      if (n && n.path) combinedByPath.set(n.path, n);
    }
    for (const n of v3Nodes) {
      if (n && n.path && !combinedByPath.has(n.path)) {
        combinedByPath.set(n.path, n);
      }
    }

    // 1. Direct same-folder siblings
    const directSiblings = [];
    // 2. Same-level submodule / peer folder siblings
    const peerSiblings = [];

    for (const cand of combinedByPath.values()) {
      const cParts = String(cand.path || "").split("/").filter(Boolean);
      const cParent = cParts.slice(0, -1).join("/");
      if (cParent === parentFolder) {
        directSiblings.push(cand);
      } else if (
        submoduleFolder &&
        (cParent === submoduleFolder || cParent.startsWith(submoduleFolder + "/"))
      ) {
        peerSiblings.push(cand);
      }
    }

    let siblings = [...directSiblings, ...peerSiblings];
    if (siblings.length <= 1 && parts.length >= 3) {
      const broaderFolder = parts.slice(0, -2).join("/");
      for (const cand of combinedByPath.values()) {
        if (
          cand.path !== activeDoc.path &&
          String(cand.path || "").startsWith(broaderFolder + "/") &&
          !siblings.some((s) => s.path === cand.path)
        ) {
          siblings.push(cand);
        }
      }
    }

    siblings = siblings.slice(0, 12);
    const currentIndex = Math.max(
      0,
      siblings.findIndex((s) => s.path === activeDoc.path)
    );

    return {
      activeDoc,
      parentFolder,
      submoduleFolder: submoduleFolder || parentFolder,
      siblings,
      currentIndex,
    };
  }

  function getLang() {
    return document.documentElement.lang === "vi" ? "vi" : "en";
  }

  function t(enText, viText) {
    return getLang() === "vi" ? viText : enText;
  }

  function extractGraphData(model) {
    if (graphState.datasetMode === "v3-maximal") {
      return getMaximalV3CatalogueModel().document_graph;
    }
    if (model && model.document_graph && Array.isArray(model.document_graph.nodes)) {
      model.document_graph.workspace = String(model.workspace || "");
      model.document_graph.document_basis = String(model.document_basis || (model.change_id ? "candidate" : "live"));
      model.document_graph.change_id = model.change_id || null;
      if (!model.document_graph._enriched) {
        for (const n of model.document_graph.nodes) {
          const m = inferV3SlotMeta(n.path, n.kind);
          n.slot_code = n.slot_code || m.slotCode;
          n.band = n.band || m.band;
          n.band_color = n.band_color || m.bandColor;
          n.band_label = n.band_label || m.bandLabel;
          n.arc42 = n.arc42 || m.arc42;
          n.arc42_order = n.arc42_order || m.arc42Order;
          n.arc42_title_en = n.arc42_title_en || m.arc42TitleEn;
          n.arc42_title_vi = n.arc42_title_vi || m.arc42TitleVi;
          n.display_title = n.display_title || humanizeSlug(n.label || n.id);
          n.summary = n.summary || summarizeArtifactNode(n);
        }
        model.document_graph._enriched = true;
      }
      return model.document_graph;
    }
    const artifacts = Array.isArray(model?.artifacts) ? model.artifacts : [];
    const diffs = model?.diffs || {};
    const nodes = artifacts.map((a, idx) => {
      const parts = String(a.path || a.id || "").split("/").filter(Boolean);
      const folder = parts.length > 1 ? parts.slice(0, -1).join("/") : "root";
      const group = parts.length > 1 ? safeText(parts[0]) : "root";
      const m = inferV3SlotMeta(a.path || a.id, a.kind);
      const label = parts[parts.length - 1] || String(a.id || "");
      const nodeObj = {
        id: String(a.id || a.path || `DOC-${idx}`),
        node_type: "artifact",
        path: String(a.path || a.id || ""),
        label,
        display_title: humanizeSlug(label),
        kind: safeText(a.kind || "document"),
        owner: safeText(a.owner || "architect"),
        revision: String(a.revision || ""),
        folder: safeText(folder),
        group: group,
        band: m.band,
        band_color: m.bandColor,
        band_label: m.bandLabel,
        slot_code: m.slotCode,
        rank: idx % 3,
        clauses: [],
        anchors: [],
        changed: Boolean(diffs[a.path]),
        upstream: [],
        downstream: [],
        upstream_artifacts: [],
        downstream_artifacts: [],
        in_degree: 0,
        out_degree: 0,
      };
      nodeObj.summary = summarizeArtifactNode(nodeObj);
      return nodeObj;
    });
    return {
      workspace: String(model?.workspace || ""),
      document_basis: String(model?.document_basis || (model?.change_id ? "candidate" : "live")),
      change_id: model?.change_id || null,
      nodes,
      clause_nodes: [],
      edges: [],
      artifact_edges: [],
      obligations: [],
      clusters: [],
      stats: {
        artifacts: nodes.length,
        clauses: 0,
        edges: 0,
        artifact_edges: 0,
        obligations: 0,
        changed: nodes.filter((n) => n.changed).length,
        kinds: Array.from(new Set(nodes.map((n) => n.kind))).sort(),
        owners: Array.from(new Set(nodes.map((n) => n.owner))).sort(),
        relations: [],
      },
    };
  }

  // ==========================================================================
  // C4 HIERARCHICAL MODEL BUILDER (C1 -> C2 -> Container Doc Tree — Clean V2.1)
  // ==========================================================================

  function buildDataBackedWorkspaceC4Model(graphData) {
    const docs = graphData.nodes || [];
    const wsTitle = safeText(graphData.workspace || "Workspace System");
    const hasExplicitC4 = docs.some(
      (d) => d.kind === "diagram" || /c1-|c2-|context|container/i.test(String(d.path || ""))
    );

    const groupMap = new Map();
    const extDocs = docs.filter((d) => {
      const p = String(d.path || "");
      return p.includes("/04-external/") || /external/i.test(String(d.kind || ""));
    });
    const extIds = new Set(extDocs.map((d) => d.id));
    const domainDocs = docs.filter((d) => {
      const p = String(d.path || "");
      return (d.band === "02-domains" || p.includes("02-domains/")) && !p.includes("02-domains/00-overview") && !extIds.has(d.id);
    });

    if (domainDocs.length > 0) {
      for (const d of domainDocs) {
        const rawParts = String(d.path || "").split("/").filter(Boolean);
        const domIdx = rawParts.indexOf("02-domains");
        const afterDom = domIdx >= 0 ? rawParts.slice(domIdx + 1) : rawParts;
        let ctxKey = d.bounded_context || "";
        if (!ctxKey) {
          if (afterDom.length >= 2 && !afterDom[0].startsWith("_") && !afterDom[0].startsWith("00-")) {
            ctxKey = afterDom[1].endsWith(".md") ? afterDom[0] : afterDom[1];
          } else if (afterDom.length >= 1) {
            ctxKey = afterDom[0].replace(/\.md$/i, "");
          } else {
            ctxKey = d.domain_family || d.group || "domain";
          }
        }
        if (!groupMap.has(ctxKey)) groupMap.set(ctxKey, []);
        groupMap.get(ctxKey).push(d);
      }
    } else {
      for (const d of docs) {
        const folderParts = String(d.folder || d.group || "root").split("/").filter(Boolean);
        const groupKey =
          d.bounded_context ||
          d.domain_family ||
          (folderParts.length >= 2 ? folderParts.slice(-2).join("/") : folderParts[0] || d.owner || "core");
        if (!groupMap.has(groupKey)) {
          groupMap.set(groupKey, []);
        }
        groupMap.get(groupKey).push(d);
      }
    }

    let entries = Array.from(groupMap.entries());
    if (entries.length === 1 && docs.length >= 6) {
      groupMap.clear();
      for (const d of docs) {
        const subKey = `${d.owner || "architect"} (${d.kind || "spec"})`;
        if (!groupMap.has(subKey)) groupMap.set(subKey, []);
        groupMap.get(subKey).push(d);
      }
      entries = Array.from(groupMap.entries());
    }

    // ISS-28 / WO-R5.3: Preserve distinct Bounded Context containers (up to 32) instead of dumping 300+ docs into topEntries[5]
    const topEntries = entries.slice(0, 32);

    const palette = ["var(--b00)", "var(--b01)", "var(--b02)", "var(--b03)", "var(--b04)", "var(--accent)"];
    const docIdToCtrId = new Map();

    const c2Containers = topEntries.map(([gKey, gDocs], idx) => {
      const ctrId = `ctr.ws-${idx + 1}`;
      for (const gd of gDocs) docIdToCtrId.set(gd.id, ctrId);
      const slotCounts = { M: 0, S: 0, C: 0, D: 0 };
      const clauseSet = new Set();
      for (const gd of gDocs) {
        const sc = gd.slot_code || inferV3SlotMeta(gd.path, gd.kind).slotCode;
        slotCounts[sc] = (slotCounts[sc] || 0) + 1;
        for (const cl of gd.clauses || []) clauseSet.add(cl.id);
      }
      const primaryOwner = gDocs[0]?.owner || "architect";
      const cleanName = humanizeSlug(gKey.split("/").pop() || gKey);
      return {
        id: ctrId,
        shortName: safeText(gKey),
        c4_type: "container",
        node_type: "c4-container",
        title: cleanName,
        display_title: cleanName,
        label: safeText(gKey),
        subtitle: `${primaryOwner}`,
        meta: `${gDocs.length} ${t("owned", "sở hữu")} · ${slotCounts.M || 0}[M] ${slotCounts.S || 0}[S]`,
        owner: primaryOwner,
        kind: "container",
        band_color: palette[idx % palette.length],
        v3FolderPath: gDocs[0]?.folder || "root",
        v3_subtree_docs: gDocs,
        path: gDocs[0]?.path || "",
        whitebox_doc: gDocs[0],
        owned_docs: gDocs,
        slotCounts,
        flowTags: ["all"],
        clauses: Array.from(clauseSet),
        upstream: [],
        downstream: [],
      };
    });

    const rawEdges = [];
    for (const ae of graphData.artifact_edges || []) {
      const fCtr = docIdToCtrId.get(ae.from);
      const tCtr = docIdToCtrId.get(ae.to);
      if (fCtr && tCtr && fCtr !== tCtr) {
        rawEdges.push({
          from: fCtr,
          to: tCtr,
          relations: ae.relations || [ae.primary_relation || "references"],
        });
      }
    }
    const c2Edges = consolidateEdges(rawEdges).map((e) => ({
      ...e,
      label: safeText(e.label).slice(0, 18),
      flowTags: ["all"],
    }));

    const pillarMap = new Map();
    for (const d of docs) {
      const bKey = d.band || d.group || "root";
      if (!pillarMap.has(bKey)) pillarMap.set(bKey, []);
      pillarMap.get(bKey).push(d);
    }
    const c2Pillars = Array.from(pillarMap.entries()).map(([bKey, bDocs], idx) => ({
      id: `pil.${bKey}`,
      shortName: safeText(bKey),
      c4_type: "pillar",
      node_type: "c4-pillar",
      title: `${safeText(bKey)}`,
      display_title: `${safeText(bKey)}`,
      label: safeText(bKey),
      subtitle: `${bDocs.length} ${t("registered specs", "tài liệu")}`,
      meta: `${bDocs.length} ${t("specs", "trang")}`,
      owner: bDocs[0]?.owner || "architect",
      kind: "pillar",
      band_color: palette[idx % palette.length],
      folderPath: bDocs[0]?.folder || "",
      v3FolderPath: bDocs[0]?.folder || "",
      v3_subtree_docs: bDocs,
      path: bDocs[0]?.path || "",
      whitebox_doc: bDocs[0],
      owned_docs: bDocs,
      clauses: [],
    }));

    const sysSlug = wsTitle.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "workspace-core";
    const sysId = `sys.${sysSlug}`;
    const c2Externals = extDocs.slice(0, 16).map((ed, idx) => {
      const extId = `ext.ws-${idx + 1}`;
      docIdToCtrId.set(ed.id, extId);
      const extName = ed.display_title || ed.title || humanizeSlug(String(ed.label || ed.id).replace(/\.md$/i, ""));
      return {
        id: extId,
        shortName: safeText(ed.label || ed.id),
        c4_type: "external",
        node_type: "c4-external",
        title: extName,
        display_title: extName,
        label: safeText(ed.label || ed.id),
        subtitle: t("External Contract", "Hợp đồng Hệ thống Ngoài"),
        meta: `1 ${t("contract spec", "đặc tả tích hợp")}`,
        owner: ed.owner || "01-system-architect",
        kind: "external",
        band_color: "var(--b04)",
        path: ed.path || "",
        whitebox_doc: ed,
        owned_docs: [ed],
        clauses: (ed.clauses || []).map((c) => c.id),
        upstream: [sysId],
        downstream: [],
      };
    });
    for (const ae of graphData.artifact_edges || []) {
      const fCtr = docIdToCtrId.get(ae.from);
      const tCtr = docIdToCtrId.get(ae.to);
      if (fCtr && tCtr && fCtr !== tCtr && (fCtr.startsWith("ext.") || tCtr.startsWith("ext."))) {
        c2Edges.push({
          from: fCtr,
          to: tCtr,
          relation: "external",
          relations: ae.relations || [ae.primary_relation || "references"],
          label: "integration",
          flowTags: ["all"],
        });
      }
    }

    const c1Systems = [
      {
        id: sysId,
        shortName: wsTitle,
        c4_type: "system",
        node_type: "c4-container",
        title: wsTitle,
        display_title: `${wsTitle}`,
        label: wsTitle,
        subtitle: t(
          `Workspace System · ${c2Containers.length} C2 Groups`,
          `Hệ thống Workspace · ${c2Containers.length} Nhóm C2`
        ),
        meta: `${docs.length} ${t("registered specs", "tài liệu đã đăng ký")}`,
        owner: docs[0]?.owner || "01-system-architect",
        kind: "system",
        band_color: "var(--accent)",
        path: docs[0]?.path || "",
        whitebox_doc: docs[0],
        owned_docs: docs,
        clauses: (graphData.clause_nodes || []).map((c) => c.id),
        drillsToC2: true,
        upstream: [],
        downstream: c2Externals.map((ex) => ex.id),
      },
    ];

    const c2Map = new Map([...c1Systems, ...c2Containers, ...c2Externals, ...c2Pillars].map((n) => [n.id, n]));
    for (const e of c2Edges) {
      const f = c2Map.get(e.from);
      const tNode = c2Map.get(e.to);
      if (f && tNode) {
        if (!f.downstream.includes(tNode.id)) f.downstream.push(tNode.id);
        if (!tNode.upstream.includes(f.id)) tNode.upstream.push(f.id);
      }
    }

    return {
      isCompact: false,
      isDataBacked: true,
      hasExplicitC4,
      c4ProvenanceNote: hasExplicitC4
        ? ""
        : t(
            "Derived from registered document folders & ownership — no external C4 containers fabricated.",
            "Được tổng hợp trực tiếp từ thư mục & quyền sở hữu tài liệu thực tế — không tự suy diễn container giả."
          ),
      c1Systems,
      c2Containers,
      c2Externals,
      c2Pillars,
      c2Edges,
      c2Map,
    };
  }

  function buildC4Model(graphData) {
    const docs = graphData.nodes || [];
    const docById = new Map(docs.map((d) => [d.id, d]));
    const wsName = String(graphData.workspace || "").toUpperCase();
    const isOmniPayDemo =
      graphState.datasetMode === "v3-maximal" ||
      wsName.includes("OMNIPAY") ||
      (docs.length >= 10 &&
        docs.some((d) => d.id === "REQ-CORE" || d.id === "DOM-LEDGER-INV") &&
        docs.some((d) => String(d.path || "").includes("payment-orchestration")));

    const cacheKey = `${getLang()}:${graphState.datasetMode}`;
    if (graphData._c4Cache && graphData._c4CacheKey === cacheKey) {
      return graphData._c4Cache;
    }
    if (!isOmniPayDemo && docs.length >= 6) {
      const built = buildDataBackedWorkspaceC4Model(graphData);
      graphData._c4Cache = built;
      graphData._c4CacheKey = cacheKey;
      return built;
    }

    const isRichWorkspace = isOmniPayDemo && docs.length >= 10;

    if (!isRichWorkspace) {
      const c2Containers = docs.map((d) => ({
        id: d.id,
        c4_type: "container",
        node_type: "artifact",
        title: d.display_title || d.label || d.id,
        label: d.label || d.id,
        subtitle: `${d.owner} · ${d.kind}`,
        owner: d.owner,
        kind: d.kind,
        band_color: d.band_color || "var(--b00)",
        path: d.path,
        whitebox_doc: d,
        owned_docs: [d],
        clauses: (d.clauses || []).map((c) => c.id),
        upstream: d.upstream || [],
        downstream: d.downstream || [],
      }));
      return {
        isCompact: true,
        c2Containers,
        c2Externals: [],
        c2Pillars: [],
        c2Edges: consolidateEdges(
          (graphData.artifact_edges || []).map((e) => ({
            from: e.from,
            to: e.to,
            relations: e.relations || [e.primary_relation || "references"],
          }))
        ),
      };
    }

    const matchDocs = (predicate) => docs.filter(predicate);
    const pickWhitebox = (list, preferredId) =>
      (preferredId && docById.get(preferredId)) || list[0] || docs[0];

    const containerDefs = [
      {
        id: "ctr.edge-gateway",
        shortName: "edge-api-gateway",
        title: "Edge API Gateway",
        roleVi: "Envoy · Khóa Idempotency & WAF",
        roleEn: "Envoy · Idempotency & WAF",
        tech: "Envoy + Redis Lease",
        owner: "gateway-architect",
        band_color: "var(--b02)",
        preferredDocId: "GATEWAY",
        flowTags: ["checkout", "timeout-webhook"],
        clauses: ["REQ-022", "REQ-025"],
        filter: (d) =>
          ["GATEWAY", "XCUT-IDEMP", "VIEW-UC01", "DOM-BIZ-CAP"].includes(d.id) ||
          d.path.includes("gateway-architect") ||
          d.path.includes("edge-architect") ||
          d.path.includes("bff-architect") ||
          d.path.includes("idempotency"),
      },
      {
        id: "ctr.payment-orchestrator",
        shortName: "payment-orchestrator",
        title: "Payment Orchestrator",
        roleVi: "Go 1.23 · Điều phối Hexagonal",
        roleEn: "Go 1.23 · Hexagonal Port",
        tech: "Go 1.23 · Timeout <= 30s",
        owner: "api-architect",
        band_color: "var(--b00)",
        preferredDocId: "API",
        flowTags: ["checkout", "timeout-webhook", "fraud-ledger"],
        clauses: ["REQ-021", "REQ-022", "ADR-001"],
        filter: (d) =>
          ["API", "ADR-0001", "DOM-CTX-MAP", "STRAT-SOL", "REQ-CORE", "VIEW-C2", "VIEW-L2-MAP"].includes(d.id) ||
          d.path.includes("api-architect") ||
          d.path.includes("backend-service-architect") ||
          d.path.includes("payment-intents"),
      },
      {
        id: "ctr.fraud-risk-ai",
        shortName: "fraud-risk-inference",
        title: "Fraud Risk AI Engine",
        roleVi: "Rust · Chấm điểm AI <= 25ms",
        roleEn: "Rust · Inline AI <= 25ms",
        tech: "Rust + ONNX Runtime",
        owner: "ai-system-architect",
        band_color: "var(--b03)",
        preferredDocId: "DOM-AI-RISK",
        flowTags: ["fraud-ledger"],
        clauses: ["REQ-024"],
        filter: (d) =>
          ["DOM-AI-RISK", "GOV-RISK"].includes(d.id) ||
          d.path.includes("04_ai_architecture") ||
          d.path.includes("fraud-risk"),
      },
      {
        id: "ctr.zero-trust-iam",
        shortName: "zero-trust-perimeter",
        title: "Zero-Trust IAM & Passkey",
        roleVi: "SPIFFE mTLS 1.3 · FIDO2 Passkey",
        roleEn: "SPIFFE mTLS 1.3 · FIDO2 Passkey",
        tech: "SPIFFE + WebAuthn ES256",
        owner: "zero-trust-architect",
        band_color: "var(--b01)",
        preferredDocId: "DOM-SEC-AUTHN",
        flowTags: ["checkout"],
        clauses: ["REQ-025", "SEC-001"],
        filter: (d) =>
          ["DOM-SEC-AUTHN", "XCUT-SEC-THREAT", "NFR-QAS", "DELIV-AUDIT"].includes(d.id) ||
          d.path.includes("07_security_architecture") ||
          d.path.includes("02-security"),
      },
      {
        id: "ctr.webhook-reconciler",
        shortName: "webhook-reconciler",
        title: "Webhook Reconciler",
        roleVi: "Go · Kafka · Đối soát UNKNOWN",
        roleEn: "Go · Kafka · Resolves UNKNOWN",
        tech: "Go + Kafka + HMAC Guard",
        owner: "agent-workflow-design",
        band_color: "var(--b04)",
        preferredDocId: "FLOW",
        flowTags: ["timeout-webhook"],
        clauses: ["REQ-021", "SEC-001", "REQ-026"],
        filter: (d) =>
          ["FLOW", "XCUT-FIT-001", "DELIV-CANARY", "VIEW-CORR"].includes(d.id) ||
          d.path.includes("workflow-orchestration-architect") ||
          d.path.includes("06-runtime") ||
          d.path.includes("04-fitness-functions"),
      },
      {
        id: "ctr.ledger-settlement",
        shortName: "ledger-settlement-core",
        title: "Ledger Settlement Core",
        roleVi: "Sổ cái Bút toán kép · Outbox CDC",
        roleEn: "Double-Entry Ledger · Outbox CDC",
        tech: "Serializable ACID · RPO=0",
        owner: "aggregate-architect",
        band_color: "var(--b04)",
        preferredDocId: "DOM-LEDGER-INV",
        flowTags: ["timeout-webhook", "fraud-ledger"],
        clauses: ["REQ-023", "ADR-002", "REQ-026"],
        filter: (d) =>
          ["DOM-LEDGER-INV", "DOM-DATA-STORE", "ADR-0002", "DOM-INFRA-MESH"].includes(d.id) ||
          d.path.includes("02_domain_architecture") ||
          d.path.includes("05_data_architecture") ||
          d.path.includes("06_infrastructure_architecture"),
      },
    ];

    const v3AllNodes = getMaximalV3CatalogueModel().document_graph.nodes || [];
    const v3FolderByContainer = {
      "ctr.zero-trust-iam": "documents/architecture/02-domains/07_security_architecture/zero-trust-perimeter",
      "ctr.payment-orchestrator": "documents/architecture/02-domains/03_application_architecture/payment-orchestration",
      "ctr.fraud-risk-ai": "documents/architecture/02-domains/04_ai_architecture/fraud-risk-intelligence",
      "ctr.edge-gateway": "documents/architecture/02-domains/03_application_architecture/payment-orchestration/gateway-architect",
      "ctr.webhook-reconciler": "documents/architecture/00-system-views/06-runtime",
      "ctr.ledger-settlement": "documents/architecture/02-domains/02_domain_architecture/payment-kernel",
    };

    const c2Containers = containerDefs.map((def) => {
      const owned = matchDocs(def.filter);
      const v3FolderPath = v3FolderByContainer[def.id] || "documents/architecture/02-domains";
      const v3SubtreeDocs = v3AllNodes.filter((vn) => vn.path.startsWith(v3FolderPath));
      const wb = pickWhitebox(owned, def.preferredDocId);
      const slotCounts = { M: 0, S: 0, C: 0, D: 0 };
      for (const od of owned) {
        const sc = od.slot_code || inferV3SlotMeta(od.path, od.kind).slotCode;
        slotCounts[sc] = (slotCounts[sc] || 0) + 1;
      }
      return {
        id: def.id,
        shortName: def.shortName,
        c4_type: "container",
        node_type: "c4-container",
        title: def.title,
        display_title: def.title,
        label: def.shortName,
        subtitle: t(def.roleEn || def.tech, def.roleVi || def.tech),
        meta: `${owned.length} ${t("owned", "sở hữu")} · ${slotCounts.M || 0}[M] ${slotCounts.S || 0}[S]`,
        owner: def.owner,
        kind: "container",
        band_color: def.band_color,
        v3FolderPath,
        v3_subtree_docs: v3SubtreeDocs,
        path: wb ? wb.path : "",
        whitebox_doc: wb,
        owned_docs: owned.length ? owned : wb ? [wb] : [],
        slotCounts,
        flowTags: def.flowTags,
        clauses: def.clauses,
        upstream: [],
        downstream: [],
      };
    });

    const c2Externals = [
      {
        id: "ext.redis-cluster",
        shortName: "Redis Idempotency Cluster",
        c4_type: "external",
        node_type: "c4-external",
        title: "Redis Idempotency Lease",
        display_title: "Redis Idempotency Lease Cluster",
        label: "Redis Cluster",
        subtitle: t("Distributed SHA-256 Lock (35s)", "Khóa phân tán SHA-256 (Lease 35s)"),
        meta: t("REQ-022 · 24h lock", "REQ-022 · Khóa 24h"),
        owner: "cache-architect",
        kind: "external",
        band_color: "var(--b02)",
        path: (docById.get("XCUT-IDEMP") || docs[0])?.path || "",
        whitebox_doc: docById.get("XCUT-IDEMP") || docs[0],
        owned_docs: [docById.get("XCUT-IDEMP"), docById.get("GATEWAY")].filter(Boolean),
        flowTags: ["checkout"],
        clauses: ["REQ-022"],
      },
      {
        id: "ext.acquirer-rails",
        shortName: "Visa / Mastercard / NAPAS",
        c4_type: "external",
        node_type: "c4-external",
        title: "Visa / MC / NAPAS Rails",
        display_title: "Visa / Mastercard / NAPAS Rails",
        label: "Visa / MC / NAPAS",
        subtitle: t("External Acquirer · Signed Webhook", "Mạng thẻ/ngân hàng · Signed Webhook"),
        meta: t("REQ-021 · <= 30s SLA", "REQ-021 · SLA <= 30s"),
        owner: "integration-adapter-architect",
        kind: "external",
        band_color: "var(--line)",
        path: (docById.get("ADR-0001") || docs[0])?.path || "",
        whitebox_doc: docById.get("ADR-0001") || docs[0],
        owned_docs: [docById.get("ADR-0001"), docById.get("VIEW-C1")].filter(Boolean),
        flowTags: ["timeout-webhook"],
        clauses: ["REQ-021", "ADR-001", "SEC-001"],
      },
      {
        id: "ext.cockroach-ledger",
        shortName: "CockroachDB Serializable",
        c4_type: "external",
        node_type: "c4-external",
        title: "CockroachDB Ledger Store",
        display_title: "CockroachDB Serializable Ledger Store",
        label: "CockroachDB",
        subtitle: t("Multi-Region Raft · Serializable", "CSDL Sổ cái · RPO=0 Multi-Region"),
        meta: t("REQ-023 · RPO=0 WORM", "REQ-023 · RPO=0 WORM"),
        owner: "database-architect",
        kind: "external",
        band_color: "var(--b01)",
        path: (docById.get("DOM-DATA-STORE") || docs[0])?.path || "",
        whitebox_doc: docById.get("DOM-DATA-STORE") || docs[0],
        owned_docs: [docById.get("DOM-DATA-STORE"), docById.get("DOM-LEDGER-INV")].filter(Boolean),
        flowTags: ["fraud-ledger", "timeout-webhook"],
        clauses: ["REQ-023", "REQ-026", "ADR-002"],
      },
    ];

    const pillarDefs = [
      {
        id: "pil.00-system-views",
        folderPath: "documents/architecture/00-system-views",
        title: "00-system-views",
        subfolders: "00-viewpoints · 01-context · 02-functional · 03-structure · 06-runtime",
        band_color: "var(--b00)",
        preferredDocId: "VIEW-C1",
      },
      {
        id: "pil.01-global-strategy",
        folderPath: "documents/architecture/01-global-strategy",
        title: "01-global-strategy",
        subfolders: "01-requirements · 02-strategy · 04-risks · 05-governance",
        band_color: "var(--b01)",
        preferredDocId: "REQ-CORE",
      },
      {
        id: "pil.02-domains",
        folderPath: "documents/architecture/02-domains",
        title: "02-domains",
        subfolders: "00-overview · 01..10 domain architecture families",
        band_color: "var(--b02)",
        preferredDocId: "DOM-CTX-MAP",
      },
      {
        id: "pil.03-cross-cutting",
        folderPath: "documents/architecture/03-cross-cutting",
        title: "03-cross-cutting",
        subfolders: "01-mechanisms · 02-security · 04-fitness-functions",
        band_color: "var(--b03)",
        preferredDocId: "XCUT-SEC-THREAT",
      },
      {
        id: "pil.04-delivery",
        folderPath: "documents/architecture/04-delivery",
        title: "04-delivery",
        subfolders: "00-planning · 01-quality · 02-release · 03-ops · 04-audit",
        band_color: "var(--b04)",
        preferredDocId: "DELIV-CANARY",
      },
    ];

    const c2Pillars = pillarDefs.map((p) => {
      const pDocs = docs.filter((d) => d.path.startsWith(p.folderPath));
      const v3Docs = v3AllNodes.filter((vn) => vn.path.startsWith(p.folderPath));
      const wb = pickWhitebox(pDocs, p.preferredDocId);
      return {
        id: p.id,
        shortName: p.title,
        c4_type: "pillar",
        node_type: "c4-pillar",
        title: p.title,
        display_title: p.title,
        label: p.title,
        subtitle: p.subfolders,
        meta: `${pDocs.length} ${t("workspace specs", "tài liệu")} · ${v3Docs.length} V3 slots`,
        owner: "01-system-architect",
        kind: "pillar",
        band_color: p.band_color,
        folderPath: p.folderPath,
        v3FolderPath: p.folderPath,
        v3_subtree_docs: v3Docs,
        path: wb ? wb.path : "",
        whitebox_doc: wb,
        owned_docs: pDocs,
        clauses: [],
      };
    });

    // Concise C2 Edges (<= 18 chars by default)
    const c2Edges = [
      {
        from: "ctr.edge-gateway",
        to: "ctr.payment-orchestrator",
        relation: "emphasis",
        relations: ["implements_contract"],
        label: t("POST /v1/intents", "Gọi /v1/intents"),
        flowTags: ["checkout", "timeout-webhook"],
      },
      {
        from: "ctr.payment-orchestrator",
        to: "ctr.fraud-risk-ai",
        relation: "satisfies",
        relations: ["satisfies"],
        label: t("AI Risk <=25ms", "Chấm AI <=25ms"),
        flowTags: ["fraud-ledger"],
      },
      {
        from: "ctr.edge-gateway",
        to: "ctr.zero-trust-iam",
        relation: "implements_contract",
        relations: ["implements_contract"],
        label: t("mTLS + Passkey", "mTLS + Passkey"),
        flowTags: ["checkout"],
      },
      {
        from: "ctr.payment-orchestrator",
        to: "ctr.webhook-reconciler",
        relation: "emphasis",
        relations: ["satisfies"],
        label: t("Timeout -> UNKNOWN", "Timeout -> UNKNOWN"),
        flowTags: ["timeout-webhook"],
      },
      {
        from: "ctr.fraud-risk-ai",
        to: "ctr.ledger-settlement",
        relation: "implements_contract",
        relations: ["implements_contract"],
        label: t("Outbox CDC", "Outbox CDC"),
        flowTags: ["fraud-ledger"],
      },
      {
        from: "ctr.webhook-reconciler",
        to: "ctr.ledger-settlement",
        relation: "satisfies",
        relations: ["satisfies"],
        label: t("HMAC -> CAPTURED", "HMAC -> CAPTURED"),
        flowTags: ["timeout-webhook"],
      },
      {
        from: "ctr.zero-trust-iam",
        to: "ext.redis-cluster",
        relation: "external",
        relations: ["references"],
        label: t("SETNX 35s Lease", "Khóa SETNX 35s"),
        flowTags: ["checkout"],
      },
      {
        from: "ctr.webhook-reconciler",
        to: "ext.acquirer-rails",
        relation: "external",
        relations: ["references"],
        label: t("Signed Webhook", "Signed Webhook"),
        flowTags: ["timeout-webhook"],
      },
      {
        from: "ctr.ledger-settlement",
        to: "ext.cockroach-ledger",
        relation: "external",
        relations: ["implements_contract"],
        label: t("Commit RPO=0", "Ghi sổ RPO=0"),
        flowTags: ["fraud-ledger", "timeout-webhook"],
      },
    ];

    const c1Systems = [
      {
        id: "sys.omnipay-core",
        shortName: "OmniPay Global Checkout V3",
        c4_type: "system",
        node_type: "c4-container",
        title: "OmniPay Global Checkout V3",
        display_title: "OmniPay Global Checkout & AI Risk Cloud",
        label: "sys.omnipay-core",
        subtitle: t(
          "Core Payment & Settlement Cloud · 6 C2 Containers",
          "Hệ thống Thanh toán Trung tâm · 6 Container C2"
        ),
        meta: `${docs.length} ${t("system specs", "tài liệu hệ thống")}`,
        owner: "01-system-architect",
        kind: "system",
        band_color: "var(--accent)",
        path: "documents/architecture/00-system-views/01-context/c1-context.md",
        whitebox_doc: docs.find((d) => d.id === "VIEW-C1") || docs[0],
        owned_docs: docs,
        clauses: ["REQ-021", "REQ-022", "REQ-023", "REQ-024", "REQ-025", "REQ-026", "ADR-001", "ADR-002", "SEC-001"],
        drillsToC2: true,
        upstream: ["act.merchant-shopper", "act.human-reviewer"],
        downstream: ["ext.acquirer-rails-c1", "ext.regulatory-hsm-c1"],
      },
      {
        id: "ext.acquirer-rails-c1",
        shortName: "Visa / Mastercard / NAPAS Rails",
        c4_type: "external-system",
        node_type: "c4-external",
        title: "Global Card & Bank Rails",
        display_title: "Visa / Mastercard / NAPAS Acquirer Rails",
        label: "visa-mastercard-napas",
        subtitle: t("External Payment Network · ISO-8583 & Webhooks", "Mạng thẻ & Ngân hàng ngoài · ISO-8583 & Webhook"),
        meta: `7 ${t("linked specs", "tài liệu liên kết")}`,
        owner: "adr-authoring",
        kind: "external",
        band_color: "var(--b02)",
        path: "documents/architecture/01-global-strategy/05-governance/decisions/0001-hexagonal-payment-port.md",
        whitebox_doc: docs.find((d) => d.id === "ADR-0001") || docs[0],
        owned_docs: docs.filter((d) => ["ADR-0001", "VIEW-C1", "FLOW", "API", "XCUT-SEC-THREAT", "GOV-RISK", "XCUT-FIT-001"].includes(d.id)),
        clauses: ["REQ-021", "ADR-001", "SEC-001"],
        upstream: ["sys.omnipay-core"],
        downstream: [],
      },
      {
        id: "ext.regulatory-hsm-c1",
        shortName: "Central Bank Audit & HSM",
        c4_type: "external-system",
        node_type: "c4-external",
        title: "Central Bank Audit & HSM",
        display_title: "Regulatory WORM Ledger Archive & Cloud HSM",
        label: "regulatory-audit-hsm",
        subtitle: t("Compliance Archive & Key Enclave · PCI-DSS v4.0", "Lưu trữ Kiểm toán & HSM · PCI-DSS v4.0"),
        meta: `7 ${t("linked specs", "tài liệu liên kết")}`,
        owner: "database-architect",
        kind: "external",
        band_color: "var(--b04)",
        path: "documents/architecture/02-domains/05_data_architecture/financial-ledger-store/database-architect/01-journal-pipeline/12-storage/cockroach-journal-storage.md",
        whitebox_doc: docs.find((d) => d.id === "DOM-DATA-STORE") || docs[0],
        owned_docs: docs.filter((d) => ["DOM-DATA-STORE", "DOM-LEDGER-INV", "ADR-0002", "NFR-QAS", "XCUT-SEC-THREAT", "DELIV-AUDIT", "VIEW-C1"].includes(d.id)),
        clauses: ["REQ-023", "REQ-025", "REQ-026", "ADR-002"],
        upstream: ["sys.omnipay-core"],
        downstream: [],
      },
      {
        id: "act.merchant-shopper",
        shortName: "Shopper & Merchant Client",
        c4_type: "actor-system",
        node_type: "c4-container",
        title: "Shopper & Merchant Client",
        display_title: "Shopper & Merchant Checkout Client",
        label: "merchant-checkout-client",
        subtitle: t("Web / iOS / Android Checkout Client", "Ứng dụng Client & Người mua · Web / Mobile"),
        meta: `7 ${t("linked specs", "tài liệu liên kết")}`,
        owner: "00-requirement-clarifier",
        kind: "actor",
        band_color: "var(--b00)",
        path: "documents/architecture/00-system-views/02-functional/use-cases/UC-001-instant-checkout.md",
        whitebox_doc: docs.find((d) => d.id === "VIEW-UC01") || docs[0],
        owned_docs: docs.filter((d) => ["VIEW-UC01", "DOM-BIZ-CAP", "GATEWAY", "XCUT-IDEMP", "API", "REQ-CORE", "VIEW-C1"].includes(d.id)),
        clauses: ["REQ-021", "REQ-022"],
        upstream: [],
        downstream: ["sys.omnipay-core"],
      },
      {
        id: "act.human-reviewer",
        shortName: "Human Architect / Reviewer",
        c4_type: "actor-system",
        node_type: "c4-container",
        title: "Human Architect / Reviewer",
        display_title: "Principal Architect & SecOps Reviewer",
        label: "human-reviewer-passkey",
        subtitle: t("Governance Actor · WebAuthn FIDO2 Passkey", "Người duyệt cổng Human Gate · FIDO2 Passkey"),
        meta: `6 ${t("linked specs", "tài liệu liên kết")}`,
        owner: "zero-trust-architect",
        kind: "actor",
        band_color: "var(--b01)",
        path: "documents/architecture/02-domains/07_security_architecture/zero-trust-perimeter/zero-trust-architect/01-passkey-and-mtls/11-authn/webauthn-passkey-authn.md",
        whitebox_doc: docs.find((d) => d.id === "DOM-SEC-AUTHN") || docs[0],
        owned_docs: docs.filter((d) => ["DOM-SEC-AUTHN", "DELIV-AUDIT", "XCUT-SEC-THREAT", "NFR-QAS", "VIEW-CORR", "DELIV-CANARY"].includes(d.id)),
        clauses: ["REQ-025", "SEC-001"],
        upstream: [],
        downstream: ["sys.omnipay-core"],
      },
    ];

    const c2Map = new Map([...c1Systems, ...c2Containers, ...c2Externals, ...c2Pillars].map((n) => [n.id, n]));
    for (const e of c2Edges) {
      const f = c2Map.get(e.from);
      const tNode = c2Map.get(e.to);
      if (f && tNode) {
        if (!f.downstream) f.downstream = [];
        if (!tNode.upstream) tNode.upstream = [];
        if (!f.downstream.includes(tNode.id)) f.downstream.push(tNode.id);
        if (!tNode.upstream.includes(f.id)) tNode.upstream.push(f.id);
      }
    }

    return {
      isCompact: false,
      c1Systems,
      c2Containers,
      c2Externals,
      c2Pillars,
      c2Edges,
      c2Map,
    };
  }

  function buildSystemDocTreeModel(sysNode, graphData, c4) {
    const allDocs = (graphData && graphData.nodes) || [];
    const docById = new Map(allDocs.map((d) => [d.id, d]));
    if (!sysNode) {
      return {
        primaryDocs: [],
        relatedDocs: [],
        allSystemDocs: [],
        arc42Groups: [],
      };
    }

    if (sysNode.c4_type === "system" || String(sysNode.id || "").startsWith("sys.")) {
      const groupMap = new Map();
      for (const sec of ARC42_SECTIONS) {
        groupMap.set(sec.code, {
          section: sec,
          items: [],
        });
      }
      for (const d of allDocs) {
        const arc = inferArc42Section(d.path, d.kind);
        const g = groupMap.get(arc.code) || groupMap.get("§5");
        const isL2Domain = String(d.path || "").includes("02-domains/") && !String(d.path || "").includes("00-overview") && !String(d.path || "").includes("_shared-");
        g.items.push({
          doc: d,
          roleLabel: d.id === "VIEW-C1" ? "C1 Context" : isL2Domain ? "C2 Domain" : "System Spec",
          isOwned: !isL2Domain,
        });
      }
      const arc42Groups = Array.from(groupMap.values()).filter((g) => g.items.length > 0);
      return {
        primaryDocs: allDocs.filter((d) => !(String(d.path || "").includes("02-domains/") && !String(d.path || "").includes("00-overview"))),
        relatedDocs: allDocs.filter((d) => String(d.path || "").includes("02-domains/") && !String(d.path || "").includes("00-overview")),
        allSystemDocs: allDocs,
        arc42Groups,
      };
    }

    const primaryDocs = sysNode.owned_docs || [];
    const primaryIds = new Set(primaryDocs.map((d) => d.id));
    const relatedMap = new Map();
    const addRel = (docObj, reason) => {
      if (!docObj || primaryIds.has(docObj.id)) return;
      if (!relatedMap.has(docObj.id)) {
        relatedMap.set(docObj.id, { doc: docObj, reasons: [] });
      }
      const entry = relatedMap.get(docObj.id);
      if (reason && !entry.reasons.includes(reason)) entry.reasons.push(reason);
    };

    const sysClauses = new Set(sysNode.clauses || []);
    for (const cl of (graphData && graphData.clause_nodes) || []) {
      if (sysClauses.has(cl.id) || primaryIds.has(cl.artifact_id)) {
        const srcDoc = docById.get(cl.artifact_id);
        if (srcDoc) addRel(srcDoc, `${t("Clause", "Điều khoản")} ${cl.id}`);
        for (const dnId of cl.downstream || []) {
          const dnDoc = docById.get(dnId);
          if (dnDoc) addRel(dnDoc, `${t("Clause", "Cùng")} ${cl.id}`);
        }
      }
    }
    for (const pd of primaryDocs) {
      for (const upId of pd.upstream_artifacts || []) {
        const upDoc = docById.get(upId);
        if (upDoc) addRel(upDoc, `Upstream ← ${pd.id}`);
      }
      for (const dnId of pd.downstream_artifacts || []) {
        const dnDoc = docById.get(dnId);
        if (dnDoc) addRel(dnDoc, `Downstream → ${pd.id}`);
      }
    }

    const relatedDocs = Array.from(relatedMap.values()).map((r) => ({
      doc: r.doc,
      reasons: r.reasons,
      primaryReason: r.reasons.slice(0, 2).join(" · ") || t("Related system spec", "Tài liệu liên quan"),
    }));

    const groupMap = new Map();
    for (const sec of ARC42_SECTIONS) {
      groupMap.set(sec.code, { section: sec, items: [] });
    }
    for (const pd of primaryDocs) {
      const arc = inferArc42Section(pd.path, pd.kind);
      const g = groupMap.get(arc.code) || groupMap.get("§3");
      g.items.push({
        doc: pd,
        roleLabel: pd === sysNode.whitebox_doc ? t("Primary C1 Interface", "Tài liệu C1 Trọng tâm") : t("Direct System Spec", "Tài liệu Trực tiếp"),
        isOwned: true,
      });
    }
    for (const rItem of relatedDocs) {
      const arc = inferArc42Section(rItem.doc.path, rItem.doc.kind);
      const g = groupMap.get(arc.code) || groupMap.get("§5");
      g.items.push({
        doc: rItem.doc,
        roleLabel: rItem.primaryReason,
        isOwned: false,
      });
    }
    const arc42Groups = Array.from(groupMap.values()).filter((g) => g.items.length > 0);
    const allSystemDocs = [...primaryDocs, ...relatedDocs.map((r) => r.doc)];

    return {
      primaryDocs,
      relatedDocs,
      allSystemDocs,
      arc42Groups,
    };
  }

  function renderSystemDocTreeDom(sysNode, graphData, c4, onOpenDoc) {
    const sysModel = buildSystemDocTreeModel(sysNode, graphData, c4);
    const wrap = el("div", "", "aaf-container-doctree-box");

    for (const grp of sysModel.arc42Groups) {
      const secDet = el("details", "", "aaf-doctree-group");
      secDet.open = true;
      const secSum = el("summary", "", "aaf-doctree-group-summary");
      secSum.append(
        el("span", t(grp.section.titleEn, grp.section.titleVi)),
        el("span", `${grp.items.length}`, "doc-graph-kpi mono")
      );
      secDet.append(secSum);

      const ul = el("ul", "", "aaf-doctree-files");
      for (const item of grp.items) {
        const d = item.doc;
        const isCur = graphState.activeLeafPath === d.path;
        const sc = d.slot_code || inferV3SlotMeta(d.path, d.kind).slotCode;
        const li = el("li", "", "aaf-doctree-file-item" + (isCur ? " active-leaf" : ""));
        const badge = el("span", `[${sc}]`, "slot-badge", { "data-slot": sc });
        const btn = el(
          "button",
          `${d.display_title || humanizeSlug(d.label || d.id)}`,
          "aaf-hg1-related-link",
          {
            type: "button",
            title: `${d.path} · ${d.kind} · ${d.owner}`,
          }
        );
        btn.onclick = () => {
          graphState.activeLeafPath = d.path;
          graphState.activeLeafNode = d;
          if (onOpenDoc) onOpenDoc(d.path, d);
        };
        li.append(badge, btn);
        ul.append(li);
      }
      secDet.append(ul);
      wrap.append(secDet);
    }

    return wrap;
  }

  function buildContainerDocTreeModel(ctr, graphData, c4) {
    if (!ctr) {
      return {
        ownedDocs: [],
        folderBranches: [],
        ownedTree: { name: "root", path: "", nodes: [], dirs_list: [], deep: 0 },
        relatedDocs: [],
        relatedArc42Groups: [],
      };
    }
    const allDocs = (graphData && graphData.nodes) || [];
    const docById = new Map(allDocs.map((d) => [d.id, d]));
    const ownedDocs =
      graphState.datasetMode === "v3-maximal" && (ctr.v3_subtree_docs || []).length
        ? ctr.v3_subtree_docs.slice(0, 18)
        : ctr.owned_docs || [];
    const ownedIds = new Set(ownedDocs.map((d) => d.id));
    const ownedPaths = new Set(ownedDocs.map((d) => d.path));

    const branchMap = new Map();
    for (const od of ownedDocs) {
      const clean = String(od.path || "")
        .replace(/^documents\/architecture\//, "")
        .replace(/^\/+/, "");
      const segs = clean.split("/").filter(Boolean);
      const dirSegs = segs.length > 1 ? segs.slice(0, -1) : ["root"];
      const branchKey =
        dirSegs.length >= 2
          ? `${dirSegs[0]}/${dirSegs[1]}`
          : dirSegs[0] || "root";
      const fullFolderPath = String(od.path || "").split("/").slice(0, -1).join("/") || "root";
      if (!branchMap.has(branchKey)) {
        const shortLabel = safeText(branchKey.replace(/\//g, " / "));
        branchMap.set(branchKey, {
          id: `BRANCH:${ctr.id}:${branchKey}`,
          branchKey,
          shortTitle: shortLabel,
          fullBranchLabel: safeText(branchKey.replace(/\//g, " / ")),
          folderPath: fullFolderPath,
          docs: [],
          slotCounts: { M: 0, S: 0, C: 0, D: 0 },
        });
      }
      const b = branchMap.get(branchKey);
      b.docs.push(od);
      const sc = od.slot_code || inferV3SlotMeta(od.path, od.kind).slotCode;
      b.slotCounts[sc] = (b.slotCounts[sc] || 0) + 1;
    }

    const folderBranches = Array.from(branchMap.values());
    const ownedTree = buildFolderTreeFromNodes(ownedDocs);

    const relatedMap = new Map();
    const addRelated = (docObj, reason) => {
      if (!docObj || ownedIds.has(docObj.id) || ownedPaths.has(docObj.path)) return;
      if (!relatedMap.has(docObj.id)) {
        relatedMap.set(docObj.id, { doc: docObj, reasons: [] });
      }
      const entry = relatedMap.get(docObj.id);
      if (reason && !entry.reasons.includes(reason)) {
        entry.reasons.push(reason);
      }
    };

    const ctrClauses = new Set(ctr.clauses || []);
    for (const cl of (graphData && graphData.clause_nodes) || []) {
      if (ctrClauses.has(cl.id) || ownedIds.has(cl.artifact_id)) {
        const srcDoc = docById.get(cl.artifact_id);
        if (srcDoc) addRelated(srcDoc, `${t("Clause", "Điều khoản")} ${cl.id}`);
        for (const dnId of cl.downstream || []) {
          const dnDoc = docById.get(dnId);
          if (dnDoc) addRelated(dnDoc, `${t("Clause", "Cùng")} ${cl.id}`);
        }
      }
    }

    for (const od of ownedDocs) {
      for (const upId of od.upstream_artifacts || []) {
        const upDoc = docById.get(upId);
        if (upDoc) addRelated(upDoc, `Upstream ← ${od.id}`);
      }
      for (const dnId of od.downstream_artifacts || []) {
        const dnDoc = docById.get(dnId);
        if (dnDoc) addRelated(dnDoc, `Downstream → ${pd_id_safe(od.id)}`);
      }
    }

    function pd_id_safe(v) {
      return String(v || "");
    }

    if (c4 && Array.isArray(c4.c2Edges)) {
      for (const edge of c4.c2Edges) {
        if (edge.from === ctr.id) {
          const targetCtr = c4.c2Map && c4.c2Map.get(edge.to);
          if (targetCtr && targetCtr.whitebox_doc) {
            addRelated(targetCtr.whitebox_doc, `${t("C2 Call:", "Gọi C2:")} ${safeText(edge.label)}`);
          }
        } else if (edge.to === ctr.id) {
          const sourceCtr = c4.c2Map && c4.c2Map.get(edge.from);
          if (sourceCtr && sourceCtr.whitebox_doc) {
            addRelated(sourceCtr.whitebox_doc, `${t("C2 Caller:", "Nhận từ C2:")} ${safeText(edge.label)}`);
          }
        }
      }
    }

    const relatedDocs = Array.from(relatedMap.values()).map((r) => {
      const arc = inferArc42Section(r.doc.path, r.doc.kind);
      return {
        doc: r.doc,
        arc42: arc,
        reasons: r.reasons,
        primaryReason: r.reasons.slice(0, 2).join(" · ") || t("Related specification", "Tài liệu liên quan"),
      };
    });

    const relGroupMap = new Map();
    for (const sec of ARC42_SECTIONS) {
      relGroupMap.set(sec.code, { section: sec, items: [] });
    }
    for (const rItem of relatedDocs) {
      const g = relGroupMap.get(rItem.arc42.code) || relGroupMap.get("§5");
      g.items.push(rItem);
    }
    const relatedArc42Groups = Array.from(relGroupMap.values()).filter((g) => g.items.length > 0);

    return {
      ownedDocs,
      folderBranches,
      ownedTree,
      relatedDocs,
      relatedArc42Groups,
    };
  }

  function renderContainerDocTreeDom(ctr, graphData, c4, onOpenDoc, options) {
    const opts = options || {};
    const treeModel = buildContainerDocTreeModel(ctr, graphData, c4);
    const wrap = el("div", "", "aaf-container-doctree-box");

    // 1. Owned Specs · arc42 §5 (Clean 2-element items: [Slot] + Clean Title)
    const ownedSection = el("details", "", "aaf-doctree-group");
    ownedSection.open = true;
    const ownedSum = el("summary", "", "aaf-doctree-group-summary");
    ownedSum.append(
      el(
        "span",
        t(
          `Owned Specs · arc42 §5 (${treeModel.ownedDocs.length})`,
          `Tài liệu sở hữu · arc42 §5 (${treeModel.ownedDocs.length})`
        )
      )
    );
    ownedSection.append(ownedSum);

    const branchList = el("div", "", "aaf-doctree-branch-list");
    for (const branch of treeModel.folderBranches) {
      const bDet = el("details", "", "aaf-doctree-branch");
      bDet.open = true;
      const bSum = el("summary", "", "aaf-doctree-branch-summary");
      bSum.append(
        el("span", `${branch.fullBranchLabel}`, "mono"),
        el("span", `${branch.docs.length}`, "doc-graph-kpi mono")
      );
      bDet.append(bSum);

      const ul = el("ul", "", "aaf-doctree-files");
      const visibleBranchDocs = branch.docs.slice(0, 40);
      for (const od of visibleBranchDocs) {
        const isCur = graphState.activeLeafPath === od.path;
        const sc = od.slot_code || inferV3SlotMeta(od.path, od.kind).slotCode;
        const li = el("li", "", "aaf-doctree-file-item" + (isCur ? " active-leaf" : ""));
        const badge = el("span", `[${sc}]`, "slot-badge", { "data-slot": sc });
        const btn = el(
          "button",
          `${od.display_title || humanizeSlug(od.label || od.id)}`,
          "aaf-hg1-related-link",
          {
            type: "button",
            title: `${od.path} · ${od.kind} · ${od.owner}`,
          }
        );
        btn.onclick = () => {
          graphState.activeLeafPath = od.path;
          graphState.activeLeafNode = od;
          if (onOpenDoc) onOpenDoc(od.path, od);
        };
        li.append(badge, btn);
        ul.append(li);
      }
      if (branch.docs.length > 40) {
        const moreLi = el("li", "", "aaf-doctree-file-item");
        const moreBtn = el(
          "button",
          t(`Show all (+${branch.docs.length - 40})`, `Hiện tất cả (+${branch.docs.length - 40})`),
          "aaf-tree-chip-btn",
          { type: "button" }
        );
        moreBtn.onclick = () => {
          moreLi.remove();
          for (const od of branch.docs.slice(40)) {
            const sc = od.slot_code || inferV3SlotMeta(od.path, od.kind).slotCode;
            const li = el("li", "", "aaf-doctree-file-item");
            const badge = el("span", `[${sc}]`, "slot-badge", { "data-slot": sc });
            const btn = el("button", `${od.display_title || humanizeSlug(od.label || od.id)}`, "aaf-hg1-related-link", {
              type: "button",
              title: `${od.path} · ${od.kind} · ${od.owner}`,
            });
            btn.onclick = () => {
              graphState.activeLeafPath = od.path;
              graphState.activeLeafNode = od;
              if (onOpenDoc) onOpenDoc(od.path, od);
            };
            li.append(badge, btn);
            ul.append(li);
          }
        };
        moreLi.append(moreBtn);
        ul.append(moreLi);
      }
      bDet.append(ul);
      branchList.append(bDet);
    }
    ownedSection.append(branchList);
    wrap.append(ownedSection);

    // 2. Referenced Specs · arc42 §1..§11 (Clean 2-element items: [Slot] + Clean Title)
    if (treeModel.relatedDocs.length > 0) {
      const relSection = el("details", "", "aaf-doctree-group aaf-doctree-related");
      relSection.open = !opts.collapseRelated;
      const relSum = el("summary", "", "aaf-doctree-group-summary");
      relSum.append(
        el(
          "span",
          t(
            `Referenced Specs · arc42 §1..§11 (${treeModel.relatedDocs.length})`,
            `Tài liệu tham chiếu · arc42 §1..§11 (${treeModel.relatedDocs.length})`
          )
        )
      );
      relSection.append(relSum);

      const relBranchesWrap = el("div", "", "aaf-doctree-branch-list");
      for (const grp of treeModel.relatedArc42Groups) {
        const gDet = el("details", "", "aaf-doctree-branch");
        gDet.open = true;
        const gSum = el("summary", "", "aaf-doctree-branch-summary");
        gSum.append(
          el("span", t(grp.section.titleEn, grp.section.titleVi)),
          el("span", `${grp.items.length}`, "doc-graph-kpi mono")
        );
        gDet.append(gSum);

        const relUl = el("ul", "", "aaf-doctree-files");
        for (const rItem of grp.items) {
          const rDoc = rItem.doc;
          const isCur = graphState.activeLeafPath === rDoc.path;
          const sc = rDoc.slot_code || inferV3SlotMeta(rDoc.path, rDoc.kind).slotCode;
          const li = el("li", "", "aaf-doctree-file-item" + (isCur ? " active-leaf" : ""));
          const badge = el("span", `[${sc}]`, "slot-badge", { "data-slot": sc });
          const btn = el(
            "button",
            `${rDoc.display_title || humanizeSlug(rDoc.label || rDoc.id)}`,
            "aaf-hg1-related-link",
            {
              type: "button",
              title: `${rDoc.path} · ${rItem.primaryReason} · ${rDoc.owner}`,
            }
          );
          btn.onclick = () => {
            graphState.activeLeafPath = rDoc.path;
            graphState.activeLeafNode = rDoc;
            if (onOpenDoc) onOpenDoc(rDoc.path, rDoc);
          };
          li.append(badge, btn);
          relUl.append(li);
        }
        gDet.append(relUl);
        relBranchesWrap.append(gDet);
      }
      relSection.append(relBranchesWrap);
      wrap.append(relSection);
    }

    return wrap;
  }

  function computeC4Layout(graphData) {
    const c4 = buildC4Model(graphData);
    const NODE_W = 248;
    const NODE_H = 88;
    const positions = new Map();
    const nodeLayerIndex = new Map();
    const clusterBoxes = [];
    const customNodesMap = new Map();
    const outlineItems = [];
    const treeSpinePaths = [];

    if (c4.isCompact) {
      return computeGraphLayout(
        graphData,
        "doc-dag",
        graphState.showClauses,
        graphState.ownerFilter,
        graphState.slotFilter
      );
    }

    if (graphState.c4Level !== "C1" && graphState.c4Level !== "C2" && graphState.c4Level !== "CONTAINER_DOCS") {
      graphState.c4Level = "CONTAINER_DOCS";
    }

    // ------------------------------------------------------------------------
    // LEVEL 1: C1 SYSTEM CONTEXT (Clean 3-line nodes, pure EN/VI cluster labels)
    // ------------------------------------------------------------------------
    if (graphState.c4Level === "C1") {
      const canvasW = 880;
      const C1_H = 88;
      const c1Nodes = (c4.c1Systems || []).map((sysItem) => {
        const sysTree = buildSystemDocTreeModel(sysItem, graphData, c4);
        return {
          ...sysItem,
          meta: `${sysTree.allSystemDocs.length} ${t("linked specs", "tài liệu liên kết")} · ${sysTree.arc42Groups.length} arc42`,
        };
      });

      for (const n of c1Nodes) customNodesMap.set(n.id, n);

      clusterBoxes.push(
        {
          id: "c1-actors",
          label: t("EXTERNAL ACTORS", "TÁC NHÂN NGOÀI"),
          x: 110,
          y: 20,
          width: 660,
          height: 136,
          count: 2,
        },
        {
          id: "c1-system",
          label: t("SYSTEM BOUNDARY", "RANH GIỚI HỆ THỐNG"),
          x: 240,
          y: 196,
          width: 400,
          height: 136,
          count: 1,
        },
        {
          id: "c1-externals",
          label: t("EXTERNAL SYSTEMS", "HỆ THỐNG ĐỐI TÁC"),
          x: 110,
          y: 372,
          width: 660,
          height: 136,
          count: 2,
        }
      );

      if (c4.isDataBacked) {
        c1Nodes.forEach((n, idx) => {
          positions.set(n.id, { x: 316, y: 100 + idx * 124, w: NODE_W, h: C1_H });
          nodeLayerIndex.set(n.id, idx);
        });
        return {
          positions,
          nodeLayerIndex,
          clusterBoxes: [{
            id: "c1-system",
            label: t("SYSTEM BOUNDARY", "RANH GIỚI HỆ THỐNG"),
            x: 200,
            y: 56,
            width: 480,
            height: 164,
            count: c1Nodes.length,
          }],
          width: canvasW,
          height: 260,
          NODE_W,
          NODE_H: C1_H,
          customNodesMap,
          customEdges: [],
          tableEdges: [],
          outlineItems,
          treeSpinePaths,
        };
      }
      positions.set("act.merchant-shopper", { x: 150, y: 52, w: NODE_W, h: C1_H });
      positions.set("act.human-reviewer", { x: 480, y: 52, w: NODE_W, h: C1_H });
      positions.set("sys.omnipay-core", { x: 316, y: 228, w: NODE_W, h: C1_H });
      positions.set("ext.acquirer-rails-c1", { x: 150, y: 404, w: NODE_W, h: C1_H });
      positions.set("ext.regulatory-hsm-c1", { x: 480, y: 404, w: NODE_W, h: C1_H });

      nodeLayerIndex.set("act.merchant-shopper", 0);
      nodeLayerIndex.set("act.human-reviewer", 0);
      nodeLayerIndex.set("sys.omnipay-core", 1);
      nodeLayerIndex.set("ext.acquirer-rails-c1", 2);
      nodeLayerIndex.set("ext.regulatory-hsm-c1", 2);

      const c1Edges = [
        {
          from: "act.merchant-shopper",
          to: "sys.omnipay-core",
          relation: "emphasis",
          relations: ["satisfies"],
          label: t("TLS 1.3 + Idemp.", "TLS 1.3 + Idemp."),
        },
        {
          from: "act.human-reviewer",
          to: "sys.omnipay-core",
          relation: "implements_contract",
          relations: ["implements_contract"],
          label: t("FIDO2 Passkey", "FIDO2 Passkey"),
        },
        {
          from: "sys.omnipay-core",
          to: "ext.acquirer-rails-c1",
          relation: "external",
          relations: ["references"],
          label: t("ISO-8583 / Webhook", "ISO-8583 / Webhook"),
        },
        {
          from: "sys.omnipay-core",
          to: "ext.regulatory-hsm-c1",
          relation: "external",
          relations: ["implements_contract"],
          label: t("WORM Ledger RPO=0", "Sổ cái WORM RPO=0"),
        },
      ];

      return {
        positions,
        nodeLayerIndex,
        clusterBoxes,
        width: canvasW,
        height: 530,
        NODE_W,
        NODE_H: C1_H,
        customNodesMap,
        customEdges: c1Edges,
        tableEdges: c1Edges,
        outlineItems,
        treeSpinePaths,
      };
    }

    // ------------------------------------------------------------------------
    // LEVEL 3: CONTAINER DOCUMENT TREE GRAPH (Clean labels, <= 3 <text> per node)
    // ------------------------------------------------------------------------
    if (graphState.c4Level === "CONTAINER_DOCS") {
      const parentCtr =
        c4.c2Map.get(graphState.c4FocusedContainer) || c4.c2Containers[1] || c4.c2Containers[0];
      const docTree = buildContainerDocTreeModel(parentCtr, graphData, c4);
      const canvasW = 880;
      const docs = graphData.nodes || [];
      const tableEdges = [];

      const topY = 16;
      const topH = 132;
      clusterBoxes.push({
        id: "doctree-c1-c2-header",
        label: t("CONTAINER CONTEXT", "NGỮ CẢNH CONTAINER"),
        x: 14,
        y: topY,
        width: 852,
        height: topH,
        count: 2,
      });

      const primarySysId = (c4.c1Systems && c4.c1Systems[0] && c4.c1Systems[0].id) || "sys.omnipay-core";
      const c1SysNode = {
        id: primarySysId,
        node_type: "c4-container",
        title: `C1: ${safeText(graphData.workspace || "OmniPay Checkout V3")}`,
        display_title: `C1: ${safeText(graphData.workspace || "OmniPay Global Checkout V3")}`,
        label: primarySysId,
        subtitle: t("C1 Software System · 6 C2 Containers", "Hệ thống C1 · 6 Container C2"),
        meta: `${docs.length} ${t("system specs", "tài liệu hệ thống")}`,
        owner: "01-system-architect",
        kind: "system",
        band_color: "var(--b01)",
        path: "documents/architecture/00-system-views/01-context/c1-context.md",
        whitebox_doc: docs.find((d) => d.id === "VIEW-C1") || docs[0],
        owned_docs: docs,
        drillsToC2: true,
      };
      const c2RootNode = {
        ...parentCtr,
        id: parentCtr.id,
        node_type: "c4-container",
        title: `C2: ${parentCtr.title}`,
        subtitle: `${parentCtr.subtitle} (${parentCtr.owner})`,
        meta: `${docTree.ownedDocs.length} ${t("owned", "sở hữu")} · ${docTree.relatedDocs.length} ${t("linked", "liên kết")}`,
      };

      customNodesMap.set(c1SysNode.id, c1SysNode);
      customNodesMap.set(c2RootNode.id, c2RootNode);
      positions.set(c1SysNode.id, { x: 34, y: topY + 32, w: 336, h: 84 });
      positions.set(c2RootNode.id, { x: 462, y: topY + 32, w: 384, h: 84 });
      nodeLayerIndex.set(c1SysNode.id, 0);
      nodeLayerIndex.set(c2RootNode.id, 0);

      const hY = topY + 32 + 42;
      treeSpinePaths.push({
        d: `M 370 ${hY} L 462 ${hY}`,
        color: "var(--accent)",
        arrow: "url(#aaf-arrow-active)",
        label: "C1 -> C2",
        lx: 416,
        ly: hY - 12,
      });
      tableEdges.push({
        from: c1SysNode.id,
        to: c2RootNode.id,
        label: "C1 System -> C2 Container",
        flowTags: ["c1-c2"],
      });

      const treeZoneY = topY + topH + 24;
      const branches = docTree.folderBranches || [];
      const relList = (docTree.relatedDocs || []).slice(0, 9);

      const BRANCH_H = 54;
      const DOC_H = 76;
      const GAP_Y = 12;

      let leftCurY = treeZoneY + 38;
      const leftTrunkX = 30;
      const branchBoxX = 48;
      const branchBoxW = 372;
      const ownedTrunkX = 66;
      const ownedBoxX = 86;
      const ownedBoxW = 334;
      const branchMidYs = [];

      for (const b of branches) {
        const bMidY = leftCurY + Math.round(BRANCH_H / 2);
        branchMidYs.push(bMidY);
        const bNode = {
          id: b.id,
          node_type: "folder",
          path: b.folderPath,
          label: b.shortTitle,
          display_title: `${b.shortTitle}`,
          kind: "container-branch",
          owner: parentCtr.shortName,
          band_color: parentCtr.band_color,
          deep: b.docs.length,
          slotCounts: b.slotCounts,
          subPreview: b.fullBranchLabel,
          whitebox_doc: b.docs[0],
        };
        customNodesMap.set(b.id, bNode);
        positions.set(b.id, { x: branchBoxX, y: leftCurY, w: branchBoxW, h: BRANCH_H });
        nodeLayerIndex.set(b.id, 1);
        tableEdges.push({
          from: c2RootNode.id,
          to: b.id,
          label: t(`Folder branch (${b.docs.length})`, `Nhánh thư mục (${b.docs.length})`),
          flowTags: ["owned-tree"],
        });

        const branchBottomY = leftCurY + BRANCH_H;
        leftCurY += BRANCH_H + 10;

        const docMidYs = [];
        for (const od of b.docs) {
          const dMidY = leftCurY + Math.round(DOC_H / 2);
          docMidYs.push(dMidY);
          const isCurrent = graphState.activeLeafPath === od.path;
          const odCopy = {
            ...od,
            node_type: "artifact",
            is_active_leaf: isCurrent,
            display_title: `${od.display_title || humanizeSlug(od.label || od.id)}`,
          };
          customNodesMap.set(od.id, odCopy);
          positions.set(od.id, { x: ownedBoxX, y: leftCurY, w: ownedBoxW, h: DOC_H });
          nodeLayerIndex.set(od.id, 2);
          tableEdges.push({
            from: b.id,
            to: od.id,
            label: `[${od.slot_code || "M"}] ${t("Owned spec", "Tài liệu sở hữu")}`,
            flowTags: [od.slot_code || "M"],
          });
          leftCurY += DOC_H + GAP_Y;
        }

        if (docMidYs.length > 0) {
          const lastDocY = docMidYs[docMidYs.length - 1];
          treeSpinePaths.push({
            d: `M ${ownedTrunkX} ${branchBottomY} L ${ownedTrunkX} ${lastDocY}`,
            color: "var(--accent)",
          });
          for (const dY of docMidYs) {
            treeSpinePaths.push({
              d: `M ${ownedTrunkX} ${dY} L ${ownedBoxX} ${dY}`,
              color: "var(--accent)",
              arrow: "url(#aaf-arrow-active)",
            });
          }
        }
        leftCurY += 6;
      }

      if (branchMidYs.length > 0) {
        const lastBranchY = branchMidYs[branchMidYs.length - 1];
        treeSpinePaths.push({
          d: `M ${leftTrunkX} ${treeZoneY + 24} L ${leftTrunkX} ${lastBranchY}`,
          color: "var(--accent)",
        });
        for (const bY of branchMidYs) {
          treeSpinePaths.push({
            d: `M ${leftTrunkX} ${bY} L ${branchBoxX} ${bY}`,
            color: "var(--accent)",
            arrow: "url(#aaf-arrow-active)",
          });
        }
      }

      let rightCurY = treeZoneY + 38;
      const rightTrunkX = 462;
      const relBoxX = 484;
      const relBoxW = 368;
      const relMidYs = [];

      for (const rItem of relList) {
        const rDoc = rItem.doc;
        const rMidY = rightCurY + Math.round(DOC_H / 2);
        relMidYs.push(rMidY);
        const isCurrent = graphState.activeLeafPath === rDoc.path;
        const relCopy = {
          ...rDoc,
          node_type: "artifact",
          is_active_leaf: isCurrent,
          is_sibling_peer: !isCurrent,
          display_title: `${rDoc.display_title || humanizeSlug(rDoc.label || rDoc.id)}`,
          summary: `${rItem.primaryReason} · ${summarizeArtifactNode(rDoc)}`,
        };
        customNodesMap.set(rDoc.id, relCopy);
        positions.set(rDoc.id, { x: relBoxX, y: rightCurY, w: relBoxW, h: DOC_H });
        nodeLayerIndex.set(rDoc.id, 2);
        tableEdges.push({
          from: c2RootNode.id,
          to: rDoc.id,
          label: rItem.primaryReason,
          flowTags: ["related-doc"],
        });
        rightCurY += DOC_H + GAP_Y;
      }

      if (relMidYs.length > 0) {
        const lastRelY = relMidYs[relMidYs.length - 1];
        treeSpinePaths.push({
          d: `M ${rightTrunkX} ${treeZoneY + 24} L ${rightTrunkX} ${lastRelY}`,
          color: "var(--b02)",
        });
        for (const rY of relMidYs) {
          treeSpinePaths.push({
            d: `M ${rightTrunkX} ${rY} L ${relBoxX} ${rY}`,
            color: "var(--b02)",
            arrow: "url(#aaf-arrow-ok)",
          });
        }
      }

      const c2BotX = 462 + 192;
      const c2BotY = topY + 32 + 84;
      const splitBarY = treeZoneY - 10;
      treeSpinePaths.push({
        d: `M ${c2BotX} ${c2BotY} L ${c2BotX} ${splitBarY} L ${leftTrunkX} ${splitBarY} L ${leftTrunkX} ${treeZoneY + 24}`,
        color: "var(--accent)",
      });
      treeSpinePaths.push({
        d: `M ${c2BotX} ${splitBarY} L ${rightTrunkX} ${splitBarY} L ${rightTrunkX} ${treeZoneY + 24}`,
        color: "var(--b02)",
      });

      const leftBoxH = Math.max(160, leftCurY - treeZoneY + 12);
      const rightBoxH = Math.max(160, rightCurY - treeZoneY + 12);
      const maxZoneH = Math.max(leftBoxH, rightBoxH);

      clusterBoxes.push(
        {
          id: "doctree-left-owned",
          label: t(
            `OWNED SPECS (${docTree.ownedDocs.length})`,
            `TÀI LIỆU SỞ HỮU (${docTree.ownedDocs.length})`
          ),
          x: 14,
          y: treeZoneY,
          width: 420,
          height: maxZoneH,
          count: docTree.ownedDocs.length,
        },
        {
          id: "doctree-right-related",
          label: t(
            `LINKED SPECS (${relList.length})`,
            `TÀI LIỆU LIÊN KẾT (${relList.length})`
          ),
          x: 446,
          y: treeZoneY,
          width: 420,
          height: maxZoneH,
          count: relList.length,
        }
      );

      return {
        positions,
        nodeLayerIndex,
        clusterBoxes,
        width: canvasW,
        height: treeZoneY + maxZoneH + 20,
        NODE_W: 360,
        NODE_H: DOC_H,
        customNodesMap,
        customEdges: [],
        tableEdges,
        outlineItems,
        treeSpinePaths,
      };
    }

    // ------------------------------------------------------------------------
    // LEVEL 2 (DEFAULT): C2 CONTAINERS (Clean 248x88px nodes, max 3 <text> lines)
    // ------------------------------------------------------------------------
    const canvasW = 880;
    const colGap = 32;
    const contentW3 = 3 * NODE_W + 2 * colGap; // 808px
    const boxW = contentW3 + 44; // 852px
    const boxX = Math.round((canvasW - boxW) / 2); // 14px
    const startX = Math.round(boxX + (boxW - contentW3) / 2); // 36px
    const rowGapC2 = 58;

    const z1Y = 18;
    const z1H = 2 * NODE_H + rowGapC2 + 52;
    clusterBoxes.push({
      id: "zone-internal",
      label: t("SYSTEM BOUNDARY · C2", "RANH GIỚI HỆ THỐNG · C2"),
      x: boxX,
      y: z1Y,
      width: boxW,
      height: z1H,
      count: c4.c2Containers.length,
    });

    c4.c2Containers.forEach((ctr, idx) => {
      const col = idx % 3;
      const row = Math.floor(idx / 3);
      const treeInfo = buildContainerDocTreeModel(ctr, graphData, c4);
      ctr.meta = `${treeInfo.ownedDocs.length} ${t("owned", "sở hữu")} · ${treeInfo.relatedDocs.length} ${t("linked", "liên kết")}`;
      nodeLayerIndex.set(ctr.id, row);
      positions.set(ctr.id, {
        x: startX + col * (NODE_W + colGap),
        y: z1Y + 34 + row * (NODE_H + rowGapC2),
        w: NODE_W,
        h: NODE_H,
      });
      customNodesMap.set(ctr.id, ctr);
    });

    const EXT_H = 88;
    const z2Y = z1Y + z1H + 34;
    const z2H = c4.c2Externals.length ? EXT_H + 50 : 0;
    if (c4.c2Externals.length) {
      clusterBoxes.push({
        id: "zone-external",
        label: t("EXTERNAL SYSTEMS", "HỆ THỐNG NGOÀI"),
        x: boxX,
        y: z2Y,
        width: boxW,
        height: z2H,
        count: c4.c2Externals.length,
      });
    }

    c4.c2Externals.forEach((ext, idx) => {
      nodeLayerIndex.set(ext.id, 2);
      positions.set(ext.id, {
        x: startX + idx * (NODE_W + colGap),
        y: z2Y + 34,
        w: NODE_W,
        h: EXT_H,
      });
      customNodesMap.set(ext.id, ext);
    });

    const filteredEdges = c4.c2Edges
      .filter((e) => {
        if (graphState.c4GuidedFlow === "all") return true;
        return (e.flowTags || []).includes(graphState.c4GuidedFlow);
      })
      .map((e, idx) => ({
        ...e,
        label:
          graphState.c4GuidedFlow === "all"
            ? safeText(e.label).slice(0, 18)
            : `${idx + 1}. ${safeText(e.label)}`.slice(0, 18),
      }));

    return {
      positions,
      nodeLayerIndex,
      clusterBoxes,
      width: canvasW,
      height: z2Y + z2H + 20,
      NODE_W,
      NODE_H,
      customNodesMap,
      customEdges: filteredEdges,
      tableEdges: c4.c2Edges,
      outlineItems,
      treeSpinePaths,
    };
  }
  function appendInlineMarkdown(parent, rawText) {
    const cleaned = safeText(rawText);
    const tokenRegex = /(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g;
    let lastIndex = 0;
    let match;
    while ((match = tokenRegex.exec(cleaned)) !== null) {
      if (match.index > lastIndex) {
        parent.append(document.createTextNode(cleaned.slice(lastIndex, match.index)));
      }
      const token = match[0];
      if (token.startsWith("**") && token.endsWith("**")) {
        parent.append(el("strong", token.slice(2, -2)));
      } else if (token.startsWith("`") && token.endsWith("`")) {
        parent.append(el("code", token.slice(1, -1)));
      } else if (token.startsWith("[")) {
        const m = token.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
        if (m) {
          const span = el("span", `${m[1]} (${m[2]})`, "mono");
          span.style.color = "var(--accent)";
          parent.append(span);
        } else {
          parent.append(document.createTextNode(token));
        }
      }
      lastIndex = tokenRegex.lastIndex;
    }
    if (lastIndex < cleaned.length) {
      parent.append(document.createTextNode(cleaned.slice(lastIndex)));
    }
  }

  function renderMarkdownToDom(markdownText) {
    const container = el("div", "", "aaf-reader-rendered");
    container.setAttribute("aria-label", t("Formatted document preview", "Bản xem tài liệu đã định dạng"));
    const raw = String(markdownText || "").replace(/\r\n/g, "\n");
    let body = raw;
    // Strip YAML frontmatter so metadata is never repeated inside the rendered specification body 
    const fmMatch = raw.match(/^---\n([\s\S]*?)\n---\n/);
    if (fmMatch) {
      body = raw.slice(fmMatch[0].length);
    }

    const lines = body.split("\n");
    let i = 0;
    while (i < lines.length) {
      const line = lines[i];
      if (!line.trim()) {
        i += 1;
        continue;
      }
      if (line.trim().startsWith("```")) {
        const codeLines = [];
        i += 1;
        while (i < lines.length && !lines[i].trim().startsWith("```")) {
          codeLines.push(lines[i]);
          i += 1;
        }
        i += 1;
        container.append(el("pre", codeLines.join("\n")));
        continue;
      }
      if (line.trim().startsWith("|") && line.trim().endsWith("|")) {
        const tableLines = [];
        while (i < lines.length && lines[i].trim().startsWith("|") && lines[i].trim().endsWith("|")) {
          tableLines.push(lines[i].trim());
          i += 1;
        }
        if (tableLines.length >= 2) {
          const table = el("table");
          const parseRow = (r) =>
            r
              .slice(1, -1)
              .split("|")
              .map((c) => c.trim());
          const headers = parseRow(tableLines[0]);
          const thead = el("thead");
          const trHead = el("tr");
          for (const h of headers) {
            const th = el("th");
            appendInlineMarkdown(th, h);
            trHead.append(th);
          }
          thead.append(trHead);
          table.append(thead);

          const tbody = el("tbody");
          for (let rIdx = 1; rIdx < tableLines.length; rIdx++) {
            const rowStr = tableLines[rIdx];
            if (/^\|[\s:|-]+\|$/.test(rowStr)) continue;
            const cells = parseRow(rowStr);
            const tr = el("tr");
            for (const c of cells) {
              const td = el("td");
              appendInlineMarkdown(td, c);
              tr.append(td);
            }
            tbody.append(tr);
          }
          table.append(tbody);
          const wrap = el("div", "", "scroll", { tabindex: "0", role: "region", "aria-label": t("Scrollable document table", "Bảng tài liệu có thể cuộn") });
          wrap.append(table);
          container.append(wrap);
          continue;
        }
      }
      if (line.trim().startsWith(">")) {
        const bqLines = [];
        while (i < lines.length && lines[i].trim().startsWith(">")) {
          bqLines.push(lines[i].trim().replace(/^>\s?/, ""));
          i += 1;
        }
        const bq = el("blockquote");
        appendInlineMarkdown(bq, bqLines.join(" "));
        container.append(bq);
        continue;
      }
      const hMatch = line.match(/^(#{1,6})\s+(.*)$/);
      if (hMatch) {
        const level = hMatch[1].length;
        const p = el("p", "", "md-heading");
        p.style.fontWeight = "700";
        p.style.fontSize = level === 1 ? "16px" : level === 2 ? "14.5px" : "13.5px";
        p.style.marginTop = "10px";
        p.style.marginBottom = "4px";
        appendInlineMarkdown(p, hMatch[2]);
        container.append(p);
        i += 1;
        continue;
      }
      if (/^\s*[-*+]\s+/.test(line)) {
        const ul = el("ul");
        while (i < lines.length && /^\s*[-*+]\s+/.test(lines[i])) {
          const li = el("li");
          appendInlineMarkdown(li, lines[i].replace(/^\s*[-*+]\s+/, ""));
          ul.append(li);
          i += 1;
        }
        container.append(ul);
        continue;
      }
      const para = [];
      while (
        i < lines.length &&
        lines[i].trim() &&
        !lines[i].trim().startsWith("```") &&
        !(lines[i].trim().startsWith("|") && lines[i].trim().endsWith("|")) &&
        !lines[i].trim().startsWith(">") &&
        !/^(#{1,6})\s+/.test(lines[i]) &&
        !/^\s*[-*+]\s+/.test(lines[i])
      ) {
        para.push(lines[i].trim());
        i += 1;
      }
      if (para.length) {
        const p = el("p");
        appendInlineMarkdown(p, para.join(" "));
        container.append(p);
      }
    }
    return container;
  }

  function findSubtreeAtPath(rootTree, targetPath) {
    if (!targetPath) return rootTree;
    const queue = [rootTree];
    while (queue.length > 0) {
      const cur = queue.shift();
      if (cur.path === targetPath) return cur;
      for (const child of cur.dirs_list || []) {
        if (targetPath === child.path) return child;
        queue.push(child);
      }
    }
    return rootTree;
  }

  function computeDrilldownLayout(graphData, filterOwner, filterSlot) {
    const filteredArtifacts = graphData.nodes.filter((n) => {
      if (filterOwner !== "all" && n.owner !== filterOwner) return false;
      const sc = n.slot_code || inferV3SlotMeta(n.path, n.kind).slotCode;
      if (filterSlot !== "all" && sc !== filterSlot) return false;
      return true;
    });
    const folderTree = buildFolderTreeFromNodes(filteredArtifacts);
    const activeBranch = findSubtreeAtPath(folderTree, graphState.drillPath);
    if (activeBranch === folderTree && graphState.drillPath) {
      graphState.drillPath = "";
    }

    const items = [];
    for (const childDir of activeBranch.dirs_list || []) {
      const meta = inferV3SlotMeta(childDir.path, "folder");
      const subNames = [
        ...(childDir.dirs_list || []).map((d) => humanizeSlug(d.name.split("/").pop())),
        ...(childDir.nodes || []).map((f) => f.display_title || humanizeSlug(f.label)),
      ].slice(0, 3);
      items.push({
        id: `DIR:${childDir.path}`,
        node_type: "folder",
        path: childDir.path,
        label: safeText(childDir.name),
        display_title: safeText(childDir.name),
        kind: "folder",
        owner: `${childDir.deep} ${t("specs", "tài liệu")}`,
        band: meta.band,
        band_color: meta.bandColor,
        band_label: meta.bandLabel,
        deep: childDir.deep,
        slotCounts: childDir.slotCounts || { M: 0, C: 0, D: 0, S: 0 },
        subPreview: subNames.join(" · ") || childDir.path,
      });
    }
    for (const docNode of activeBranch.nodes || []) {
      const isCurLeaf = graphState.activeLeafPath === docNode.path;
      items.push({
        ...docNode,
        node_type: "artifact",
        is_active_leaf: isCurLeaf,
      });
    }
    if ((activeBranch.dirs_list || []).length === 0 && (activeBranch.nodes || []).length > 0) {
      const primaryLeaf = activeBranch.nodes[0];
      const sibInfo = getSiblingDocuments(primaryLeaf, graphData);
      const existingPaths = new Set(items.map((it) => it.path));
      for (const sib of sibInfo.siblings || []) {
        if (!existingPaths.has(sib.path)) {
          existingPaths.add(sib.path);
          items.push({
            ...sib,
            node_type: "artifact",
            is_sibling_peer: true,
          });
        }
      }
    }

    const totalItems = items.length;
    const totalPages = Math.max(1, Math.ceil(totalItems / graphState.pageSize));
    if (graphState.page >= totalPages) graphState.page = 0;
    const pagedItems = items.slice(
      graphState.page * graphState.pageSize,
      (graphState.page + 1) * graphState.pageSize
    );

    const NODE_W = 368;
    const NODE_H = 88;
    const positions = new Map();
    const nodeLayerIndex = new Map();
    const clusterBoxes = [];
    const itemMap = new Map(pagedItems.map((it) => [it.id, it]));

    const groups = new Map();
    for (const it of pagedItems) {
      const gKey =
        it.node_type === "folder"
          ? t("ARCHITECTURE BRANCHES", "NHÁNH KIẾN TRÚC")
          : it.is_sibling_peer
          ? t("SIBLING SPECIFICATIONS", "TÀI LIỆU CÙNG CẤP")
          : t("LEAF SPECIFICATIONS", "TÀI LIỆU CHI TIẾT");
      if (!groups.has(gKey)) groups.set(gKey, []);
      groups.get(gKey).push(it);
    }

    let curY = 20;
    const canvasW = 820;
    let gIdx = 0;
    for (const [gLabel, members] of groups.entries()) {
      const cols = Math.min(2, Math.max(1, members.length));
      const rows = Math.ceil(members.length / cols);
      const contentW = cols * NODE_W + (cols - 1) * 28;
      const boxW = Math.max(420, contentW + 40);
      const boxH = rows * NODE_H + (rows - 1) * 24 + 50;
      const boxX = Math.round((canvasW - boxW) / 2);

      clusterBoxes.push({
        id: `drill-group-${gIdx}`,
        label: gLabel,
        x: boxX,
        y: curY,
        width: boxW,
        height: boxH,
        count: members.length,
      });

      const startX = Math.round(boxX + (boxW - contentW) / 2);
      members.forEach((m, idx) => {
        const col = idx % cols;
        const row = Math.floor(idx / cols);
        nodeLayerIndex.set(m.id, gIdx * 2 + row);
        positions.set(m.id, {
          x: startX + col * (NODE_W + 28),
          y: curY + 32 + row * (NODE_H + 24),
        });
      });
      curY += boxH + 28;
      gIdx += 1;
    }

    const rolledEdges = [];
    const nodeIdToPath = new Map(graphData.nodes.map((n) => [n.id, n.path]));
    for (const edge of graphData.artifact_edges || []) {
      const fromPath = nodeIdToPath.get(edge.from) || "";
      const toPath = nodeIdToPath.get(edge.to) || "";
      const matchItem = (p) => {
        for (const it of pagedItems) {
          if (it.node_type === "artifact" && it.path === p) return it.id;
          if (it.node_type === "folder" && (p === it.path || p.startsWith(it.path + "/"))) return it.id;
        }
        return null;
      };
      const fId = matchItem(fromPath);
      const tId = matchItem(toPath);
      if (fId && tId && fId !== tId) {
        rolledEdges.push({
          from: fId,
          to: tId,
          relations: edge.relations || [edge.primary_relation || "references"],
        });
      }
    }

    return {
      positions,
      nodeLayerIndex,
      clusterBoxes,
      width: canvasW,
      height: Math.max(260, curY),
      NODE_W,
      NODE_H,
      customNodesMap: itemMap,
      customEdges: consolidateEdges(
        rolledEdges.filter((e) => !String(e.from).startsWith("DIR:") && !String(e.to).startsWith("DIR:"))
      ),
      tableEdges: consolidateEdges(rolledEdges),
      totalItems,
      totalPages,
      activeBranch,
    };
  }

  function computeGraphLayout(graphData, mode, includeClauses, filterOwner, filterSlot) {
    if (mode === "c4-map") {
      return computeC4Layout(graphData);
    }
    if (mode === "drilldown") {
      return computeDrilldownLayout(graphData, filterOwner, filterSlot);
    }

    const allFilteredArtifacts = graphData.nodes.filter((n) => {
      if (filterOwner !== "all" && n.owner !== filterOwner) return false;
      const sc = n.slot_code || inferV3SlotMeta(n.path, n.kind).slotCode;
      if (filterSlot !== "all" && sc !== filterSlot) return false;
      if (graphState.drillPath && !n.path.startsWith(graphState.drillPath)) return false;
      return true;
    });

    const totalItems = allFilteredArtifacts.length;
    const totalPages = Math.max(1, Math.ceil(totalItems / graphState.pageSize));
    if (graphState.page >= totalPages) graphState.page = 0;

    const artifactNodes =
      totalItems > graphState.pageSize
        ? allFilteredArtifacts.slice(
            graphState.page * graphState.pageSize,
            (graphState.page + 1) * graphState.pageSize
          )
        : allFilteredArtifacts;

    const allowedArtifactIds = new Set(artifactNodes.map((n) => n.id));
    const clauseNodes = includeClauses
      ? (graphData.clause_nodes || []).filter((c) => allowedArtifactIds.has(c.artifact_id))
      : [];
    const allNodes = [...artifactNodes, ...clauseNodes];
    const positions = new Map();
    const nodeLayerIndex = new Map();
    const clusterBoxes = [];
    const NODE_W = 236;
    const NODE_H = 88;

    if (!allNodes.length) {
      return { positions, nodeLayerIndex, clusterBoxes, width: 680, height: 220, NODE_W, NODE_H, totalItems, totalPages };
    }

    if (mode === "radial") {
      const width = 800;
      const height = 500;
      const cx = Math.round(width / 2 - NODE_W / 2);
      const cy = Math.round(height / 2 - NODE_H / 2);
      const centerId =
        graphState.selectedNodeId && allNodes.some((n) => n.id === graphState.selectedNodeId)
          ? graphState.selectedNodeId
          : allNodes[0].id;
      const centerNode = allNodes.find((n) => n.id === centerId) || allNodes[0];
      const others = allNodes.filter((n) => n.id !== centerNode.id).slice(0, 10);
      positions.set(centerNode.id, graphState.customPositions.get(`radial:${centerNode.id}`) || { x: cx, y: cy });
      nodeLayerIndex.set(centerNode.id, 0);
      const radiusX = 255;
      const radiusY = 175;
      others.forEach((n, idx) => {
        const angle = (2 * Math.PI * idx) / Math.max(1, others.length) - Math.PI / 2;
        nodeLayerIndex.set(n.id, 1);
        const custom = graphState.customPositions.get(`radial:${n.id}`);
        positions.set(n.id, custom || {
          x: Math.round(cx + Math.cos(angle) * radiusX),
          y: Math.round(cy + Math.sin(angle) * radiusY),
        });
      });
      return { positions, nodeLayerIndex, clusterBoxes, width, height, NODE_W, NODE_H, totalItems, totalPages };
    }

    const layers = new Map();
    for (const n of artifactNodes) {
      const baseRank = (n.rank || 0) * (clauseNodes.length ? 2 : 1);
      if (!layers.has(baseRank)) layers.set(baseRank, []);
      layers.get(baseRank).push(n);
    }
    for (const c of clauseNodes) {
      const parent = artifactNodes.find((a) => a.id === c.artifact_id);
      const cRank = (parent?.rank || 0) * 2 + 1;
      if (!layers.has(cRank)) layers.set(cRank, []);
      layers.get(cRank).push(c);
    }

    const sortedRanks = Array.from(layers.keys()).sort((a, b) => a - b);
    const maxCols = Math.max(1, ...sortedRanks.map((r) => Math.min(3, (layers.get(r) || []).length)));
    const canvasW = Math.max(700, maxCols * (NODE_W + 40) + 180);
    let curY = 24;
    const layerNames = [
      t("L0 · STRATEGY & REQUIREMENTS", "TẦNG 0 · CHIẾN LƯỢC & YÊU CẦU"),
      t("L1 · SYSTEM VIEWS", "TẦNG 1 · GÓC NHÌN HỆ THỐNG"),
      t("L2 · DOMAIN & API SPECS", "TẦNG 2 · PHÂN HỆ & HỢP ĐỒNG API"),
      t("L3 · RUNTIME & DELIVERY", "TẦNG 3 · THỰC THI & BÀN GIAO"),
    ];

    sortedRanks.forEach((r, layerIdx) => {
      const rowNodes = layers.get(r) || [];
      const cols = Math.min(3, Math.max(1, rowNodes.length));
      const rows = Math.ceil(rowNodes.length / cols);
      const contentW = cols * NODE_W + (cols - 1) * 38;
      const boxW = Math.max(340, contentW + 52);
      const boxH = rows * NODE_H + (rows - 1) * 24 + 46;
      const boxX = Math.round((canvasW - boxW) / 2);

      clusterBoxes.push({
        id: `layer-${r}`,
        label: layerNames[Math.min(layerIdx, layerNames.length - 1)],
        x: boxX,
        y: curY,
        width: boxW,
        height: boxH,
        count: rowNodes.length,
      });

      const startX = Math.round(boxX + (boxW - contentW) / 2);
      rowNodes.forEach((n, idx) => {
        const col = idx % cols;
        const row = Math.floor(idx / cols);
        nodeLayerIndex.set(n.id, layerIdx);
        const custom = graphState.customPositions.get(`layered:${n.id}`);
        positions.set(n.id, custom || {
          x: startX + col * (NODE_W + 38),
          y: curY + 32 + row * (NODE_H + 24),
        });
      });
      curY += boxH + 40;
    });

    return { positions, nodeLayerIndex, clusterBoxes, width: canvasW, height: Math.max(260, curY), NODE_W, NODE_H, totalItems, totalPages };
  }

  function consolidateEdges(rawList) {
    const map = new Map();
    for (const item of rawList) {
      const key = `${item.from}-->${item.to}`;
      if (!map.has(key)) {
        map.set(key, {
          from: item.from,
          to: item.to,
          relations: [],
        });
      }
      const entry = map.get(key);
      for (const r of item.relations) {
        if (r && !entry.relations.includes(r)) {
          entry.relations.push(r);
        }
      }
    }
    return Array.from(map.values()).map((e) => {
      const primary = e.relations.includes("satisfies")
        ? "satisfies"
        : e.relations.includes("implements_contract")
        ? "implements_contract"
        : e.relations[0] || "references";
      return {
        from: e.from,
        to: e.to,
        relations: e.relations,
        relation: primary,
        label: e.relations.join(" · "),
      };
    });
  }
  function buildDocumentGraphCard(model, onSelectArtifact, onDatasetModeChange) {
    const card = el("section", "", "doc-graph-card", {
      "aria-label": t("Document architecture graph", "Đồ thị kiến trúc tài liệu"),
    });

    const head = el("div", "", "doc-graph-header");
    const titleGroup = el("div", "", "doc-graph-title-group");
    titleGroup.append(
      el("h3", t("Architecture map", "Bản đồ kiến trúc")),
      el(
        "p",
        t(
          "Select a system or container to inspect its specifications.",
          "Chọn một hệ thống hoặc container để xem tài liệu."
        )
      )
    );
    const kpis = el("div", "", "doc-graph-kpis");
    head.append(titleGroup, kpis);
    card.append(head);

    // Unified Single Toolbar 
    const unifiedToolbar = el("div", "", "doc-graph-unified-toolbar");
    const leftLevels = el("div", "", "doc-graph-mode-group");
    const centerPopovers = el("div", "", "doc-graph-mode-group");
    const rightZoom = el("div", "", "doc-graph-mode-group zoom-group");

    // 1. Runtime Flows Popover
    const flowPopover = el("details", "", "aaf-toolbar-popover");
    flowPopover.append(el("summary", t("Runtime flows", "Luồng thực thi")));
    const flowBody = el("div", "", "aaf-toolbar-popover-body");
    flowPopover.append(flowBody);

    // 2. Map Options & Filters Popover (preserves exact summary text for test_f06_f07)
    const advDetails = el("details", "", "aaf-toolbar-popover aaf-advanced-filters");
    advDetails.append(
      el("summary", t("Map options & filters", "Tùy chọn & bộ lọc bản đồ"))
    );
    const advBody = el("div", "", "aaf-toolbar-popover-body");

    const modeBar = el("div", "", "doc-graph-mode-bar");
    const modeLeft = el("div", "", "doc-graph-mode-group");
    modeLeft.append(el("strong", t("Dataset:", "Bộ dữ liệu:")));

    const wsModeBtn = el(
      "button",
      t("Active Enterprise Workspace", "Workspace Dự án Hiện tại"),
      "aaf-tree-chip-btn",
      {
        type: "button",
        "aria-pressed": String(graphState.datasetMode === "workspace"),
      }
    );
    const v3ModeBtn = el(
      "button",
      t("Full Maximal V3 Catalogue (690 Slots · 10 Domains)", "Danh mục V3 Maximal Đầy đủ (690 Slots · 10 Domains)"),
      "aaf-tree-chip-btn",
      {
        type: "button",
        "aria-pressed": String(graphState.datasetMode === "v3-maximal"),
      }
    );
    modeLeft.append(wsModeBtn, v3ModeBtn);

    const slotGroup = el("div", "", "doc-graph-mode-group");
    slotGroup.append(el("span", t("Contract:", "Hợp đồng:"), "muted"));
    const slotButtons = [];
    for (const [code, labelEn, labelVi] of [
      ["all", "All", "Tất cả"],
      ["M", "[M] Mandatory", "[M] Bắt buộc"],
      ["S", "[S] Seam", "[S] Nghĩa vụ"],
      ["C", "[C] Conditional", "[C] Có ĐK"],
      ["D", "[D] Derived", "[D] Tự sinh"],
    ]) {
      const b = el("button", t(labelEn, labelVi), "aaf-tree-chip-btn", {
        type: "button",
        "aria-pressed": String(graphState.slotFilter === code),
      });
      b.onclick = () => {
        graphState.slotFilter = code;
        graphState.page = 0;
        for (const item of slotButtons) {
          item.btn.setAttribute("aria-pressed", String(item.code === graphState.slotFilter));
        }
        renderCanvasAndPassport();
        if (onDatasetModeChange) onDatasetModeChange();
      };
      slotButtons.push({ code, btn: b });
      slotGroup.append(b);
    }
    modeBar.append(modeLeft, slotGroup);

    const toolbar = el("div", "", "doc-graph-toolbar");
    const layoutLabel = el("label", t("Architecture model", "Mô hình hiển thị"));
    const layoutSelect = el("select", "", "", {
      "aria-label": t("Graph layout", "Bố cục Graph"),
    });
    for (const [val, labelEn, labelVi] of [
      ["c4-map", "C4 Model (C1 / C2 / Doc Tree)", "Mô hình C4 (C1 / C2 / Cây Tài liệu)"],
      ["drilldown", "Folder Tree Drill-Down", "Cây Thư mục Đệ quy"],
      ["doc-dag", "Document Dependency DAG", "Đồ thị Phụ thuộc Tài liệu"],
      ["radial", "Radial Hub Network", "Mạng Tâm điểm"],
    ]) {
      const opt = el("option", t(labelEn, labelVi), "", { value: val });
      opt.selected = graphState.layoutMode === val;
      layoutSelect.append(opt);
    }
    layoutLabel.append(layoutSelect);

    const traceLabel = el("label", t("Trace lens", "Truy vết"));
    const traceSelect = el("select", "", "", {
      "aria-label": t("Trace lens", "Truy vết"),
    });
    for (const [val, labelEn, labelVi] of [
      ["all", "All connections", "Tất cả liên kết"],
      ["upstream", "Upstream authority (Sources)", "Nguồn gốc (Upstream)"],
      ["downstream", "Downstream impact (Consumers)", "Ảnh hưởng xuôi (Downstream)"],
    ]) {
      const opt = el("option", t(labelEn, labelVi), "", { value: val });
      opt.selected = graphState.traceMode === val;
      traceSelect.append(opt);
    }
    traceLabel.append(traceSelect);

    const relLabel = el("label", t("Relation filter", "Lọc quan hệ"));
    const relSelect = el("select", "", "", {
      "aria-label": t("Relation filter", "Lọc quan hệ"),
    });
    relLabel.append(relSelect);

    const ownerLabel = el("label", t("Owner skill", "Skill sở hữu"));
    const ownerSelect = el("select", "", "", {
      "aria-label": t("Owner skill", "Skill sở hữu"),
    });
    ownerLabel.append(ownerSelect);

    toolbar.append(layoutLabel, traceLabel, relLabel, ownerLabel);
    advBody.append(modeBar, toolbar);
    advDetails.append(advBody);

    centerPopovers.append(flowPopover, advDetails);

    // 3. Zoom & Wide Controls
    const zoomOutBtn = el("button", "−", "doc-graph-crumb-btn", {
      type: "button",
      "aria-label": t("Zoom out graph", "Thu nhỏ đồ thị"),
    });
    const zoomResetBtn = el("button", `${Math.round(graphState.zoom * 100)}%`, "doc-graph-crumb-btn", {
      type: "button",
      "aria-label": t("Reset graph zoom", "Đặt lại tỷ lệ đồ thị"),
    });
    const zoomInBtn = el("button", "+", "doc-graph-crumb-btn", {
      type: "button",
      "aria-label": t("Zoom in graph", "Phóng to đồ thị"),
    });
    const wideBtn = el("button", t("Wide", "Mở rộng"), "doc-graph-crumb-btn", {
      type: "button",
    });
    rightZoom.append(zoomOutBtn, zoomResetBtn, zoomInBtn, wideBtn);

    unifiedToolbar.append(leftLevels, centerPopovers, rightZoom);
    card.append(unifiedToolbar);

    const paginationHost = el("div");
    const stage = el("div", "", "doc-graph-stage" + (graphState.expandedCanvas ? " expanded" : ""), {
      role: "region",
      tabindex: "0",
      "aria-label": t("Scrollable document graph canvas", "Khung cuộn đồ thị tài liệu"),
    });

    const adjacencyDetails = el("details");
    adjacencyDetails.append(
      el(
        "summary",
        t(
          "Document relationship & obligation matrix (accessible table view)",
          "Bảng ma trận quan hệ C4 & nghĩa vụ tài liệu (chế độ bảng truy cập)"
        )
      )
    );
    const adjacencyScroll = el("div", "", "scroll", {
      role: "region",
      tabindex: "0",
      "aria-label": t("Document relationship table", "Bảng quan hệ tài liệu"),
    });
    adjacencyDetails.append(adjacencyScroll);

    function rebuildDropdownOptions(graphData) {
      relSelect.replaceChildren();
      const relOptions = [["all", t("All relations", "Mọi quan hệ")]];
      for (const r of graphData.stats.relations || []) {
        relOptions.push([r, safeText(r)]);
      }
      for (const [val, label] of relOptions) {
        const opt = el("option", label, "", { value: val });
        opt.selected = graphState.relationFilter === val;
        relSelect.append(opt);
      }

      ownerSelect.replaceChildren();
      const ownerOptions = [["all", t("All owners", "Mọi skill")]];
      for (const o of graphData.stats.owners || []) {
        ownerOptions.push([o, safeText(o)]);
      }
      for (const [val, label] of ownerOptions) {
        const opt = el("option", label, "", { value: val });
        opt.selected = graphState.ownerFilter === val;
        ownerSelect.append(opt);
      }
    }

    function renderCanvasAndPassport() {
      const graphData = extractGraphData(model);
      rebuildDropdownOptions(graphData);

      kpis.replaceChildren();
      kpis.append(
        el("span", `${graphData.stats.artifacts} ${t("specs", "tài liệu")}`, "doc-graph-kpi"),
        el("span", `${graphData.stats.clauses} ${t("clauses", "điều khoản")}`, "doc-graph-kpi")
      );

      leftLevels.replaceChildren();
      flowBody.replaceChildren();
      paginationHost.replaceChildren();
      stage.replaceChildren();
      adjacencyScroll.replaceChildren();
      zoomResetBtn.textContent = `${Math.round(graphState.zoom * 100)}%`;
      layoutSelect.value = graphState.layoutMode;
      wideBtn.textContent = document.querySelector(".aaf-docs-workspace.wide-graph-mode")
        ? t("Sidebar", "Hiện Sidebar")
        : t("Wide", "Mở rộng");

      if (graphState.layoutMode === "c4-map") {
        for (const [lvl, enLbl, viLbl] of [
          ["C1", "C1 · System context", "C1 · System context"],
          ["C2", "C2 · Containers", "C2 · Containers"],
          ["CONTAINER_DOCS", "Doc Tree", "Cây Tài liệu"],
        ]) {
          const b = el("button", lvl === "CONTAINER_DOCS" ? t("Doc Tree", "Cây tài liệu") : lvl, "aaf-tree-chip-btn", {
            type: "button",
            "aria-label": t(enLbl, viLbl),
            title: t(enLbl, viLbl),
            "aria-pressed": String(graphState.c4Level === lvl),
          });
          b.onclick = () => {
            graphState.c4Level = lvl;
            if (lvl === "C1") {
              graphState.sidebarScope = "system";
              graphState.selectedNodeId = graphState.c1FocusedSystem || "sys.omnipay-core";
            } else {
              graphState.sidebarScope = "container";
              graphState.selectedNodeId = graphState.c4FocusedContainer || "ctr.payment-orchestrator";
            }
            renderCanvasAndPassport();
            if (onDatasetModeChange) onDatasetModeChange();
          };
          leftLevels.append(b);
        }

        for (const [fKey, fEn, fVi] of [
          ["all", "All Connections", "Tất cả kết nối"],
          ["checkout", "01 · Checkout & Idempotency (REQ-022)", "01 · Checkout & Idempotency (REQ-022)"],
          ["timeout-webhook", "02 · 30s Timeout & Webhook (REQ-021)", "02 · Timeout 30s & Webhook (REQ-021)"],
          ["fraud-ledger", "03 · AI Fraud <=25ms & Ledger (REQ-023)", "03 · AI Fraud <=25ms & Sổ cái (REQ-023)"],
        ]) {
          const fb = el("button", t(fEn, fVi), "aaf-tree-chip-btn", {
            type: "button",
            "aria-pressed": String(graphState.c4GuidedFlow === fKey),
          });
          fb.onclick = () => {
            graphState.c4GuidedFlow = fKey;
            flowPopover.open = false;
            renderCanvasAndPassport();
          };
          flowBody.append(fb);
        }
      } else {
        const backC4Btn = el("button", t("← C2 Map", "← Bản đồ C2"), "doc-graph-crumb-btn", {
          type: "button",
        });
        backC4Btn.onclick = () => {
          graphState.layoutMode = "c4-map";
          graphState.c4Level = "C2";
          graphState.drillPath = "";
          renderCanvasAndPassport();
        };
        leftLevels.append(backC4Btn);
        if (graphState.drillPath) {
          const upBtn = el("button", t("← Up 1 Level", "← Lùi 1 cấp"), "doc-graph-crumb-btn", {
            type: "button",
          });
          upBtn.onclick = () => {
            const parts = graphState.drillPath.split("/").filter(Boolean);
            parts.pop();
            graphState.drillPath = parts.join("/");
            graphState.page = 0;
            renderCanvasAndPassport();
          };
          leftLevels.append(upBtn);
        }
      }

      const layout = computeGraphLayout(
        graphData,
        graphState.layoutMode,
        graphState.showClauses,
        graphState.ownerFilter,
        graphState.slotFilter
      );
      const {
        positions,
        nodeLayerIndex,
        clusterBoxes,
        width,
        height,
        NODE_W,
        NODE_H,
        customNodesMap,
        customEdges,
        totalItems,
        totalPages,
      } = layout;

      if (totalPages && totalPages > 1) {
        const pagBar = el("div", "", "doc-graph-mode-group");
        pagBar.style.marginBottom = "6px";
        pagBar.append(
          el(
            "span",
            t(
              `Page ${graphState.page + 1}/${totalPages} (${totalItems} specs)`,
              `Trang ${graphState.page + 1}/${totalPages} (${totalItems} tài liệu)`
            ),
            "mono muted"
          )
        );
        const prevBtn = el("button", t("← Prev", "← Trước"), "doc-graph-crumb-btn", {
          type: "button",
        });
        prevBtn.disabled = graphState.page <= 0;
        prevBtn.onclick = () => {
          graphState.page = Math.max(0, graphState.page - 1);
          renderCanvasAndPassport();
        };
        const nextBtn = el("button", t("Next →", "Tiếp →"), "doc-graph-crumb-btn", {
          type: "button",
        });
        nextBtn.disabled = graphState.page + 1 >= totalPages;
        nextBtn.onclick = () => {
          graphState.page = Math.min(totalPages - 1, graphState.page + 1);
          renderCanvasAndPassport();
        };
        pagBar.append(prevBtn, nextBtn);
        paginationHost.append(pagBar);
      }

      const allMap = new Map();
      for (const n of graphData.nodes) allMap.set(n.id, n);
      for (const c of graphData.clause_nodes || []) allMap.set(c.id, c);
      if (customNodesMap) {
        for (const [k, v] of customNodesMap.entries()) allMap.set(k, v);
      }

      if (!graphState.selectedNodeId || !allMap.has(graphState.selectedNodeId)) {
        const firstPosId = positions.keys().next().value;
        graphState.selectedNodeId = positions.has(graphState.c4FocusedContainer)
          ? graphState.c4FocusedContainer
          : firstPosId || (graphData.nodes[0] && graphData.nodes[0].id);
      }
      const activeNodeId = graphState.hoveredNodeId || graphState.selectedNodeId;
      const activeNode = activeNodeId ? allMap.get(activeNodeId) : null;

      let consolidated = [];
      if (customEdges) {
        consolidated = customEdges;
      } else {
        const rawPairs = graphState.showClauses
          ? (graphData.edges || []).map((e) => ({
              from: e.from,
              to: e.to,
              relations: [e.relation],
            }))
          : (graphData.artifact_edges || []).map((e) => ({
              from: e.from,
              to: e.to,
              relations: e.relations || [e.primary_relation || "references"],
            }));
        consolidated = consolidateEdges(rawPairs);
      }

      const visibleEdges = consolidated.filter((e) => {
        if (!positions.has(e.from) || !positions.has(e.to)) return false;
        if (
          graphState.relationFilter !== "all" &&
          !(e.relations || []).includes(graphState.relationFilter)
        )
          return false;
        return true;
      });

      const highlightedNodes = new Set();
      if (activeNode) {
        highlightedNodes.add(activeNode.id);
        if (graphState.traceMode === "all" || graphState.traceMode === "upstream") {
          for (const u of activeNode.upstream || []) highlightedNodes.add(u);
          for (const u of activeNode.upstream_artifacts || []) highlightedNodes.add(u);
        }
        if (graphState.traceMode === "all" || graphState.traceMode === "downstream") {
          for (const d of activeNode.downstream || []) highlightedNodes.add(d);
          for (const d of activeNode.downstream_artifacts || []) highlightedNodes.add(d);
        }
      }

      const svg = svgEl("svg", {
        viewBox: `0 0 ${width} ${height}`,
        role: "group",
        "aria-label": t("Interactive document architecture graph", "Đồ thị kiến trúc tài liệu tương tác"),
      });
      svg.style.minWidth = `${Math.round(560 * graphState.zoom)}px`;
      svg.style.width = `${Math.round(100 * graphState.zoom)}%`;

      const defs = svgEl("defs");
      for (const [id, colorVar] of [
        ["aaf-arrow-default", "var(--line)"],
        ["aaf-arrow-active", "var(--accent)"],
        ["aaf-arrow-ok", "var(--ok)"],
      ]) {
        const marker = svgEl("marker", {
          id,
          viewBox: "0 0 10 10",
          refX: "9",
          refY: "5",
          markerWidth: "6",
          markerHeight: "6",
          orient: "auto-start-reverse",
        });
        marker.append(
          svgEl("path", {
            d: "M 0 1 L 10 5 L 0 9 z",
            fill: colorVar,
          })
        );
        defs.append(marker);
      }
      svg.append(defs);

      for (const box of clusterBoxes) {
        const g = svgEl("g");
        g.append(
          svgEl("rect", {
            x: box.x,
            y: box.y,
            width: box.width,
            height: box.height,
            rx: 10,
            class: "doc-graph-cluster-rect",
          }),
          svgEl(
            "text",
            {
              x: box.x + 14,
              y: box.y + 20,
              class: "doc-graph-cluster-label",
            },
            `${box.label}`
          )
        );
        svg.append(g);
      }

      const edgesPathLayer = svgEl("g", { class: "aaf-layer-edge-paths" });
      const nodesLayer = svgEl("g", { class: "aaf-layer-nodes" });
      const edgeLabelsLayer = svgEl("g", { class: "aaf-layer-edge-labels" });

      for (const sp of layout.treeSpinePaths || []) {
        edgesPathLayer.append(
          svgEl("path", {
            d: sp.d,
            fill: "none",
            stroke: sp.color || "var(--accent)",
            "stroke-width": "2.2",
            "marker-end": sp.arrow || undefined,
          })
        );
        if (sp.label) {
          const pillW = Math.max(54, Math.round(sp.label.length * 6.0 + 14));
          edgeLabelsLayer.append(
            svgEl("rect", {
              x: sp.lx - Math.round(pillW / 2),
              y: sp.ly - 9,
              width: pillW,
              height: 18,
              rx: 9,
              class: "doc-graph-edge-pill",
            }),
            svgEl(
              "text",
              {
                x: sp.lx,
                y: sp.ly + 3.5,
                "text-anchor": "middle",
                class: "doc-graph-edge-text",
              },
              sp.label.slice(0, 18)
            )
          );
        }
      }

      let sideArcCount = 0;
      visibleEdges.forEach((edge) => {
        const pFrom = positions.get(edge.from);
        const pTo = positions.get(edge.to);
        if (!pFrom || !pTo) return;

        const isEdgeHighlighted =
          activeNode &&
          (edge.from === activeNode.id ||
            edge.to === activeNode.id ||
            (highlightedNodes.has(edge.from) && highlightedNodes.has(edge.to)));

        const sameRow = Math.abs(pFrom.y - pTo.y) < 16;
        const lFrom = nodeLayerIndex.get(edge.from) ?? 0;
        const lTo = nodeLayerIndex.get(edge.to) ?? 0;
        const isLongSkip =
          graphState.layoutMode !== "radial" &&
          Math.abs(lFrom - lTo) > 1 &&
          Math.abs(pFrom.x - pTo.x) < 60;

        let dPath = "";
        let labelX = 0;
        let labelY = 0;

        const fw = pFrom.w || NODE_W;
        const fh = pFrom.h || NODE_H;
        const tw = pTo.w || NODE_W;
        const th = pTo.h || NODE_H;
        if (sameRow && Math.abs(pFrom.x - pTo.x) > fw - 10) {
          const goingRight = pFrom.x < pTo.x;
          const x1 = goingRight ? pFrom.x + fw : pFrom.x;
          const y1 = pFrom.y + Math.round(fh / 2);
          const x2 = goingRight ? pTo.x : pTo.x + tw;
          const y2 = pTo.y + Math.round(th / 2);
          dPath = `M ${x1} ${y1} L ${x2} ${y2}`;
          labelX = Math.round((x1 + x2) / 2);
          labelY = pFrom.y + fh + 12;
        } else if (isLongSkip) {
          const sideSign = sideArcCount % 2 === 0 ? 1 : -1;
          sideArcCount += 1;
          const x1 = sideSign > 0 ? pFrom.x + fw : pFrom.x;
          const y1 = pFrom.y + fh / 2;
          const x2 = sideSign > 0 ? pTo.x + tw : pTo.x;
          const y2 = pTo.y + th / 2;
          const ctrlX = sideSign > 0 ? Math.max(x1, x2) + 52 : Math.min(x1, x2) - 52;
          dPath = `M ${x1} ${y1} C ${ctrlX} ${y1}, ${ctrlX} ${y2}, ${x2} ${y2}`;
          labelX = Math.round(0.35 * x1 + 0.65 * ctrlX);
          labelY = Math.round((y1 + y2) / 2);
        } else {
          const goingDown = pFrom.y <= pTo.y;
          const x1 = pFrom.x + fw / 2;
          const y1 = goingDown ? pFrom.y + fh : pFrom.y;
          const x2 = pTo.x + tw / 2;
          const y2 = goingDown ? pTo.y : pTo.y + th;
          const midY = Math.round((y1 + y2) / 2);
          dPath = `M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`;
          labelX = Math.round((x1 + x2) / 2);
          const stagger = Math.abs(x1 - x2) > 80 ? (x1 < x2 ? -10 : 10) : 0;
          labelY = Math.abs(x1 - x2) < 10 && y2 - y1 > 110 ? y1 + 36 : midY + stagger;
        }

        const pathEl = svgEl("path", {
          d: dPath,
          class: "doc-graph-edge-path" + (isEdgeHighlighted ? " highlighted" : ""),
          "data-rel": edge.relation,
          "marker-end": isEdgeHighlighted
            ? "url(#aaf-arrow-active)"
            : edge.relation === "satisfies" || edge.relation === "emphasis"
            ? "url(#aaf-arrow-ok)"
            : "url(#aaf-arrow-default)",
        });
        edgesPathLayer.append(pathEl);

        const labelText = safeText(edge.label).slice(0, 18);
        const pillW = Math.max(54, Math.round(labelText.length * 5.8 + 12));
        const edgeGroup = svgEl("g");
        edgeGroup.append(
          svgEl("rect", {
            x: labelX - Math.round(pillW / 2),
            y: labelY - 9,
            width: pillW,
            height: 18,
            rx: 9,
            class: "doc-graph-edge-pill",
          }),
          svgEl(
            "text",
            {
              x: labelX,
              y: labelY + 3.5,
              "text-anchor": "middle",
              class: "doc-graph-edge-text",
            },
            labelText
          )
        );
        edgeLabelsLayer.append(edgeGroup);
      });

      // Strictly <= 3 <text> elements per SVG node 
      for (const [nodeId, pos] of positions.entries()) {
        const nodeObj = allMap.get(nodeId);
        if (!nodeObj) continue;
        const isSelected = graphState.selectedNodeId === nodeId;
        const isUpstream = activeNode && nodeId !== activeNode.id && (activeNode.upstream || []).includes(nodeId);
        const isDownstream = activeNode && nodeId !== activeNode.id && (activeNode.downstream || []).includes(nodeId);
        const isFlowDimmed =
          graphState.layoutMode === "c4-map" &&
          graphState.c4Level === "C2" &&
          graphState.c4GuidedFlow !== "all" &&
          nodeObj.flowTags &&
          !nodeObj.flowTags.includes(graphState.c4GuidedFlow);

        let cls = "doc-graph-node";
        if (nodeObj.node_type === "c4-container") cls += " c4-container-node";
        else if (nodeObj.node_type === "c4-external") cls += " c4-external-node";
        else if (nodeObj.node_type === "c4-pillar") cls += " c4-pillar-node";
        else if (nodeObj.node_type === "folder") cls += " folder-node";

        if (nodeObj.is_active_leaf) cls += " leaf-active-node selected";
        else if (nodeObj.is_sibling_peer) cls += " sibling-peer-node";
        else if (isSelected) cls += " selected";
        else if (isUpstream) cls += " trace-upstream";
        else if (isDownstream) cls += " trace-downstream";
        else if (isFlowDimmed) cls += " dimmed";

        const ariaLabel = `Graph node ${nodeObj.id}: ${nodeObj.title || nodeObj.path} (${nodeObj.kind} · ${nodeObj.owner})`;

        const g = svgEl("g", {
          class: cls,
          role: "button",
          tabindex: "0",
          "aria-label": ariaLabel,
          "data-node-id": nodeObj.id,
        });

        const curW = pos.w || NODE_W;
        const curH = pos.h || NODE_H;

        g.append(
          svgEl("rect", {
            x: pos.x,
            y: pos.y,
            width: curW,
            height: curH,
            rx: nodeObj.node_type === "clause" ? 18 : 8,
            class: "doc-graph-node-box",
          })
        );

        const accentColor = nodeObj.band_color || "var(--accent)";
        g.append(
          svgEl("rect", {
            x: pos.x + 2,
            y: pos.y + 2,
            width: curW - 4,
            height: 4,
            rx: 3,
            fill: accentColor,
          })
        );

        let titleLine = "";
        let subLine = "";
        let metaLine = "";

        const trimWord = (str, lim) => {
          const s = String(str || "");
          if (s.length <= lim) return s;
          const cut = s.slice(0, lim - 1);
          const sp = cut.lastIndexOf(" ");
          return (sp > lim * 0.55 ? cut.slice(0, sp) : cut) + "…";
        };
        const maxT = curW >= 330 ? 44 : 29;
        const maxS = curW >= 330 ? 50 : 35;
        const maxM = curW >= 330 ? 48 : 35;

        if (nodeObj.node_type === "c4-container" || nodeObj.node_type === "c4-external" || nodeObj.node_type === "c4-pillar") {
          titleLine = trimWord(`${nodeObj.title}`, maxT);
          subLine = trimWord(nodeObj.subtitle || "", maxS);
          metaLine = trimWord(nodeObj.meta || "", maxM);
        } else if (nodeObj.node_type === "folder") {
          titleLine = trimWord(`${nodeObj.display_title || nodeObj.label}`, maxT);
          subLine = trimWord(nodeObj.subPreview || nodeObj.path, maxS);
          const sc = nodeObj.slotCounts || { M: 0, S: 0, C: 0, D: 0 };
          metaLine = `${nodeObj.deep} ${t("specs", "tài liệu")} ([M]:${sc.M || 0} [S]:${sc.S || 0})`;
        } else if (nodeObj.node_type === "clause") {
          titleLine = `${nodeObj.id} · ${humanizeSlug(nodeObj.anchor || "clause")}`.slice(0, maxT);
          subLine = String(nodeObj.summary || `${nodeObj.path}#${nodeObj.anchor || ""}`).slice(0, maxS);
          metaLine = `${nodeObj.artifact_id} -> ${(nodeObj.downstream || []).length} ${t("consumers", "đích")}`;
        } else {
          const slotTag = nodeObj.slot_code ? `[${nodeObj.slot_code}] ` : "";
          const niceTitle = nodeObj.display_title || humanizeSlug(nodeObj.label || nodeObj.id);
          titleLine = trimWord(`${slotTag}${niceTitle}`, maxT);
          subLine = trimWord(summarizeArtifactNode(nodeObj), maxS);
          metaLine = trimWord(`${nodeObj.kind} · ${nodeObj.owner}`, maxM);
        }

        if (curH <= 60) {
          g.append(
            svgEl("text", { x: pos.x + 12, y: pos.y + 22, class: "doc-graph-node-title" }, titleLine),
            svgEl("text", { x: pos.x + 12, y: pos.y + 41, class: "doc-graph-node-meta" }, metaLine)
          );
        } else {
          g.append(
            svgEl("text", { x: pos.x + 12, y: pos.y + 25, class: "doc-graph-node-title" }, titleLine),
            svgEl("text", { x: pos.x + 12, y: pos.y + 46, class: "doc-graph-node-sub" }, subLine),
            svgEl("text", { x: pos.x + 12, y: pos.y + 68, class: "doc-graph-node-meta" }, metaLine)
          );
        }

        const activateNode = () => {
          if (graphState.layoutMode === "c4-map" && graphState.c4Level === "C1") {
            graphState.selectedNodeId = nodeObj.id;
            graphState.c1FocusedSystem = nodeObj.id;
            graphState.sidebarScope = "system";
            const wbDoc = nodeObj.whitebox_doc;
            if (wbDoc) {
              graphState.activeLeafPath = wbDoc.path;
              graphState.activeLeafNode = wbDoc;
              if (onSelectArtifact) onSelectArtifact(wbDoc.path, wbDoc);
            }
            if (onDatasetModeChange) onDatasetModeChange();
            window.setTimeout(() => renderCanvasAndPassport(), 0);
            return;
          }
          if (nodeObj.drillsToC2) {
            graphState.c4Level = "C2";
            graphState.sidebarScope = "container";
            graphState.selectedNodeId = graphState.c4FocusedContainer || "ctr.payment-orchestrator";
            renderCanvasAndPassport();
            if (onDatasetModeChange) onDatasetModeChange();
            return;
          }
          if (nodeObj.node_type === "c4-pillar") {
            graphState.layoutMode = "drilldown";
            graphState.drillPath = nodeObj.folderPath;
            graphState.page = 0;
            renderCanvasAndPassport();
            return;
          }
          if (nodeObj.node_type === "folder") {
            if (nodeObj.whitebox_doc) {
              graphState.activeLeafPath = nodeObj.whitebox_doc.path;
              graphState.activeLeafNode = nodeObj.whitebox_doc;
              if (onSelectArtifact) onSelectArtifact(nodeObj.whitebox_doc.path, nodeObj.whitebox_doc);
              renderCanvasAndPassport();
              return;
            }
            graphState.layoutMode = "drilldown";
            graphState.drillPath = nodeObj.path;
            graphState.page = 0;
            renderCanvasAndPassport();
            return;
          }
          if (nodeObj.node_type === "c4-container" || nodeObj.node_type === "c4-external") {
            graphState.selectedNodeId = nodeObj.id;
            graphState.c4FocusedContainer = nodeObj.id;
            graphState.sidebarScope = "container";
            const wbDoc = nodeObj.whitebox_doc;
            if (wbDoc) {
              graphState.activeLeafPath = wbDoc.path;
              graphState.activeLeafNode = wbDoc;
              if (onSelectArtifact) onSelectArtifact(wbDoc.path, wbDoc);
            }
            if (onDatasetModeChange) onDatasetModeChange();
            window.setTimeout(() => renderCanvasAndPassport(), 0);
            return;
          }
          graphState.selectedNodeId = nodeObj.id;
          const leafDoc = nodeObj.whitebox_doc || nodeObj;
          if (leafDoc && leafDoc.path) {
            graphState.activeLeafPath = leafDoc.path;
            graphState.activeLeafNode = leafDoc;
          }
          const targetPath = nodeObj.path;
          if (onSelectArtifact && targetPath) {
            onSelectArtifact(targetPath, leafDoc);
          }
          window.setTimeout(() => renderCanvasAndPassport(), 0);
        };

        const drillNodeOnDblClick = () => {
          if (graphState.layoutMode === "c4-map" && graphState.c4Level === "C1" && nodeObj.drillsToC2) {
            graphState.c4Level = "C2";
            graphState.sidebarScope = "container";
            graphState.selectedNodeId = graphState.c4FocusedContainer || "ctr.payment-orchestrator";
            renderCanvasAndPassport();
            if (onDatasetModeChange) onDatasetModeChange();
            return;
          }
          if (graphState.layoutMode === "c4-map" && graphState.c4Level === "C2" && (nodeObj.node_type === "c4-container" || nodeObj.node_type === "c4-external")) {
            graphState.c4FocusedContainer = nodeObj.id;
            graphState.selectedNodeId = nodeObj.id;
            graphState.c4Level = "CONTAINER_DOCS";
            graphState.sidebarScope = "container";
            renderCanvasAndPassport();
            if (onDatasetModeChange) onDatasetModeChange();
          }
        };

        g.addEventListener("click", activateNode);
        g.addEventListener("dblclick", drillNodeOnDblClick);
        g.addEventListener("keydown", (ev) => {
          if (ev.key === "Enter" || ev.key === " ") {
            ev.preventDefault();
            activateNode();
          }
        });

        nodesLayer.append(g);
      }
      svg.append(edgesPathLayer, nodesLayer, edgeLabelsLayer);
      stage.append(svg);

      const table = el("table");
      table.append(
        el(
          "caption",
          t(
            "C4 & Document dependencies, references, and obligation links",
            "Danh sách liên kết C4, tham chiếu và nghĩa vụ"
          )
        )
      );
      const thead = el("thead");
      const hRow = el("tr");
      for (const col of [
        t("Consumer / Source (From)", "Thành phần gọi (Từ)"),
        t("Relation / Protocol", "Quan hệ / Giao thức"),
        t("Target / Authority (To)", "Thành phần đích (Tới)"),
        t("Obligation / Clause", "Nghĩa vụ / Điều khoản"),
      ]) {
        hRow.append(el("th", col));
      }
      thead.append(hRow);
      table.append(thead);
      const tbody = el("tbody");
      const allMatrixEdges = layout.tableEdges || visibleEdges;
      const matrixEdges = allMatrixEdges.length > 120 ? allMatrixEdges.slice(0, 120) : allMatrixEdges;
      for (const edge of matrixEdges) {
        const tr = el("tr");
        const fromNode = allMap.get(edge.from);
        const toNode = allMap.get(edge.to);
        tr.append(
          el("td", fromNode ? `${fromNode.id} (${fromNode.label || fromNode.path})` : edge.from, "mono"),
          el("td", safeText(edge.label)),
          el("td", toNode ? `${toNode.id} (${toNode.label || toNode.path})` : edge.to, "mono"),
          el("td", (edge.flowTags || []).join(", ") || "—", "mono")
        );
        tbody.append(tr);
      }
      table.append(tbody);
      adjacencyScroll.append(table);
    }

    wsModeBtn.onclick = () => {
      graphState.datasetMode = "workspace";
      graphState.layoutMode = "c4-map";
      graphState.c4Level = "C2";
      graphState.drillPath = "";
      graphState.page = 0;
      graphState.selectedNodeId = "ctr.payment-orchestrator";
      wsModeBtn.setAttribute("aria-pressed", "true");
      v3ModeBtn.setAttribute("aria-pressed", "false");
      advDetails.open = false;
      renderCanvasAndPassport();
      if (onDatasetModeChange) onDatasetModeChange();
    };

    v3ModeBtn.onclick = () => {
      graphState.datasetMode = "v3-maximal";
      graphState.layoutMode = "c4-map";
      graphState.c4Level = "C2";
      graphState.drillPath = "documents/architecture";
      graphState.page = 0;
      graphState.selectedNodeId = "ctr.payment-orchestrator";
      wsModeBtn.setAttribute("aria-pressed", "false");
      v3ModeBtn.setAttribute("aria-pressed", "true");
      advDetails.open = false;
      renderCanvasAndPassport();
      if (onDatasetModeChange) onDatasetModeChange();
    };

    layoutSelect.onchange = () => {
      graphState.layoutMode = layoutSelect.value;
      graphState.page = 0;
      renderCanvasAndPassport();
    };
    traceSelect.onchange = () => {
      graphState.traceMode = traceSelect.value;
      renderCanvasAndPassport();
    };
    relSelect.onchange = () => {
      graphState.relationFilter = relSelect.value;
      renderCanvasAndPassport();
    };
    ownerSelect.onchange = () => {
      graphState.ownerFilter = ownerSelect.value;
      graphState.page = 0;
      renderCanvasAndPassport();
    };
    zoomOutBtn.onclick = () => {
      graphState.zoom = Math.max(0.75, Math.round((graphState.zoom - 0.15) * 100) / 100);
      renderCanvasAndPassport();
    };
    zoomInBtn.onclick = () => {
      graphState.zoom = Math.min(1.6, Math.round((graphState.zoom + 0.15) * 100) / 100);
      renderCanvasAndPassport();
    };
    zoomResetBtn.onclick = () => {
      graphState.zoom = 1;
      graphState.customPositions.clear();
      renderCanvasAndPassport();
    };
    wideBtn.onclick = () => {
      const ws = document.querySelector(".aaf-docs-workspace");
      if (ws) ws.classList.toggle("wide-graph-mode");
      renderCanvasAndPassport();
    };

    stage.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape") {
        if (graphState.layoutMode === "c4-map" && graphState.c4Level === "CONTAINER_DOCS") {
          ev.preventDefault();
          graphState.c4Level = "C2";
          renderCanvasAndPassport();
        } else if (graphState.layoutMode === "c4-map" && graphState.c4Level === "C2") {
          ev.preventDefault();
          graphState.c4Level = "C1";
          renderCanvasAndPassport();
        } else if (graphState.drillPath) {
          ev.preventDefault();
          const parts = graphState.drillPath.split("/").filter(Boolean);
          parts.pop();
          graphState.drillPath = parts.join("/");
          graphState.page = 0;
          renderCanvasAndPassport();
        }
      }
    });

    renderCanvasAndPassport();

    const footer = el("div", "", "doc-graph-footer");
    const legend = el("div", "", "doc-graph-legend");
    for (const [labelEn, labelVi, borderColor] of [
      ["C2 Container", "Container C2", "var(--b00)"],
      ["Zero-Trust / Strategy", "Bảo mật / Chiến lược", "var(--b01)"],
      ["Edge / Seam [S]", "Cổng biên / Nghĩa vụ [S]", "var(--b02)"],
      ["AI Risk Engine", "AI Chấm điểm Rủi ro", "var(--b03)"],
      ["Ledger & Reconcile", "Sổ cái & Đối soát", "var(--b04)"],
    ]) {
      const item = el("span", "", "doc-graph-legend-item");
      const sw = el("span", "", "doc-graph-swatch");
      sw.style.borderColor = borderColor;
      item.append(sw, el("span", t(labelEn, labelVi)));
      legend.append(item);
    }
    footer.append(legend);

    card.append(paginationHost, stage, footer, adjacencyDetails);
    return { card, refreshGraph: renderCanvasAndPassport };
  }

  function enhanceLeftDocumentTree(docSection, model, reader, onSelectV3Node, refreshGraph, onOpenDocByPath) {
    if (!docSection) return;
    Array.from(docSection.querySelectorAll(":scope > p")).forEach((pEl) => {
      pEl.hidden = true;
    });

    const graphData = extractGraphData(model);
    const c4 = buildC4Model(graphData);
    const v3HostId = "aaf-v3-tree-host";
    let v3Host = docSection.querySelector(`#${v3HostId}`);
    const nativeUl = Array.from(docSection.querySelectorAll(":scope > ul")).find((u) => u.id !== v3HostId);

    const searchInputEarly = docSection.querySelector('input[type="search"]');
    const queryEarly = (searchInputEarly?.value || "").trim();
    const shouldFormatNativeUl = (c4.isCompact && graphState.datasetMode === "workspace") || Boolean(queryEarly);
    if (nativeUl && shouldFormatNativeUl) {
      nativeUl.querySelectorAll(":scope > li > details").forEach((d, idx) => {
        if (idx < 4 && !d.dataset.aafInitOpen) {
          d.open = true;
          d.dataset.aafInitOpen = "1";
        }
      });
      nativeUl.querySelectorAll("summary").forEach((s) => {
        s.textContent = safeText(s.textContent || "");
      });
      nativeUl.querySelectorAll("li").forEach((li) => {
        const btn = li.querySelector(":scope > button");
        if (btn) {
          if (!btn.dataset.rawPath) btn.dataset.rawPath = (btn.textContent || "").trim();
          btn.textContent = safeText(btn.dataset.rawPath);
        }
        if (btn && !li.querySelector(".slot-badge")) {
          const p = (btn.textContent || "").trim();
          const meta = inferV3SlotMeta(p, "");
          const badge = el("span", `[${meta.slotCode}]`, "slot-badge", {
            "data-slot": meta.slotCode,
          });
          btn.after(badge);
        }
      });
    }

    if (c4.isCompact && graphState.datasetMode === "workspace") {
      if (v3Host) v3Host.hidden = true;
      if (nativeUl) nativeUl.hidden = false;
      return;
    }

    let controlsBar = docSection.querySelector(".aaf-tree-controls");
    if (!controlsBar) {
      controlsBar = el("div", "", "aaf-tree-controls");
      const ul = docSection.querySelector("ul");
      if (ul) ul.before(controlsBar);
      else docSection.append(controlsBar);
    }
    controlsBar.replaceChildren();

    const scopeHeader = el("div", "", "aaf-sidebar-scope-bar");
    const scopeTabs = el("div", "", "aaf-tree-actions-row");
    for (const [scKey, scEn, scVi] of [
      ["system", "C1 System", "C1 System"],
      ["container", "C2 Container", "C2 Container"],
      ["hg1", "HG-1 (9)", "HG-1 (9)"],
    ]) {
      const b = el("button", t(scEn, scVi), "aaf-tree-chip-btn", {
        type: "button",
        "aria-pressed": String(graphState.sidebarScope === scKey),
      });
      b.onclick = () => {
        graphState.sidebarScope = scKey;
        if (scKey === "system" && graphState.layoutMode === "c4-map" && graphState.c4Level !== "C1") {
          graphState.c4Level = "C1";
          graphState.selectedNodeId = graphState.c1FocusedSystem || "sys.omnipay-core";
          if (refreshGraph) refreshGraph();
        } else if (scKey === "container" && graphState.layoutMode === "c4-map" && graphState.c4Level === "C1") {
          graphState.c4Level = "C2";
          graphState.selectedNodeId = graphState.c4FocusedContainer || "ctr.payment-orchestrator";
          if (refreshGraph) refreshGraph();
        }
        enhanceLeftDocumentTree(docSection, model, reader, onSelectV3Node, refreshGraph, onOpenDocByPath);
      };
      scopeTabs.append(b);
    }
    scopeHeader.append(scopeTabs);
    controlsBar.append(scopeHeader);

    const row1 = el("div", "", "aaf-tree-actions-row");
    const expandAllBtn = el("button", t("Expand All", "Mở hết"), "aaf-tree-chip-btn", {
      type: "button",
    });
    const collapseAllBtn = el("button", t("Collapse All", "Thu gọn"), "aaf-tree-chip-btn", {
      type: "button",
    });
    expandAllBtn.onclick = () => {
      docSection.querySelectorAll("details").forEach((d) => {
        d.open = true;
      });
    };
    collapseAllBtn.onclick = () => {
      docSection.querySelectorAll("details").forEach((d) => {
        d.open = false;
      });
    };
    const clearFiltersBtn = el("button", t("Clear filters", "Xóa bộ lọc"), "aaf-tree-chip-btn", {
      type: "button",
    });
    clearFiltersBtn.onclick = () => {
      const sInp = docSection.querySelector('input[type="search"]');
      if (sInp && sInp.value) {
        sInp.value = "";
        sInp.dispatchEvent(new Event("input", { bubbles: true }));
      }
      graphState.slotFilter = "all";
      graphState.ownerFilter = "all";
      graphState.relationFilter = "all";
      graphState.c4GuidedFlow = "all";
      graphState.page = 0;
      enhanceLeftDocumentTree(docSection, model, reader, onSelectV3Node, refreshGraph, onOpenDocByPath);
      if (refreshGraph) refreshGraph();
    };
    row1.append(expandAllBtn, collapseAllBtn, clearFiltersBtn);
    controlsBar.append(row1);

    const searchInput = docSection.querySelector('input[type="search"]');
    const query = (searchInput?.value || "").trim().toLowerCase();

    if (!v3Host) {
      v3Host = el("div", "", "aaf-sidebar-custom-host", { id: v3HostId });
      docSection.append(v3Host);
    }

    if (query && graphState.datasetMode === "workspace") {
      if (nativeUl) nativeUl.hidden = false;
      v3Host.hidden = true;
      return;
    }

    if (nativeUl) nativeUl.hidden = true;
    v3Host.hidden = false;
    v3Host.replaceChildren();

    const handleOpenDoc = (docPath, docNode) => {
      if (graphState.datasetMode === "v3-maximal" && docNode) {
        onSelectV3Node(docNode);
      } else if (onOpenDocByPath) {
        onOpenDocByPath(docPath, docNode);
      } else if (docNode) {
        onSelectV3Node(docNode);
      }
    };

    if (graphState.sidebarScope === "system") {
      const allC1Systems = c4.c1Systems || [];
      const focusedSys =
        allC1Systems.find((s) => s.id === graphState.c1FocusedSystem) ||
        allC1Systems.find((s) => s.id === graphState.selectedNodeId) ||
        allC1Systems[0];

      const selWrap = el("div", "", "aaf-sidebar-ctr-selector");
      const selLabel = el("label", t("System / Actor:", "Hệ thống / Tác nhân:"));
      const selEl = el("select", "", "", {
        "aria-label": t("Select C1 System for Document Tree", "Chọn System ở C1 để xem tài liệu"),
      });
      for (const sysItem of allC1Systems) {
        const sModel = buildSystemDocTreeModel(sysItem, graphData, c4);
        const opt = el(
          "option",
          `${sysItem.title} (${sModel.allSystemDocs.length} ${t("specs", "tài liệu")} · ${sModel.arc42Groups.length} arc42)`,
          "",
          { value: sysItem.id }
        );
        opt.selected = focusedSys && sysItem.id === focusedSys.id;
        selEl.append(opt);
      }
      selEl.onchange = () => {
        graphState.c1FocusedSystem = selEl.value;
        graphState.selectedNodeId = selEl.value;
        const chosen = allC1Systems.find((s) => s.id === selEl.value);
        if (chosen && chosen.whitebox_doc) {
          handleOpenDoc(chosen.whitebox_doc.path, chosen.whitebox_doc);
        }
        enhanceLeftDocumentTree(docSection, model, reader, onSelectV3Node, refreshGraph, onOpenDocByPath);
        if (refreshGraph) refreshGraph();
      };
      selLabel.append(selEl);
      selWrap.append(selLabel);
      if (focusedSys) {
        const sysModel = buildSystemDocTreeModel(focusedSys, graphData, c4);
        selWrap.append(
          el(
            "small",
            `${sysModel.primaryDocs.length} ${t("direct", "trực tiếp")} · ${sysModel.relatedDocs.length} ${t("referenced", "tham chiếu")} · ${sysModel.allSystemDocs.length} ${t("unique specs", "tài liệu duy nhất")}`,
            "aaf-sidebar-stats mono"
          )
        );
      }
      v3Host.append(selWrap);

      if (focusedSys) {
        v3Host.append(renderSystemDocTreeDom(focusedSys, graphData, c4, handleOpenDoc));
      }
    } else if (graphState.sidebarScope === "hg1") {
      const clauseList = el("div", "", "aaf-hg1-clause-list");
      const clauses = graphData.clause_nodes || [];
      const docById = new Map((graphData.nodes || []).map((d) => [d.id, d]));
      for (const c of clauses) {
        const card = el("div", "", "aaf-hg1-clause-card");
        const head = el("div", "", "doc-graph-header");
        head.append(el("strong", `${c.id}`, "mono"), el("span", safeText(c.owner), "doc-graph-kpi mono"));
        card.append(head, el("p", c.summary || c.id));
        const relRow = el("div", "", "doc-graph-mode-group");
        const relatedIds = [c.artifact_id, ...(c.downstream || [])].filter(Boolean);
        const seenPaths = new Set();
        for (const rid of relatedIds) {
          const docNode = docById.get(rid);
          if (!docNode || seenPaths.has(docNode.path)) continue;
          seenPaths.add(docNode.path);
          const linkBtn = el("button", docNode.label || docNode.id, "doc-chip-btn", {
            type: "button",
            title: docNode.path,
          });
          linkBtn.onclick = () => handleOpenDoc(docNode.path, docNode);
          relRow.append(linkBtn);
        }
        card.append(relRow);
        clauseList.append(card);
      }
      v3Host.append(clauseList);
    } else {
      const allC2Nodes = [...(c4.c2Containers || []), ...(c4.c2Externals || [])];
      const focusedCtr =
        allC2Nodes.find((c) => c.id === graphState.c4FocusedContainer) ||
        allC2Nodes.find((c) => c.id === graphState.selectedNodeId) ||
        c4.c2Containers[1] ||
        c4.c2Containers[0];

      const selWrap = el("div", "", "aaf-sidebar-ctr-selector");
      const selLabel = el("label", t("Container:", "Container:"));
      const selEl = el("select", "", "", {
        "aria-label": t("Select Container for Document Tree", "Chọn Container ở C2 để xem tài liệu"),
      });
      for (const ctrItem of allC2Nodes) {
        const tModel = buildContainerDocTreeModel(ctrItem, graphData, c4);
        const opt = el(
          "option",
          `${ctrItem.title} (${tModel.ownedDocs.length} ${t("owned", "sở hữu")} · ${tModel.relatedDocs.length} ${t("linked", "liên kết")})`,
          "",
          { value: ctrItem.id }
        );
        opt.selected = focusedCtr && ctrItem.id === focusedCtr.id;
        selEl.append(opt);
      }
      selEl.onchange = () => {
        graphState.c4FocusedContainer = selEl.value;
        graphState.selectedNodeId = selEl.value;
        const chosen = allC2Nodes.find((c) => c.id === selEl.value);
        if (chosen && chosen.whitebox_doc) {
          handleOpenDoc(chosen.whitebox_doc.path, chosen.whitebox_doc);
        }
        enhanceLeftDocumentTree(docSection, model, reader, onSelectV3Node, refreshGraph, onOpenDocByPath);
        if (refreshGraph) refreshGraph();
      };
      selLabel.append(selEl);
      selWrap.append(selLabel);
      if (focusedCtr) {
        const treeModel = buildContainerDocTreeModel(focusedCtr, graphData, c4);
        const uniqueIds = new Set([
          ...treeModel.ownedDocs.map((d) => d.id),
          ...treeModel.relatedDocs.map((r) => r.doc.id),
        ]);
        selWrap.append(
          el(
            "small",
            `${treeModel.ownedDocs.length} ${t("owned", "sở hữu")} · ${treeModel.relatedDocs.length} ${t("referenced", "tham chiếu")} · ${uniqueIds.size} ${t("unique specs", "tài liệu duy nhất")}`,
            "aaf-sidebar-stats mono"
          )
        );
      }
      v3Host.append(selWrap);

      if (focusedCtr) {
        v3Host.append(renderContainerDocTreeDom(focusedCtr, graphData, c4, handleOpenDoc));
      }
    }
  }

  function enhanceDocumentReader(reader, model, onNavigatePath) {
    if (!reader) return false;
    if (reader.querySelector(".aaf-reader-header") || reader.querySelector(".aaf-reader-empty")) {
      return false;
    }
    const h3 = reader.querySelector("h3");
    const rawPre = reader.querySelector("pre");
    if (!h3) {
      const emptyBox = el("div", "", "aaf-reader-empty");
      emptyBox.append(
        el(
          "p",
          t(
            "Choose a document from the browser or map to read its specification here.",
            "Chọn tài liệu từ cây hoặc bản đồ để đọc nội dung tại đây."
          )
        )
      );
      reader.append(emptyBox);
      return true;
    }

    const docPath = (h3.dataset.rawPath || h3.textContent || "").trim();
    const graphData = extractGraphData(model);
    const v3Nodes = getMaximalV3CatalogueModel().document_graph.nodes || [];
    const nodeObj =
      (graphData.nodes || []).find((n) => n.path === docPath) ||
      v3Nodes.find((n) => n.path === docPath);
    if (nodeObj) {
      graphState.activeLeafPath = nodeObj.path;
      graphState.activeLeafNode = nodeObj;
    } else if (docPath) {
      graphState.activeLeafPath = docPath;
    }

    // Extract original metadata & revision before removing duplicate raw <p> elements 
    const rawParas = Array.from(reader.querySelectorAll(":scope > p"));
    const metaPara = rawParas.find((p) => !p.classList.contains("mono"));
    const revPara = rawParas.find((p) => p.classList.contains("mono"));
    const fullRev = (revPara?.textContent || nodeObj?.revision || "live").trim();
    const shortRev = fullRev.length > 10 ? fullRev.slice(0, 8) : fullRev;
    const rawMetaText = (metaPara?.textContent || "").trim();

    for (const pEl of rawParas) {
      if (pEl.textContent && pEl.textContent.includes("truncated")) continue;
      pEl.remove();
    }

    const existingProv = reader.querySelector(".aaf-provenance-banner");
    const isSynth = existingProv?.getAttribute("data-origin") === "synthetic" || graphState.datasetMode === "v3-maximal";
    const isCand = Boolean(model && model.change_id);
    const isPrev = window.__aafStandaloneCanvas === true;
    const originType = isSynth ? "synthetic" : isPrev ? "preview" : isCand ? "candidate" : "live";
    if (existingProv) existingProv.remove();

    const slotCode = nodeObj?.slot_code || inferV3SlotMeta(docPath, nodeObj?.kind || "").slotCode;
    const basename = docPath.split("/").pop() || docPath;
    const humanTitle = nodeObj?.display_title || humanizeSlug(basename);

    const headerBox = el("div", "", "aaf-reader-header");
    const metaRow = el("div", "", "aaf-reader-meta-row");
    const provLabel = isSynth
      ? t("Synthetic V3 Catalogue Template", "Mẫu danh mục V3 tổng hợp")
      : isPrev
      ? t("Preview sample · Read-only", "Bản xem thử · Chỉ đọc")
      : isCand
      ? t(`Candidate · ${model.change_id}`, `Dự thảo · ${model.change_id}`)
      : t("Live workspace source", "Nguồn thực tế đã đăng ký");

    metaRow.append(
      el("span", provLabel, "doc-graph-kpi aaf-provenance-banner", { "data-origin": originType }),
      el("span", `[${slotCode}]`, "slot-badge", { "data-slot": slotCode }),
      el("code", `rev: ${shortRev}`, "aaf-rev-short mono", { title: fullRev })
    );

    h3.dataset.rawPath = docPath;
    h3.textContent = safeText(humanTitle);
    h3.title = docPath;

    const subText = nodeObj
      ? `${basename} · ${nodeObj.id} · ${nodeObj.kind} · ${nodeObj.owner}`
      : `${basename} · ${rawMetaText}`;
    const subLine = el("p", subText, "aaf-reader-sub muted", { title: docPath });

    headerBox.append(metaRow, h3, subLine);
    reader.prepend(headerBox);

    if (rawPre) rawPre.textContent = safeText(rawPre.textContent || "");

    // Single compact Toolbar + Traceability Strip 
    const toolbar = el("div", "", "aaf-reader-toolbar");
    const modeGroup = el("div", "", "doc-graph-mode-group");
    const renderedBox = renderMarkdownToDom(rawPre ? rawPre.textContent || "" : "");
    const modeBtns = [];

    const applyMode = (mode) => {
      graphState.readerMode = mode;
      renderedBox.hidden = mode === "raw";
      if (rawPre) {
        rawPre.hidden = mode === "rendered";
      }
      for (const item of modeBtns) {
        item.btn.setAttribute("aria-pressed", String(item.key === mode));
      }
    };

    for (const [mKey, mEn, mVi] of [
      ["rendered", "Rendered", "Bản đọc"],
      ["raw", "Markdown", "Mã nguồn"],
      ["split", "Split", "Cả hai"],
    ]) {
      const btn = el("button", t(mEn, mVi), "doc-chip-btn", {
        type: "button",
        "aria-pressed": String(graphState.readerMode === mKey),
      });
      btn.onclick = () => applyMode(mKey);
      modeBtns.push({ key: mKey, btn });
      modeGroup.append(btn);
    }
    toolbar.append(modeGroup);

    const traceGroup = el("div", "", "doc-graph-mode-group");
    if (nodeObj) {
      for (const upId of (nodeObj.upstream_artifacts || []).slice(0, 2)) {
        const target = (graphData.nodes || []).find((n) => n.id === upId);
        if (target) {
          const b = el("button", `↑ ${target.id}`, "doc-chip-btn", {
            type: "button",
            title: target.path,
            "aria-label": `Open upstream document ${target.path}`,
          });
          b.onclick = () => onNavigatePath && onNavigatePath(target.path, target);
          traceGroup.append(b);
        }
      }
      for (const downId of (nodeObj.downstream_artifacts || []).slice(0, 2)) {
        const target = (graphData.nodes || []).find((n) => n.id === downId);
        if (target) {
          const b = el("button", `↓ ${target.id}`, "doc-chip-btn", {
            type: "button",
            title: target.path,
            "aria-label": `Open downstream document ${target.path}`,
          });
          b.onclick = () => onNavigatePath && onNavigatePath(target.path, target);
          traceGroup.append(b);
        }
      }
    }

    const sibInfo = getSiblingDocuments(nodeObj || docPath, graphData);
    if (sibInfo.siblings && sibInfo.siblings.length > 1) {
      const prevSib =
        sibInfo.siblings[
          (sibInfo.currentIndex - 1 + sibInfo.siblings.length) % sibInfo.siblings.length
        ];
      const nextSib =
        sibInfo.siblings[(sibInfo.currentIndex + 1) % sibInfo.siblings.length];
      const prevBtn = el("button", "←", "doc-chip-btn", {
        type: "button",
        title: prevSib ? prevSib.path : "",
        "aria-label": t("Previous sibling specification", "Tài liệu cùng cấp trước"),
      });
      prevBtn.onclick = () => prevSib && onNavigatePath && onNavigatePath(prevSib.path, prevSib);
      const nextBtn = el("button", "→", "doc-chip-btn", {
        type: "button",
        title: nextSib ? nextSib.path : "",
        "aria-label": t("Next sibling specification", "Tài liệu cùng cấp tiếp"),
      });
      nextBtn.onclick = () => nextSib && onNavigatePath && onNavigatePath(nextSib.path, nextSib);
      traceGroup.append(prevBtn, nextBtn);
    }

    if (traceGroup.childElementCount) {
      toolbar.append(traceGroup);
    }

    if (rawPre) {
      rawPre.before(toolbar, renderedBox);
      applyMode(graphState.readerMode);
    }
    return true;
  }

  function initWorkbenchEnhancer() {
    const main = document.getElementById("main");
    const coreModelEl = document.getElementById("core-model");
    if (!main || !coreModelEl) return;

    let currentModel = {};
    try {
      currentModel = JSON.parse(coreModelEl.textContent || "{}");
    } catch {
      currentModel = {};
    }

    const prevFetch = window.fetch;
    if (prevFetch && !window.__aafFetchWrapped) {
      window.__aafFetchWrapped = true;
      window.fetch = async function (input, ...args) {
        const urlStr = String(input || "");
        if (window.__aafStandaloneCanvas === true) {
          if (urlStr.includes("/api/runs")) {
            return new Response(JSON.stringify(currentModel.runs || { last_seq: 0, events: [] }), {
              status: 200,
              headers: { "Content-Type": "application/json" },
            });
          }
          if (urlStr.includes("/api/model")) {
            return new Response(JSON.stringify({ site: null, review: currentModel }), {
              status: 200,
              headers: { "Content-Type": "application/json" },
            });
          }
        }
        const response = await prevFetch.call(this, input, ...args);
        try {
          const url = String(input || "");
          if (url.includes("/api/model")) {
            const clone = response.clone();
            clone
              .json()
              .then((data) => {
                if (data && data.review) {
                  currentModel = data.review;
                }
              })
              .catch(() => {});
          }
        } catch {
          // ignore
        }
        return response;
      };
    }

    let enhancing = false;
    function syncStateFromUrlHash() {
      const params = new URLSearchParams(location.hash.slice(1));
      const c4Param = params.get("c4");
      if (c4Param && ["C1", "C2", "CONTAINER_DOCS"].includes(c4Param)) {
        graphState.c4Level = c4Param;
        graphState.sidebarScope = c4Param === "C1" ? "system" : "container";
      }
      const nodeParam = params.get("node");
      if (nodeParam) {
        graphState.selectedNodeId = nodeParam;
        if (nodeParam.startsWith("ctr.") || nodeParam.startsWith("ext.")) {
          graphState.c4FocusedContainer = nodeParam;
        } else if (nodeParam.startsWith("sys.") || nodeParam.startsWith("act.")) {
          graphState.c1FocusedSystem = nodeParam;
        }
      }
      const dsParam = params.get("dataset");
      if (dsParam && ["workspace", "v3-maximal"].includes(dsParam)) {
        graphState.datasetMode = dsParam;
      }
      const slotParam = params.get("slot");
      if (slotParam && ["all", "M", "S", "C", "D"].includes(slotParam)) {
        graphState.slotFilter = slotParam;
      }
    }
    syncStateFromUrlHash();
    window.addEventListener("hashchange", syncStateFromUrlHash);

    function enhanceCurrentMain() {
      if (enhancing) return;
      const route = new URLSearchParams(location.hash.slice(1)).get("view") || "overview";

      // Do NOT embed a duplicate C4 Architecture Map on Overview 
      if (route !== "documents") return;
      if (main.querySelector(".aaf-docs-workspace")) return;

      const reader = main.querySelector('section[aria-label="Document reader"]');
      const docSection = Array.from(main.querySelectorAll("section.card")).find(
        (s) => s !== reader && s.querySelector('input[type="search"]')
      );
      if (!docSection || !reader) return;

      enhancing = true;
      try {
        let refreshGraphFn = null;

        const renderMissingOrStaleSourceInReader = (targetPath, reasonMsg) => {
          reader.replaceChildren();
          const banner = el("div", "", "receipt aaf-provenance-banner", {
            "data-origin": "error",
            role: "alert",
          });
          banner.append(
            el("strong", t("Exact document source unavailable", "Không thể tải nguồn tài liệu chính xác")),
            el(
              "p",
              reasonMsg ||
                t(
                  `Source for "${targetPath}" could not be loaded from the workspace revision store. Synthetic templates are never substituted for live workspace documents.`,
                  `Không tìm thấy phiên bản nguồn của "${targetPath}" trong kho lưu trữ workspace. Hệ thống tuyệt đối không dùng mẫu giả lập để thay thế tài liệu thật.`
                )
            )
          );
          reader.append(banner);
        };

        const openV3NodeInReader = (nodeObj, originMode) => {
          if (!nodeObj) return;
          const mode =
            originMode ||
            (graphState.datasetMode === "v3-maximal"
              ? "synthetic"
              : window.__aafStandaloneCanvas === true
              ? "preview"
              : "live");
          if (mode === "live") {
            renderMissingOrStaleSourceInReader(nodeObj.path || nodeObj.id);
            return;
          }
          graphState.activeLeafPath = nodeObj.path;
          graphState.activeLeafNode = nodeObj;
          const mdText = synthesizeV3Markdown(nodeObj, mode);
          reader.replaceChildren();
          const provBanner = el("div", "", "receipt aaf-provenance-banner", {
            "data-origin": mode,
          });
          const h3El = el("h3", nodeObj.path);
          h3El.dataset.rawPath = nodeObj.path;
          reader.append(
            provBanner,
            h3El,
            el("p", `[${nodeObj.slot_code || "M"}] ${nodeObj.id} · ${nodeObj.kind} · ${nodeObj.owner}`),
            el("p", nodeObj.revision, "mono"),
            el("pre", mdText)
          );
          enhanceDocumentReader(reader, currentModel, (p, targetNode) => {
            if (targetNode) openV3NodeInReader(targetNode, mode);
          });
          if (refreshGraphFn) refreshGraphFn();
        };

        const triggerTreeDoc = (targetPath, nodeObj) => {
          if (graphState.datasetMode === "v3-maximal" && nodeObj) {
            openV3NodeInReader(nodeObj, "synthetic");
            return;
          }
          if (window.__aafStandaloneCanvas === true && nodeObj) {
            openV3NodeInReader(nodeObj, "preview");
            return;
          }
          const nativeTreeUl = Array.from(docSection.querySelectorAll(":scope > ul")).find(
            (u) => u.id !== "aaf-v3-tree-host"
          );
          const buttons = nativeTreeUl ? Array.from(nativeTreeUl.querySelectorAll("button")) : [];
          let btn = buttons.find(
            (b) =>
              (b.dataset.rawPath || b.textContent || "").trim() === targetPath ||
              (b.textContent || "").trim() === safeText(targetPath)
          );
          if (!btn && nativeTreeUl) {
            const searchInput = docSection.querySelector('input[type="search"]');
            if (searchInput && searchInput.value) {
              searchInput.value = "";
              searchInput.dispatchEvent(new Event("input", { bubbles: true }));
              const refreshedUl = Array.from(docSection.querySelectorAll(":scope > ul")).find(
                (u) => u.id !== "aaf-v3-tree-host"
              );
              btn = refreshedUl
                ? Array.from(refreshedUl.querySelectorAll("button")).find(
                    (b) => (b.dataset.rawPath || b.textContent || "").trim() === targetPath
                  )
                : null;
            }
          }
          if (btn) {
            btn.click();
            return;
          }
          const registeredArt = (currentModel.artifacts || []).find(
            (a) => a.path === targetPath || (nodeObj && a.id === nodeObj.id)
          );
          if (registeredArt && location.protocol.startsWith("http")) {
            const query = new URLSearchParams({
              id: registeredArt.id,
              revision: registeredArt.revision,
            });
            if (currentModel.change_id) query.set("change", currentModel.change_id);
            const artifactUrl = "/api/artifact?" + query.toString();
            fetch(artifactUrl)
              .then(async (res) => {
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
                reader.replaceChildren();
                reader.append(
                  el("h3", registeredArt.path),
                  el("p", `${registeredArt.id} · ${registeredArt.kind} · ${registeredArt.owner}`),
                  el("p", data.revision, "mono"),
                  el("pre", data.text)
                );
                if (data.has_more) {
                  reader.append(
                    el("p", "This display is truncated. Use the complete source before review.")
                  );
                }
                enhanceDocumentReader(reader, currentModel, (p, targetNode) =>
                  triggerTreeDoc(p, targetNode)
                );
              })
              .catch((err) => {
                renderMissingOrStaleSourceInReader(
                  targetPath,
                  err instanceof Error ? err.message : String(err)
                );
              });
          } else {
            renderMissingOrStaleSourceInReader(targetPath);
          }
        };

        const workspaceGrid = el("div", "", "aaf-docs-workspace");
        const leftCol = el("div", "", "aaf-docs-left-col");
        const centerCol = el("div", "", "aaf-docs-center-col");
        const rightCol = el("div", "", "aaf-docs-right-col");

        const { card: graphCard, refreshGraph } = buildDocumentGraphCard(
          currentModel,
          (targetPath, nodeObj) => {
            triggerTreeDoc(targetPath, nodeObj);
          },
          () => {
            enhanceLeftDocumentTree(docSection, currentModel, reader, openV3NodeInReader, refreshGraph, triggerTreeDoc);
            if (graphState.datasetMode === "v3-maximal") {
              const v3Nodes = getMaximalV3CatalogueModel().document_graph.nodes;
              const matched =
                (graphState.activeLeafPath &&
                  v3Nodes.find((n) => n.path === graphState.activeLeafPath)) ||
                (graphState.drillPath &&
                  v3Nodes.find((n) => n.path.startsWith(graphState.drillPath))) ||
                v3Nodes[0];
              if (matched) {
                graphState.activeLeafPath = matched.path;
                graphState.activeLeafNode = matched;
                openV3NodeInReader(matched);
              }
            }
          }
        );
        refreshGraphFn = refreshGraph;

        const browserDetails = el("details", "", "aaf-document-browser");
        browserDetails.open = window.matchMedia("(min-width: 1000px)").matches;
        browserDetails.append(el("summary", t("Browse documents", "Duyệt tài liệu")), docSection);
        leftCol.append(browserDetails);
        centerCol.append(graphCard);
        rightCol.append(reader);
        workspaceGrid.append(leftCol, centerCol, rightCol);
        main.append(workspaceGrid);

        enhanceLeftDocumentTree(docSection, currentModel, reader, openV3NodeInReader, refreshGraph, triggerTreeDoc);
        if (window.__aafStandaloneCanvas === true && !reader.querySelector("h3")) {
          const initGraph = extractGraphData(currentModel);
          const initDoc =
            (initGraph.nodes || []).find((n) => n.id === "API") || (initGraph.nodes || [])[0];
          if (initDoc) {
            openV3NodeInReader(initDoc);
          }
        }

        const searchInput = docSection.querySelector('input[type="search"]');
        if (searchInput) {
          searchInput.addEventListener("input", () => {
            window.setTimeout(() => {
              enhanceLeftDocumentTree(docSection, currentModel, reader, openV3NodeInReader, refreshGraph, triggerTreeDoc);
            }, 0);
          });
        }

        enhanceDocumentReader(reader, currentModel, (path, targetNode) => {
          triggerTreeDoc(path, targetNode);
        });

        if (reader.__aafObserver) {
          reader.__aafObserver.disconnect();
        }
        const readerObserver = new MutationObserver(() => {
          if (reader.querySelector(".aaf-reader-header") || reader.querySelector(".aaf-reader-empty")) {
            return;
          }
          const changed = enhanceDocumentReader(reader, currentModel, (path, targetNode) => {
            triggerTreeDoc(path, targetNode);
          });
          if (changed) {
            refreshGraph();
          }
        });
        readerObserver.observe(reader, { childList: true });
        reader.__aafObserver = readerObserver;

        if (graphState.pendingDocPath) {
          const pending = graphState.pendingDocPath;
          graphState.pendingDocPath = null;
          window.setTimeout(() => triggerTreeDoc(pending), 0);
        }
      } finally {
        enhancing = false;
      }
    }

    const mainObserver = new MutationObserver(() => {
      enhanceCurrentMain();
    });
    mainObserver.observe(main, { childList: true });
    enhanceCurrentMain();
  }

  function initReviewConsoleEnhancer() {
    const app = document.querySelector("[id=app]");
    if (!app || document.getElementById("main")) return;

    let enhancing = false;
    function enhanceReviewApp() {
      if (enhancing) return;
      if (typeof packet === "undefined" || !packet) return;
      if (app.querySelector(".doc-graph-card")) return;

      enhancing = true;
      try {
        const changesSection = Array.from(app.querySelectorAll("section")).find((s) => {
          const h2 = s.querySelector("h2");
          return (
            h2 &&
            (h2.textContent === "Changes from accepted baseline" ||
              h2.textContent === "Thay đổi so với bản đã duyệt")
          );
        });
        const { card: graphCard } = buildDocumentGraphCard(packet, (targetPath) => {
          if (!changesSection) return;
          const summary = Array.from(changesSection.querySelectorAll("details > summary")).find(
            (sum) => (sum.textContent || "").trim() === targetPath
          );
          if (summary && summary.parentElement) {
            summary.parentElement.open = true;
            summary.focus();
          }
        });
        if (changesSection) {
          changesSection.before(graphCard);
        } else {
          app.append(graphCard);
        }
      } finally {
        enhancing = false;
      }
    }

    const appObserver = new MutationObserver(() => {
      enhanceReviewApp();
    });
    appObserver.observe(app, { childList: true });
    enhanceReviewApp();
  }

  if (document.getElementById("main") && document.getElementById("core-model")) {
    initWorkbenchEnhancer();
  } else if (document.querySelector("[id=app]")) {
    initReviewConsoleEnhancer();
  }
})();
