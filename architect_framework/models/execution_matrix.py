from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from architect_framework.models.domain_skill import DomainSkill
from architect_framework.models.task_skill import TaskTechnicalItem, TaskFamily
from architect_framework.models.catalogs import PatternItem, ArtifactTemplate, TechKBItem


class ExecutionPoint(BaseModel):
    """
    Represents an Execution Point E_{i,j} = Domain_i x Task_j in the matrix.
    """
    domain_skill_id: str
    task_skill_id: str
    matrix_id: str = Field(..., description="E.g. E[data-platform-architect, data-design]")

    def get_matrix_key(self) -> str:
        return f"{self.domain_skill_id}::{self.task_skill_id}"


class OrchestrationContext(BaseModel):
    """
    Full context generated for an Agent performing E_{i,j}.
    Includes bound domain skill, task skill, matched patterns, artifact templates, and tech attributes.
    """
    execution_point: ExecutionPoint
    domain_skill: DomainSkill
    task_skill: TaskTechnicalItem
    task_family: TaskFamily
    bound_patterns: List[PatternItem] = Field(default_factory=list)
    bound_artifact_templates: List[ArtifactTemplate] = Field(default_factory=list)
    bound_tech_items: List[TechKBItem] = Field(default_factory=list)
    system_prompt: str = Field("", description="Dynamically generated Agent System Prompt")

    def generate_prompt(self) -> str:
        """
        Generates the standard structured prompt for the agent.
        """
        patterns_str = "\n".join([f"- **{p.name}**: {p.solution}" for p in self.bound_patterns]) or "None specified."
        artifacts_str = "\n".join([f"- **{a.name}** ({a.format_type})" for a in self.bound_artifact_templates]) or "Standard Architecture Spec."
        tech_str = "\n".join([f"- **{t.name}**: {t.nfr_attributes}" for t in self.bound_tech_items]) or "Generic technology selection."
        steps_str = "\n".join([f"{i+1}. {step}" for i, step in enumerate(self.task_skill.procedural_steps)])
        outputs_str = "\n".join([f"- {out}" for out in self.task_skill.expected_outputs])

        prompt = f"""# AGENT ROLE: {self.domain_skill.name} [{self.domain_skill.id}]
## Cluster: {self.domain_skill.cluster_name} (ISO Aspects: {', '.join(self.domain_skill.iso_aspects)})
### Domain Scope:
{self.domain_skill.description}

---

# ARCHITECTURAL TASK: {self.task_skill.name} [{self.task_skill.id}]
## Task Family: {self.task_family.name} ({self.task_family.core_activity})

### Procedural Thinking & Execution Steps:
{steps_str}

### Expected Outputs & Artifact Deliverables:
{outputs_str}

---

# AUXILIARY KNOWLEDGE & CATALOG BINDINGS

## Relevant Architecture Patterns (Pattern Catalog):
{patterns_str}

## Deliverable Formatting Standards (Artifact Catalog):
{artifacts_str}

## Declarative Technology Knowledge Base Attributes (Tech KB):
{tech_str}

---

# EXECUTION RULE & ISO 42010 COMPLIANCE:
- Perform the task strictly following procedural steps.
- Ensure all output formats strictly adhere to specified Artifact templates.
- Maintain consistency with dependent viewpoints via Correspondence Rules.
"""
        self.system_prompt = prompt
        return prompt
