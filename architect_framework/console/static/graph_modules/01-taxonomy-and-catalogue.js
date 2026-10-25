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

