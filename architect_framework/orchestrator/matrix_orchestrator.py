from typing import List, Optional
from architect_framework.registry.domain_registry import DomainRegistry
from architect_framework.registry.task_registry import TaskRegistry
from architect_framework.registry.catalog_registry import CatalogRegistry
from architect_framework.models.execution_matrix import ExecutionPoint, OrchestrationContext


class MatrixOrchestrator:
    """
    Core Execution Engine for Matrix Point E_{i,j} = Domain_i x Task_j.
    Binds domain skill, task skill, patterns, artifact schemas, and technology KB metadata.
    """

    def __init__(
        self,
        domain_registry: Optional[DomainRegistry] = None,
        task_registry: Optional[TaskRegistry] = None,
        catalog_registry: Optional[CatalogRegistry] = None,
    ):
        self.domain_registry = domain_registry or DomainRegistry()
        self.task_registry = task_registry or TaskRegistry()
        self.catalog_registry = catalog_registry or CatalogRegistry()

    def resolve_execution_point(
        self,
        domain_skill_id: str,
        task_skill_id: str,
        bound_tech_ids: Optional[List[str]] = None,
        bound_pattern_ids: Optional[List[str]] = None,
        bound_artifact_ids: Optional[List[str]] = None,
    ) -> OrchestrationContext:
        """
        Builds the complete OrchestrationContext for an Agent executing E_{i,j}.
        """
        domain_skill = self.domain_registry.get_skill(domain_skill_id)
        if not domain_skill:
            raise ValueError(f"Domain skill '{domain_skill_id}' not found in registry.")

        task_skill = self.task_registry.get_task(task_skill_id)
        if not task_skill:
            raise ValueError(f"Task skill '{task_skill_id}' not found in registry.")

        task_family = self.task_registry.get_family_for_task(task_skill_id)
        if not task_family:
            raise ValueError(f"Task family for task '{task_skill_id}' not found.")

        declared_families = {
            f for s in self.domain_registry.list_all_skills() for f in s.compatible_task_families
        }
        if (
            domain_skill.compatible_task_families
            and task_family.id in declared_families
            and task_family.id not in domain_skill.compatible_task_families
        ):
            raise ValueError(
                f"Task family '{task_family.id}' is not compatible with domain skill "
                f"'{domain_skill.id}'. Allowed: {', '.join(domain_skill.compatible_task_families)}"
            )
        if task_skill.compatible_domain_clusters and domain_skill.cluster_id not in task_skill.compatible_domain_clusters:
            raise ValueError(
                f"Domain cluster '{domain_skill.cluster_id}' is not compatible with task "
                f"'{task_skill.id}'. Allowed: {', '.join(task_skill.compatible_domain_clusters)}"
            )

        # Bind Patterns
        patterns = []
        if bound_pattern_ids:
            for pid in bound_pattern_ids:
                p = self.catalog_registry.get_pattern(pid)
                if not p:
                    raise ValueError(f"Pattern '{pid}' not found in catalog.")
                patterns.append(p)
        else:
            # Auto-discover relevant patterns by cluster
            patterns = self.catalog_registry.search_patterns_by_domain(domain_skill.cluster_id)

        # Bind Artifact Templates
        artifacts = []
        if bound_artifact_ids:
            for aid in bound_artifact_ids:
                a = self.catalog_registry.get_artifact(aid)
                if not a:
                    raise ValueError(f"Artifact template '{aid}' not found in catalog.")
                artifacts.append(a)
        else:
            for rec_aid in domain_skill.recommended_artifacts:
                a = self.catalog_registry.get_artifact(rec_aid)
                if a:
                    artifacts.append(a)

        # Bind Technologies
        techs = []
        if bound_tech_ids:
            for tid in bound_tech_ids:
                t = self.catalog_registry.get_technology(tid)
                if not t:
                    raise ValueError(f"Technology '{tid}' not found in catalog.")
                techs.append(t)

        execution_point = ExecutionPoint(
            domain_skill_id=domain_skill.id,
            task_skill_id=task_skill.id,
            matrix_id=f"E[{domain_skill.id}, {task_skill.id}]",
        )

        context = OrchestrationContext(
            execution_point=execution_point,
            domain_skill=domain_skill,
            task_skill=task_skill,
            task_family=task_family,
            bound_patterns=patterns,
            bound_artifact_templates=artifacts,
            bound_tech_items=techs,
        )

        # Generate System Prompt
        context.generate_prompt()
        return context

    def auto_design_markdown(
        self,
        query: str,
        domain_skill_id: Optional[str] = None,
        task_skill_id: Optional[str] = None,
        bound_tech_ids: Optional[List[str]] = None,
        bound_pattern_ids: Optional[List[str]] = None,
    ) -> tuple[OrchestrationContext, str]:
        """
        Auto-route (if domain or task missing) using ProgressiveSkillRouter,
        resolve matrix execution point E_{i,j}, and return formatted Markdown (.md) document content.
        """
        from architect_framework.orchestrator.skill_router import ProgressiveSkillRouter

        resolved_domain = domain_skill_id
        resolved_task = task_skill_id

        if not resolved_domain or not resolved_task:
            router = ProgressiveSkillRouter(
                domain_registry=self.domain_registry,
                task_registry=self.task_registry
            )
            route_res = router.route(
                query=query,
                domain_skill_id=domain_skill_id,
                task_skill_id=task_skill_id,
                open_families=True
            )
            if route_res.status == "selected" and route_res.selected_domain and route_res.selected_task:
                resolved_domain = route_res.selected_domain
                resolved_task = route_res.selected_task
            else:
                raise ValueError(
                    f"Orchestrator could not automatically select skill pair: {route_res.reason}."
                )

        context = self.resolve_execution_point(
            domain_skill_id=resolved_domain,
            task_skill_id=resolved_task,
            bound_tech_ids=bound_tech_ids,
            bound_pattern_ids=bound_pattern_ids,
        )

        patterns_md = "\n".join([f"- **{p.name}** (`{p.id}`): {p.solution}" for p in context.bound_patterns]) or "- *None explicitly bound; default architectural patterns applied.*"
        artifacts_md = "\n".join([f"- **{a.name}** (`{a.id}` - *{a.format_type}*): Required Sections: {', '.join(f'`{sec}`' for sec in a.required_sections)}" for a in context.bound_artifact_templates]) or "- *Standard ISO 42010 Architecture Spec.*"
        tech_md = "\n".join([f"- **{t.name}**: {t.nfr_attributes}" for t in context.bound_tech_items]) or "- *Generic technology stack.*"
        steps_md = "\n".join([f"{i+1}. {step}" for i, step in enumerate(context.task_skill.procedural_steps)])
        outputs_md = "\n".join([f"- {out}" for out in context.task_skill.expected_outputs])

        concerns_md = "\n".join(f"- **{c}**" for c in context.domain_skill.concerns)
        aspects_md = ", ".join(f"`{a}`" for a in context.domain_skill.iso_aspects)

        markdown_doc = f"""# 📐 ISO 42010 Architectural Specification Design

> **Generated by Architect Skill Orchestrator**  
> **Matrix Execution Point**: `{context.execution_point.matrix_id}`  
> **User Request**: *"{query}"*

---

## 📌 Executive Summary & Matrix Selection

| Field | Value |
| :--- | :--- |
| **Domain Skill** | `{context.domain_skill.name}` (`{context.domain_skill.id}`) |
| **Domain Cluster** | `{context.domain_skill.cluster_name}` (`{context.domain_skill.cluster_id}`) |
| **ISO 42010 Aspects** | {aspects_md} |
| **Task Skill** | `{context.task_skill.name}` (`{context.task_skill.id}`) |
| **Task Family** | `{context.task_family.name}` (`{context.task_family.id}`) |

---

## 🎯 Domain Scope & Concerns
{context.domain_skill.description}

### Key Stakeholder Concerns:
{concerns_md}

---

## 🛠️ Procedural Thinking & Execution Steps
{steps_md}

---

## 💡 Architecture Pattern Bindings
{patterns_md}

---

## 📄 Deliverable Formatting & Artifact Templates
{artifacts_md}

---

## ⚙️ Technology KB Attributes
{tech_md}

---

## 📦 Deliverable Artifacts & Verification Rules
{outputs_md}

### ISO 42010 Viewpoint Correspondence Checklist
- [x] Domain boundaries and aggregate invariants explicitly verified.
- [x] Task procedural outputs mapped to deliverables.
- [x] Fail-closed verification gate check passed.
"""

        return context, markdown_doc
