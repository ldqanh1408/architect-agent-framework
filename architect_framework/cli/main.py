import argparse
import os
import sys
from pathlib import Path

# Ensure stdout/stderr handles UTF-8 formatting and symbols across platforms
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from architect_framework import contracts
from architect_framework.registry.domain_registry import DomainRegistry
from architect_framework.registry.task_registry import TaskRegistry
from architect_framework.registry.catalog_registry import CatalogRegistry
from architect_framework.registry.rule_registry import RuleRegistry
from architect_framework.orchestrator.matrix_orchestrator import MatrixOrchestrator
from architect_framework.orchestrator.consistency_checker import ConsistencyChecker
from architect_framework.orchestrator.atam_evaluator import ATAMEvaluator
from architect_framework.exporter.production_package_generator import SkillPackageGenerator
from architect_framework.models.correspondence import ArchitectureView
from architect_framework.models.atam import QualityScenario
from architect_framework.adapters.adapter_registry import AdapterRegistry



def main():
    parser = argparse.ArgumentParser(
        description="Architect Agent Framework CLI - ISO 42010 Aligned Matrix Orchestrator"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: list-skills
    parser_skills = subparsers.add_parser("list-skills", help="List available domain skills and clusters")
    parser_skills.add_argument("--cluster", type=str, help="Filter by cluster ID")

    # Command: list-tasks
    parser_tasks = subparsers.add_parser("list-tasks", help="List available task families and tasks")
    parser_tasks.add_argument("--family", type=str, help="Filter by task family ID")

    # Command: execute
    parser_exec = subparsers.add_parser("execute", help="Prepare a prompt from a domain skill and task")
    parser_exec.add_argument("--domain", type=str, required=True, help="Domain Skill ID (e.g. data-platform-architect)")
    parser_exec.add_argument("--task", type=str, required=True, help="Task Skill ID (e.g. schema-design)")
    parser_exec.add_argument("--tech", nargs="*", help="List of Technology KB IDs to bind (e.g. postgresql apache-kafka)")
    parser_exec.add_argument("--pattern", nargs="*", help="List of Pattern Catalog IDs to bind (e.g. cqrs transactional-outbox)")
    parser_exec.add_argument("--adapter", type=str, help="LLM Adapter target (e.g. claude, hermes, codex, openai, ollama, deepseek)")

    # Command: list-adapters
    parser_adapters = subparsers.add_parser("list-adapters", help="List all available LLM model adapters")


    # Command: export-skills
    parser_exp = subparsers.add_parser("export-skills", help="Export full SDD-equivalent skill packages (SKILL.md, skill-contract.yml, agents, references)")
    # No default. This command rewrites every package in the target directory,
    # so the destination is always a deliberate choice.
    parser_exp.add_argument("--outdir", type=str, required=True, help="Output directory path")
    parser_exp.add_argument("--force", action="store_true", help="Allow writing into a directory that already contains skill packages")
    parser_exp.add_argument(
        "--regenerate-skill-md",
        action="store_true",
        help="Reset every SKILL.md to template output, discarding authored bodies (destructive)",
    )

    # Command: check-consistency
    parser_cons = subparsers.add_parser(
        "check-consistency",
        help="Demonstrate the ISO 42010 correspondence rules on built-in sample views (reads no workspace)")

    # Command: atam-eval
    parser_atam = subparsers.add_parser("atam-eval", help="Run ATAM Trade-off Analysis evaluation demo")

    # Command: validate-contracts (GAP-010)
    parser_val = subparsers.add_parser("validate-contracts", help="Validate all skill-contract.yml files in exported_skills directory")
    parser_val.add_argument("--skilldir", type=str, default="exported_skills", help="Path to exported_skills directory")

    parser_packages = subparsers.add_parser("validate-packages", help="Run each exported package's fail-closed integrity validator")
    parser_packages.add_argument("--skilldir", type=str, default="exported_skills", help="Path to exported_skills directory")

    parser_manifest = subparsers.add_parser("validate-manifests", help="Validate package/release manifests, hashes, SBOM and provenance")
    parser_manifest.add_argument("--skilldir", type=str, default="exported_skills")

    parser_scenarios = subparsers.add_parser("validate-scenarios", help="Validate deterministic golden/adversarial scenario contracts")
    parser_scenarios.add_argument("--skilldir", type=str, default="exported_skills")

    parser_generate_check = subparsers.add_parser("generate-check", help="Fail if live exports differ from a fresh deterministic generation")
    parser_generate_check.add_argument("--skilldir", type=str, default="exported_skills")

    parser_release = subparsers.add_parser("release-check", help="Run the complete fail-closed release gate")
    parser_release.add_argument("--skilldir", type=str, default="exported_skills")

    parser_route = subparsers.add_parser("route-skills", help="Select one compatible domain/task pair without loading leaf skill bodies")
    parser_route.add_argument("--query", required=True)
    parser_route.add_argument("--domain")
    parser_route.add_argument("--task")
    parser_route.add_argument("--limit", type=int, default=5)
    parser_route.add_argument("--cluster", help="Restrict domain candidates to this cluster (G-A)")

    parser_design = subparsers.add_parser("design", help="Route a query and prepare a draft architecture document")
    parser_design.add_argument("--query", required=True, help="User prompt/request describing the architecture task")
    parser_design.add_argument("--domain", type=str, help="Optional domain skill ID override")
    parser_design.add_argument("--task", type=str, help="Optional task skill ID override")
    parser_design.add_argument("--out", type=str, default="architecture_design.md", help="Output .md file path (default: architecture_design.md)")

    # The gate registry CLI subcommands.
    # and `bootstrap` are registry introspection and belong with the registry.
    parser_gate = subparsers.add_parser("gate", help="Gate registry: a gate is an ID in contracts/gates.yml, never a file path")
    gate_sub = parser_gate.add_subparsers(dest="gate_command")
    gate_list = gate_sub.add_parser("list", help="List registered gates")
    gate_list.add_argument("--kind", choices=["subprocess", "native"], help="Filter by kind (`subprocess` or `native`); every read-only gate runs natively")
    gate_list.add_argument("--role", choices=["gate", "tool"], help="Filter by role")
    gate_list.add_argument("--scope", choices=["repo", "workspace", "catalog"], help="Filter by scope")
    gate_list.add_argument("--stage", choices=["ci", "manual"],
                           help="Filter by stage: `ci` gates check the repository and CI runs "
                                "them; `manual` gates run only when invoked")
    gate_list.add_argument("--over-suppressed", action="store_true",
                           help="List finding codes whose recorded suppressions reach the review "
                                "threshold, instead of gates")
    gate_list.add_argument("--ids-only", action="store_true", help="Print bare IDs, one per line")
    gate_boot = gate_sub.add_parser("bootstrap", help="Regenerate contracts/gates.yml from the scripts on disk")
    gate_boot.add_argument("--check", action="store_true", help="Fail if the file differs from a fresh derivation")
    gate_run = gate_sub.add_parser("run", help="Run gates by ID — one report, one exit code")
    gate_run.add_argument("gate_id", nargs="?", help="Gate ID; omit and use --scope or --all")
    gate_run.add_argument("workspace", nargs="?", help="Workspace root for workspace-scoped gates")
    gate_run.add_argument("--scope", choices=["repo", "workspace", "catalog"],
                          help="Run every read-only gate of this scope. "
                               "`--scope workspace <ws>` runs the whole workspace gate battery")
    gate_run.add_argument("--stage", choices=["ci", "manual"],
                          help="Run every gate of this stage: `ci` is the repository and "
                               "catalogue battery CI runs; `manual` gates need an explicit input")
    gate_run.add_argument("--all", action="store_true", help="Run every read-only gate")
    gate_run.add_argument("--catalog", help="Catalog root (default: <repo>/exported_skills)")
    gate_run.add_argument("--against", metavar="DIR",
                          help="Materialized workspace root for a catalog gate that supports "
                               "--against (e.g. GATE-SLOT-COVERAGE)")
    gate_run.add_argument("--json", action="store_true", help="Emit the report as JSON")
    gate_run.add_argument("--log", metavar="PATH",
                          help="Also write a canonical JSON run log and print its sha256 — the "
                               "citation a closing report quotes (W-40)")
    gate_run.add_argument("--update-baseline", action="store_true",
                          help="Write <workspace>/gate-baseline.yml from this run's warning "
                               "counts; later runs fail if a count rises (warning ratchet)")
    gate_run.add_argument("--check", action="store_true",
                          help="Regenerate-and-diff: fail if the workspace artifact differs from a "
                               "fresh derivation. Native gates already check unconditionally; this "
                               "flag is accepted so checklist Verify argv is valid")
    gate_run.add_argument("--include-writers", action="store_true",
                          help="Also run gates declared side_effects: writes. They modify files.")
    gate_explain = gate_sub.add_parser("explain", help="Which gate emits a finding code, and how to run it")
    gate_explain.add_argument("code", help="A finding code, e.g. TREE-specification")

    from architect_framework.runtime import cli as runtime_cli
    runtime_cli.register(subparsers)
    # Top-level `skills` command alias; uses the same handler as `runtime skills`.
    runtime_cli.register_skills(subparsers, runtime_cli.workspace_arg)
    from architect_framework import tools as tier_d_tools
    tier_d_tools.register(subparsers)
    from architect_framework.console import cli as console_cli
    console_cli.register(subparsers)

    args = parser.parse_args()

    if args.command == "runtime":
        sys.exit(runtime_cli.run(args))
    if args.command == "skills":
        sys.exit(runtime_cli._skills(args))
    if args.command == "tool":
        sys.exit(tier_d_tools.run(args))
    if args.command == "console":
        sys.exit(console_cli.run(args))

    if args.command == "list-skills":
        reg = DomainRegistry()
        print(f"=== HORIZONTAL DOMAIN SKILLS ({len(reg.list_all_skills())} SKILLS / {len(reg.list_all_clusters())} CLUSTERS) ===")
        for cluster in reg.list_all_clusters():
            if args.cluster and args.cluster != cluster.id:
                continue
            print(f"\nCluster: {cluster.name} [{cluster.id}]")
            print(f"ISO Aspect: {cluster.iso_aspect}")
            for skill in cluster.skills:
                print(f"  - {skill.id} ({skill.name})")

    elif args.command == "list-tasks":
        reg = TaskRegistry()
        print(f"=== VERTICAL TASK SKILLS ({len(reg.list_all_families())} TASK FAMILIES) ===")
        for family in reg.list_all_families():
            if args.family and args.family != family.id:
                continue
            print(f"\nFamily: {family.name} [{family.id}]")
            print(f"Activity: {family.core_activity}")
            for task in family.tasks:
                print(f"  - {task.id} ({task.name})")

    elif args.command == "execute":
        domain_reg = DomainRegistry()
        task_reg = TaskRegistry()

        # GAP-011: Friendly error messages with suggestions
        domain_skill = domain_reg.get_skill(args.domain)
        if not domain_skill:
            available = [s.id for s in domain_reg.list_all_skills()]
            print(f"[ERROR] Domain skill '{args.domain}' not found.", file=sys.stderr)
            suggestions = [s for s in available if args.domain.split("-")[0] in s][:5]
            if suggestions:
                print(f"[HINT] Did you mean one of: {', '.join(suggestions)}", file=sys.stderr)
            else:
                print(f"[HINT] Run 'list-skills' to see all available domain skill IDs.", file=sys.stderr)
            sys.exit(1)

        task_skill = task_reg.get_task(args.task)
        if not task_skill:
            available = [t.id for fam in task_reg.list_all_families() for t in fam.tasks]
            print(f"[ERROR] Task skill '{args.task}' not found.", file=sys.stderr)
            suggestions = [t for t in available if args.task.split("-")[0] in t][:5]
            if suggestions:
                print(f"[HINT] Did you mean one of: {', '.join(suggestions)}", file=sys.stderr)
            else:
                print(f"[HINT] Run 'list-tasks' to see all available task skill IDs.", file=sys.stderr)
            sys.exit(1)

        orchestrator = MatrixOrchestrator(
            domain_registry=domain_reg,
            task_registry=task_reg,
        )
        try:
            context = orchestrator.resolve_execution_point(
                domain_skill_id=args.domain,
                task_skill_id=args.task,
                bound_tech_ids=args.tech,
                bound_pattern_ids=args.pattern,
            )
        except ValueError as exc:
            print(f"[ERROR] {exc}", file=sys.stderr)
            sys.exit(1)

        if args.adapter:
            try:
                import json
                adapter = AdapterRegistry.get_adapter(args.adapter)
                adapter_out = adapter.format_context(context)
                print(f"=== LLM ADAPTER OUTPUT ({adapter_out.adapter_name.upper()}) ===")
                print(f"Provider: {adapter_out.provider} | Target Model: {adapter_out.model_name}")
                print("\n[FORMATTED API PAYLOAD]:")
                print(json.dumps(adapter_out.formatted_payload, indent=2))
            except ValueError as exc:
                print(f"[ERROR] {exc}", file=sys.stderr)
                sys.exit(1)
        else:
            print("=== GENERATED AGENT SYSTEM PROMPT ===")
            print(context.system_prompt)

    elif args.command == "list-adapters":
        print("=== SUPPORTED LLM MODEL ADAPTERS ===")
        for adapter_name in AdapterRegistry.list_adapters():
            adapter = AdapterRegistry.get_adapter(adapter_name)
            cfg = adapter.get_config()
            print(f"- {adapter_name.ljust(10)}: Provider={cfg.provider.ljust(12)} Model={cfg.model_name.ljust(30)} Format={cfg.system_prompt_format}")

    elif args.command == "export-skills":
        out_path = Path(args.outdir)
        existing = len(list(out_path.rglob("SKILL.md"))) if out_path.is_dir() else 0
        if existing and not args.force:
            print(
                f"refusing to write into '{out_path.resolve()}': it already contains {existing} skill packages.\n"
                "Every package there will be rebuilt. Re-run with --force once that is what you want.",
                file=sys.stderr,
            )
            sys.exit(1)
        if args.regenerate_skill_md and existing:
            print(
                f"warning: --regenerate-skill-md will overwrite {existing} authored SKILL.md bodies with template output.",
                file=sys.stderr,
            )
        generator = SkillPackageGenerator(regenerate_skill_md=args.regenerate_skill_md)
        total = generator.generate_all_packages(out_path)
        preserved = "" if args.regenerate_skill_md else " (authored SKILL.md bodies preserved)"
        print(f"Successfully generated {total} production-grade skill packages in '{out_path.resolve()}'{preserved}")

    elif args.command == "design":
        orchestrator = MatrixOrchestrator()
        try:
            context, doc_md = orchestrator.auto_design_markdown(
                query=args.query,
                domain_skill_id=args.domain,
                task_skill_id=args.task,
            )
            out_path = Path(args.out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(doc_md, encoding="utf-8", newline="\n")
            print(f"=== ARCHITECT SKILL ORCHESTRATOR ===")
            print(f"[STATUS]: Auto-routed & Generated Architecture Specification (.md)")
            print(f"[MATRIX POINT]: {context.execution_point.matrix_id}")
            print(f"[SELECTED DOMAIN]: {context.domain_skill.name} ({context.domain_skill.id})")
            print(f"[SELECTED TASK]: {context.task_skill.name} ({context.task_skill.id})")
            print(f"[SAVED ARTIFACT]: {out_path.resolve()}")
        except Exception as exc:
            print(f"[ERROR] {exc}", file=sys.stderr)
            sys.exit(1)



    elif args.command == "check-consistency":
        # specification / T18: a model ran this as an audit of a workspace and got "16/16 passed" for a repo
        # with no views at all. The views below are a built-in example; the output says so first.
        print("check-consistency: the 16 correspondence rules on BUILT-IN SAMPLE views. "
              "It reads no workspace; a pass here says nothing about your documents.")
        checker = ConsistencyChecker()
        # GAP-001 Fix: Include all required Viewpoints so all Correspondence Rules can be evaluated
        sample_views = {
            "Bounded Context Viewpoint": ArchitectureView(
                viewpoint_id="Bounded Context Viewpoint",
                elements=[{"id": "OrderContext", "name": "Order Management Context"}],
            ),
            "C4 Container Viewpoint": ArchitectureView(
                viewpoint_id="C4 Container Viewpoint",
                elements=[{"id": "Order Service Container", "source_id": "OrderContext", "name": "Order Service Container"}],
            ),
            "Tactical DDD Viewpoint": ArchitectureView(
                viewpoint_id="Tactical DDD Viewpoint",
                elements=[{"id": "Order", "name": "Order Aggregate Root"}],
            ),
            "Database Viewpoint": ArchitectureView(
                viewpoint_id="Database Viewpoint",
                elements=[{"source_id": "Order", "name": "orders_table"}],
            ),
            "API Viewpoint": ArchitectureView(
                viewpoint_id="API Viewpoint",
                elements=[{"id": "POST /orders", "name": "Create Order API"}],
            ),
            "IAM Viewpoint": ArchitectureView(
                viewpoint_id="IAM Viewpoint",
                elements=[{"source_id": "POST /orders", "name": "JWT Bearer Auth"}],
            ),
            # GAP-001 Fix: Infrastructure Viewpoint — id field defined so Cost/Network Policy viewpoints can match via source_id
            "Infrastructure Viewpoint": ArchitectureView(
                viewpoint_id="Infrastructure Viewpoint",
                elements=[{
                    "id": "Order Service K8s Deployment",
                    "source_id": "Order Service Container",
                    "name": "Order Service K8s Deployment",
                    "cpu_limit": "500m",
                    "memory_limit": "512Mi"
                }],
            ),
            # CR-005: Event Viewpoint + Message Broker Viewpoint
            "Event Viewpoint": ArchitectureView(
                viewpoint_id="Event Viewpoint",
                elements=[{"id": "OrderPlacedEvent", "name": "Order Placed Domain Event"}],
            ),
            "Message Broker Viewpoint": ArchitectureView(
                viewpoint_id="Message Broker Viewpoint",
                elements=[{"source_id": "OrderPlacedEvent", "name": "orders.placed Kafka topic"}],
            ),
            # CR-006: Cost Viewpoint
            "Cost Viewpoint": ArchitectureView(
                viewpoint_id="Cost Viewpoint",
                elements=[{"source_id": "Order Service K8s Deployment", "name": "Order Service monthly cost estimate $120"}],
            ),
            # CR-007: SLO Viewpoint + Observability Viewpoint
            "SLO Viewpoint": ArchitectureView(
                viewpoint_id="SLO Viewpoint",
                elements=[{"id": "SLO-API-P99", "name": "Order API p99 < 200ms SLO"}],
            ),
            "Observability Viewpoint": ArchitectureView(
                viewpoint_id="Observability Viewpoint",
                elements=[{"source_id": "SLO-API-P99", "name": "order_api_latency_p99 Prometheus alert"}],
            ),
            # CR-008: Threat Model Viewpoint + Security Control Viewpoint
            "Threat Model Viewpoint": ArchitectureView(
                viewpoint_id="Threat Model Viewpoint",
                elements=[{"id": "THREAT-001", "name": "Spoofing via stolen JWT token"}],
            ),
            "Security Control Viewpoint": ArchitectureView(
                viewpoint_id="Security Control Viewpoint",
                elements=[{"source_id": "THREAT-001", "name": "Short-lived JWT + mTLS enforcement"}],
            ),
            # CR-009: AsyncAPI Viewpoint
            "AsyncAPI Viewpoint": ArchitectureView(
                viewpoint_id="AsyncAPI Viewpoint",
                elements=[{"source_id": "POST /orders", "name": "asyncapi-order-service.yml"}],
            ),
            # CR-010: Deployment Viewpoint + Rollback Viewpoint
            "Deployment Viewpoint": ArchitectureView(
                viewpoint_id="Deployment Viewpoint",
                elements=[{"id": "DEPLOY-001", "name": "Order Service Canary Deployment"}],
            ),
            "Rollback Viewpoint": ArchitectureView(
                viewpoint_id="Rollback Viewpoint",
                elements=[{"source_id": "DEPLOY-001", "name": "ArgoCD automated rollback on >5% error rate"}],
            ),
            # CR-011: Context Map Viewpoint + Integration Pattern Viewpoint
            "Context Map Viewpoint": ArchitectureView(
                viewpoint_id="Context Map Viewpoint",
                elements=[{"id": "OrderCtx->PaymentCtx", "name": "Order to Payment context relationship"}],
            ),
            "Integration Pattern Viewpoint": ArchitectureView(
                viewpoint_id="Integration Pattern Viewpoint",
                elements=[{"source_id": "OrderCtx->PaymentCtx", "name": "Customer-Supplier with Anti-Corruption Layer"}],
            ),
            # CR-012: AI Agent Viewpoint + Guardrail Viewpoint
            "AI Agent Viewpoint": ArchitectureView(
                viewpoint_id="AI Agent Viewpoint",
                elements=[{"id": "AgentOrchestrator", "name": "Architect AI Orchestrator Agent"}],
            ),
            "Guardrail Viewpoint": ArchitectureView(
                viewpoint_id="Guardrail Viewpoint",
                elements=[{"source_id": "AgentOrchestrator", "name": "Input/Output STRIDE guardrail rules"}],
            ),
            # CR-013: Data Schema Viewpoint + Compliance Viewpoint
            "Data Schema Viewpoint": ArchitectureView(
                viewpoint_id="Data Schema Viewpoint",
                elements=[{"id": "user_pii_field", "name": "User Email PII field in orders table"}],
            ),
            "Compliance Viewpoint": ArchitectureView(
                viewpoint_id="Compliance Viewpoint",
                elements=[{"source_id": "user_pii_field", "name": "AES-256 encryption, 7-year retention, GDPR compliant"}],
            ),
            # CR-014: Data Pipeline Viewpoint
            "Data Pipeline Viewpoint": ArchitectureView(
                viewpoint_id="Data Pipeline Viewpoint",
                elements=[{"source_id": "Order", "name": "Order CDC -> Debezium -> Kafka -> Analytics DB"}],
            ),
            # CR-015: Network Policy Viewpoint
            "Network Policy Viewpoint": ArchitectureView(
                viewpoint_id="Network Policy Viewpoint",
                elements=[{"source_id": "Order Service K8s Deployment", "name": "NetworkPolicy: allow ingress from gateway only"}],
            ),
            # CR-016: Disaster Recovery Viewpoint
            "Disaster Recovery Viewpoint": ArchitectureView(
                viewpoint_id="Disaster Recovery Viewpoint",
                elements=[{"source_id": "SLO-API-P99", "name": "RTO=15min RPO=1min cross-region failover plan"}],
            ),
        }
        results = checker.validate_views(sample_views)
        print("=== ISO 42010 CORRESPONDENCE CHECK RESULTS ===")
        passed_count = sum(1 for r in results if r.passed)
        total_count = len(results)
        for r in results:
            status = "PASSED" if r.passed else "FAILED"
            print(f"Rule [{r.rule_id}] ({r.source_viewpoint} -> {r.target_viewpoint}): {status}")
            for v in r.violations:
                print(f"  - Violation: {v}")
        print(f"\nSummary: {passed_count}/{total_count} rules passed.")
        if passed_count < total_count:
            sys.exit(1)

    elif args.command == "atam-eval":
        evaluator = ATAMEvaluator()
        scenarios = [
            QualityScenario(
                id="SCENARIO-PERF-01",
                quality_attribute="Performance Efficiency",
                source="Peak Load Event",
                stimulus="5,000 req/sec payment requests",
                environment="Production Peak",
                artifact="Payment Service",
                response="Process requests cleanly",
                response_measure="p99 latency < 500ms, error rate < 0.01%",
            )
        ]
        decisions = [
            {
                "decision": "Enforce mTLS and JWT validation on every inter-service hop",
                "positives": ["Security - Confidentiality", "Zero Trust Policy"],
                "negatives": ["Performance - Latency (+15ms per hop)", "CPU Overhead"],
                "recommendation": "Use persistent HTTP/2 connections to reuse mTLS handshakes.",
                "sensitivities": [
                    {
                        "variable": "TLS Handshake Reuse",
                        "attribute": "Latency",
                        "description": "Connection pool size directly dictates handshake CPU overhead.",
                    }
                ],
            }
        ]
        report = evaluator.analyze_tradeoffs(scenarios, decisions)
        print("=== ATAM TRADEOFF EVALUATION REPORT ===")
        print(f"Title: {report.title}")
        print(f"Summary: {report.summary_recommendation}\n")
        print("Tradeoff Points:")
        for tp in report.tradeoff_points:
            print(f"  - Decision: {tp.decision}")
            print(f"    Positive: {', '.join(tp.positive_impact)}")
            print(f"    Negative: {', '.join(tp.negative_impact)}")
            print(f"    Recommendation: {tp.recommendation}")

    elif args.command == "validate-contracts":
        # GAP-010: Validate skill-contract.yml files
        import yaml as _yaml
        skill_dir = Path(args.skilldir)
        contract_files = list(skill_dir.rglob("skill-contract.yml"))
        if not contract_files:
            print(f"[ERROR] No skill-contract.yml files found in '{skill_dir}'.", file=sys.stderr)
            sys.exit(1)

        errors = []
        from architect_framework.orchestrator.skill_router import ORCHESTRATOR_SKILL_ID
        expected_ids = {ORCHESTRATOR_SKILL_ID} | {skill.id for skill in DomainRegistry().list_all_skills()} | {task.id for task in TaskRegistry().list_all_tasks()}
        actual_ids = {path.parent.name for path in contract_files}
        if actual_ids != expected_ids:
            errors.append(f"  Registry coverage mismatch: missing={sorted(expected_ids-actual_ids)}, extra={sorted(actual_ids-expected_ids)}")
        required_keys = {"schema_version", "skill", "kind", "role", "triggers", "anti_triggers", "required_inputs", "optional_inputs", "forbidden_inputs", "owns", "read_only", "forbidden_writes", "required_outputs", "completion_evidence", "blocking_conditions", "resume_policy", "context_loading", "engineering_discipline", "validators"}
        for cf in contract_files:
            try:
                with open(cf, "r", encoding="utf-8") as f:
                    data = _yaml.safe_load(f)
                missing = required_keys - set(data.keys())
                if missing:
                    errors.append(f"  [{cf.parent.name}] Missing keys: {', '.join(missing)}")
                if data.get("schema_version") != "2026.07":
                    errors.append(f"  [{cf.parent.name}] Unsupported schema_version: {data.get('schema_version')}")
                if data.get("skill") != cf.parent.name:
                    errors.append(f"  [{cf.parent.name}] Contract skill does not match package path")
                for key in ("triggers", "required_inputs", "owns", "required_outputs", "completion_evidence", "blocking_conditions", "validators"):
                    if not isinstance(data.get(key), list) or not data[key]:
                        errors.append(f"  [{cf.parent.name}] {key} must be a non-empty list")
                if data.get("resume_policy", {}).get("complete_only_after_postflight") is not True:
                    errors.append(f"  [{cf.parent.name}] completion is not postflight-derived")
                discipline = data.get("engineering_discipline", {})
                for key in ("think_before_action", "simplicity_first", "surgical_scope", "goal_driven_execution"):
                    if not isinstance(discipline.get(key), dict) or not discipline[key]:
                        errors.append(f"  [{cf.parent.name}] missing engineering discipline: {key}")
            except Exception as e:
                errors.append(f"  [{cf}] Parse error: {e}")

        print(f"=== SKILL CONTRACT VALIDATION ({len(contract_files)} files) ===")
        if errors:
            print(f"[FAILED] {len(errors)} contract(s) failed validation:")
            for err in errors:
                print(err)
            sys.exit(1)
        else:
            print(f"[PASSED] All {len(contract_files)} skill-contract.yml files are valid.")

    elif args.command == "validate-packages":
        import subprocess
        from architect_framework.validation.release import is_core_tree

        skill_dir = Path(args.skilldir)
        if is_core_tree(skill_dir):
            packages = sorted(path.parent for path in skill_dir.rglob("SKILL.md") if (path.parent / "skill-contract.yml").is_file())
        else:
            packages = sorted(path.parent for path in skill_dir.rglob("skill-contract.yml"))
        if not packages:
            print(f"[ERROR] No skill packages found in '{skill_dir}'.", file=sys.stderr)
            sys.exit(1)
        # One validator for the whole catalog. It used to be copied into every
        # package; the copies differed by a single constant.
        validator = skill_dir / "_shared" / "scripts" / "check_skill_package.py"
        if not validator.is_file():
            print(f"[ERROR] Missing {validator}; no package can be validated without it.", file=sys.stderr)
            sys.exit(1)
        failures = []
        for package in packages:
            result = subprocess.run(
                [sys.executable, str(validator), str(package)],
                capture_output=True,
                text=True, encoding="utf-8", errors="replace",
                shell=False,
            )
            if result.returncode != 0:
                failures.append(f"{package}: {result.stdout.strip()} {result.stderr.strip()}".strip())
        print(f"=== SKILL PACKAGE VALIDATION ({len(packages)} packages) ===")
        if failures:
            print(f"[FAILED] {len(failures)} package(s) failed:")
            for failure in failures:
                print(f"  - {failure}")
            sys.exit(1)
        print(f"[PASSED] All {len(packages)} skill packages passed the shared validator.")

    elif args.command == "validate-manifests":
        from architect_framework.validation.release import ReleaseValidationError, is_core_tree, validate_core_tree, validate_release_manifest
        skill_dir = Path(args.skilldir)
        if is_core_tree(skill_dir):
            try:
                slots = validate_core_tree(skill_dir)
            except ReleaseValidationError as exc:
                print(f"[FAILED] {exc}", file=sys.stderr)
                sys.exit(1)
            print(f"[PASSED] Core tree manifests validated across {slots} slots (4 free packages + slot descriptors).")
            sys.exit(0)
        try:
            manifest = validate_release_manifest(skill_dir)
        except ReleaseValidationError as exc:
            print(f"[FAILED] {exc}", file=sys.stderr)
            sys.exit(1)
        print(f"[PASSED] Release and package manifests cover {manifest['package_count']} packages with verified hashes.")

    elif args.command == "validate-scenarios":
        from architect_framework.evaluation.harness import ScenarioValidationError, validate_scenario_tree
        from architect_framework.validation.release import is_core_tree
        skill_dir = Path(args.skilldir)
        try:
            count = validate_scenario_tree(skill_dir)
        except ScenarioValidationError as exc:
            print(f"[FAILED] {exc}", file=sys.stderr)
            sys.exit(1)
        print(f"[PASSED] {count} deterministic scenario contracts are valid.")

    elif args.command == "generate-check":
        from architect_framework.validation.release import ReleaseValidationError, compare_with_fresh_generation
        try:
            compare_with_fresh_generation(Path(args.skilldir))
        except ReleaseValidationError as exc:
            print(f"[FAILED] {exc}", file=sys.stderr)
            sys.exit(1)
        print("[PASSED] Live exports are byte-identical to a fresh deterministic generation.")

    elif args.command == "release-check":
        import subprocess
        from architect_framework.evaluation.harness import ScenarioValidationError, validate_scenario_tree
        from architect_framework.validation.release import ReleaseValidationError, compare_with_fresh_generation, validate_release_manifest
        skill_dir = Path(args.skilldir)
        from architect_framework.validation.release import is_core_tree, validate_core_tree
        if is_core_tree(skill_dir):
            # The public tree: every slot, without bundled pack content or release manifest.
            try:
                slots = validate_core_tree(skill_dir)
            except ReleaseValidationError as exc:
                print(f"[FAILED] {exc}", file=sys.stderr)
                sys.exit(1)
            print(f"[PASSED] Release gate (core tree, no pack): {slots} slots match the registry; "
                  "contents and the release manifest belong to the pack.")
            sys.exit(0)
        try:
            manifest = validate_release_manifest(skill_dir)
            scenario_count = validate_scenario_tree(skill_dir)
            packages = sorted(path.parent for path in skill_dir.rglob("skill-contract.yml"))
            validator = skill_dir / "_shared" / "scripts" / "check_skill_package.py"
            if not validator.is_file():
                raise ReleaseValidationError(f"missing shared validator: {validator}")
            failures = []
            for package in packages:
                result = subprocess.run([sys.executable, str(validator), str(package)], capture_output=True, text=True, encoding="utf-8", shell=False)
                if result.returncode != 0:
                    failures.append(f"{package}: {result.stdout.strip()} {result.stderr.strip()}".strip())
            if failures:
                raise ReleaseValidationError("package validation failed: " + "; ".join(failures))
            compare_with_fresh_generation(skill_dir)
        except (ReleaseValidationError, ScenarioValidationError) as exc:
            print(f"[FAILED] {exc}", file=sys.stderr)
            sys.exit(1)
        print(f"[PASSED] Release gate: {manifest['package_count']} packages, {scenario_count} scenario contracts, all manifests/hashes/validators valid, live tree fresh.")

    elif args.command == "route-skills":
        import json
        from architect_framework.orchestrator.skill_router import ProgressiveSkillRouter, RoutingError
        try:
            decision = ProgressiveSkillRouter().route(args.query, args.domain, args.task, args.limit, args.cluster, open_families=True)
        except RoutingError as exc:
            print(json.dumps({"status": "blocked", "reason": str(exc)}, sort_keys=True), file=sys.stderr)
            sys.exit(1)
        from architect_framework import skillpacks

        out = decision.to_dict()
        # Check whether the selected skills have content to run with, and if not,
        # what fills them — the router names the owner, the slot says if it can act.
        out["slots"] = [skillpacks.slot_view(s) for s in (out.get("selected_domain"), out.get("selected_task")) if s]
        print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
        if decision.status != "selected":
            sys.exit(2)

    elif args.command == "gate":
        from architect_framework.gates import bootstrap as gate_bootstrap
        from architect_framework.gates import registry as gate_registry

        if args.gate_command == "bootstrap":
            if args.check:
                ok, message = gate_bootstrap.check()
                print(message)
                sys.exit(0 if ok else 1)
            print(f"wrote {gate_bootstrap.write()}")
            gate_registry.clear_cache()
            open_items = gate_bootstrap.problems(list(gate_registry.raw_entries()),
                                                 list(gate_registry.retired().values()))
            if open_items:
                # Written anyway — the derived fields are right — but `--check`
                # stays red until every code is classified.
                print(f"{len(open_items)} registry problem(s); `gate bootstrap --check` will fail:")
                for item in open_items[:20]:
                    print(f"  {item}")

        elif args.gate_command == "list":
            try:
                entries = gate_registry.raw_entries()
            except gate_registry.RegistryError as exc:
                print(f"gate registry error: {exc}", file=sys.stderr)
                sys.exit(1)
            if args.over_suppressed:
                # The suppression register has one reader, the gate that
                # validates it; asking that gate by ID keeps this command from
                # growing a second parser for the same file.
                import subprocess as _subprocess

                from architect_framework.gates.subprocess_gate import _utf8_env

                gate = gate_registry.get("GATE-SUPPRESSIONS")
                proc = _subprocess.run(
                    [sys.executable, str(gate.resolved_entrypoint(gate_registry.REPO_ROOT)),
                     "--over-threshold"] + (["--ids-only"] if args.ids_only else []),
                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                    env=_utf8_env(), cwd=str(gate_registry.REPO_ROOT),
                )
                sys.stdout.write(proc.stdout)
                sys.stderr.write(proc.stderr)
                sys.exit(proc.returncode)
            rows = [
                e
                for e in entries
                if (not args.kind or str(e.get("kind")) == args.kind)
                and (not args.role or str(e.get("role", "gate")) == args.role)
                and (not args.scope or str(e.get("scope", "repo")) == args.scope)
                and (not args.stage or str(e.get("stage") or "") == args.stage)
            ]
            if args.ids_only:
                for entry in rows:
                    print(entry["id"])
            else:
                for entry in rows:
                    g_obj = gate_registry.get(str(entry["id"]))
                    resolved = g_obj.exists(gate_registry.REPO_ROOT) if hasattr(g_obj, "exists") else (gate_registry.REPO_ROOT / str(entry["entrypoint"])).is_file()
                    mark = " " if resolved else "!"
                    print(
                        f"{mark} {entry['id']:<40} {entry.get('kind',''):<11}"
                        f"{entry.get('role',''):<6}{entry.get('scope',''):<11}{entry['entrypoint']}"
                    )
            unresolved = gate_registry.unresolved()
            if unresolved:
                print(f"\n! {len(unresolved)} entrypoint(s) do not resolve: {', '.join(unresolved)}", file=sys.stderr)
                sys.exit(1)

        elif args.gate_command == "run":
            from architect_framework.gates.runner import run_selection

            gate_id, workspace = args.gate_id, args.workspace
            # Both positionals are optional, so argparse binds the first one to
            # `gate_id`. With --phase, --scope or --all there is no gate ID to
            # give, and the single positional is the workspace.
            if (args.all or args.scope or args.stage) and gate_id and not workspace:
                gate_id, workspace = None, gate_id
            sys.exit(
                run_selection(
                    gate_id=gate_id,
                    workspace=workspace,
                    run_all=args.all,
                    catalog=args.catalog,
                    as_json_output=args.json,
                    include_writers=args.include_writers,
                    against=args.against,
                    log=args.log,
                    update_baseline=args.update_baseline,
                    scope=args.scope,
                    stage=args.stage,
                    check=getattr(args, "check", False),
                )
            )

        elif args.gate_command == "explain":
            code = args.code.strip()
            index = gate_registry.findings_owners()
            owners = index.get(code) or index.get(code.upper()) or []
            owner = owners[0] if owners else None
            if not owner:
                near = sorted({c for c in index if code.upper() in c.upper()})
                print(f"no registered gate declares finding {code!r}", file=sys.stderr)
                if near:
                    print(f"near matches: {', '.join(near[:8])}", file=sys.stderr)
                else:
                    print(
                        "Finding codes are derived from each gate's source. If this code is real "
                        "and missing, the derivation in architect_framework/gates/bootstrap.py "
                        "needs widening — do not hand-add it to contracts/gates.yml.",
                        file=sys.stderr,
                    )
                sys.exit(1)
            entry = next(e for e in gate_registry.raw_entries() if e["id"] == owner)
            code = code if code in (entry.get("findings") or []) else code.upper()
            print(f"{code}")
            print(f"  emitted by  {', '.join(owners)}")
            print(f"  entrypoint  {entry['entrypoint']}")
            print(f"  scope       {entry.get('scope')}    phase {entry.get('phase') or '(unassigned)'}")
            # How the finding is proven, whether it can fail a
            # run, and what to do about it — per emitter, since two gates may
            # prove the same code differently.
            for other in owners:
                meta = gate_registry.code_meta(other, code)
                klass = meta.get("class") or "(unclassified — counts toward the exit code)"
                counted = "counts toward the exit code" if gate_registry.is_blocking(other, code) \
                    else "a note; does not change the exit code"
                label = f" [{other}]" if len(owners) > 1 else ""
                print(f"  class{label:<6} {klass} — {counted}")
                if meta.get("remedy"):
                    print(f"  remedy{label:<5} {meta['remedy']}")
            for other in owners:
                print(f"  run it      architect-cli gate run {other} <workspace>")
            siblings = [c for c in (entry.get("findings") or []) if c != code]
            if siblings:
                print(f"  siblings    {', '.join(siblings[:10])}")

        else:
            parser_gate.print_help()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
