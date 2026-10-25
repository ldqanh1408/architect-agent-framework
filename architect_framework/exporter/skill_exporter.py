from pathlib import Path
from typing import Optional
from architect_framework.registry.domain_registry import DomainRegistry
from architect_framework.registry.task_registry import TaskRegistry
from architect_framework.registry.catalog_registry import CatalogRegistry


class SkillExporter:
    """
    Deprecated compatibility shim. Standalone flat Markdown exports are no longer
    supported because they create a second, stale source of authority.
    """

    def __init__(
        self,
        domain_registry: Optional[DomainRegistry] = None,
        task_registry: Optional[TaskRegistry] = None,
        catalog_registry: Optional[CatalogRegistry] = None,
    ):
        self.domain_registry = domain_registry or DomainRegistry(include_installed=False)
        self.task_registry = task_registry or TaskRegistry(include_installed=False)
        self.catalog_registry = catalog_registry or CatalogRegistry()

    def export_all(self, output_dir: Path) -> int:
        """
        Exports domain skills and task skills to output_dir.
        Returns total number of exported skill files.
        """
        raise RuntimeError(
            "Flat skill export is retired; use SkillPackageGenerator.generate_all_packages()"
        )
        output_dir = Path(output_dir)  # pragma: no cover - retained only for source compatibility
        domains_dir = output_dir / "domains"
        tasks_dir = output_dir / "tasks"

        domains_dir.mkdir(parents=True, exist_ok=True)
        tasks_dir.mkdir(parents=True, exist_ok=True)

        count = 0

        # Export Domain Skills
        for cluster in self.domain_registry.list_all_clusters():
            cluster_dir = domains_dir / cluster.id
            cluster_dir.mkdir(parents=True, exist_ok=True)

            for skill in cluster.skills:
                file_path = cluster_dir / f"{skill.id}.md"
                content = f"""---
id: "{skill.id}"
name: "{skill.name}"
cluster_id: "{skill.cluster_id}"
iso_aspects: {skill.iso_aspects}
concerns: {skill.concerns}
viewpoints: {skill.viewpoints}
---

# DOMAIN ARCHITECT SKILL: {skill.name}

## 📌 Cluster Context:
- **Cluster**: {skill.cluster_name}
- **ISO 42010 Aspects**: {', '.join(skill.iso_aspects)}
- **Viewpoints**: {', '.join(skill.viewpoints)}
- **Key Concerns**: {', '.join(skill.concerns)}

## 🎯 Role & Responsibility:
{skill.description}

## 💡 Recommended Architecture Patterns:
"""
                patterns = self.catalog_registry.search_patterns_by_domain(cluster.id)
                for p in patterns:
                    content += f"- **{p.name}** (`{p.id}`): {p.solution}\n"

                content += "\n## 📐 ISO 42010 Viewpoint Compliance:\n"
                content += "- Ensure view components produced explicitly address stakeholder concerns.\n"
                content += "- Maintain correspondence mappings to dependent architecture views.\n"

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                count += 1

        # Export Task Skills
        for family in self.task_registry.list_all_families():
            family_dir = tasks_dir / family.id
            family_dir.mkdir(parents=True, exist_ok=True)

            for task in family.tasks:
                file_path = family_dir / f"{task.id}.md"
                steps_str = "\n".join([f"{i+1}. {step}" for i, step in enumerate(task.procedural_steps)])
                outputs_str = "\n".join([f"- {out}" for out in task.expected_outputs])

                content = f"""---
id: "{task.id}"
name: "{task.name}"
family_id: "{family.id}"
family_name: "{family.name}"
---

# TASK ARCHITECT SKILL: {task.name}

## 📌 Task Family Context:
- **Family**: {family.name}
- **Core Engineering Activity**: {family.core_activity}
- **Expected High-Level Deliverable**: {family.expected_technical_output}

## 🧠 Procedural Thinking Steps:
{steps_str}

## 📄 Expected Artifact Outputs:
{outputs_str}
"""
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                count += 1

        return count
