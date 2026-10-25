from typing import List, Optional
from pydantic import BaseModel, Field


class DomainSkill(BaseModel):
    """
    Represents a single Horizontal Domain Skill (Role/Expertise).
    Aligned with ISO/IEC/IEEE 42010 Aspects and Concerns.
    """
    id: str = Field(..., description="Unique slug identifier (e.g. business-architect)")
    name: str = Field(..., description="Human-readable name")
    cluster_id: str = Field(..., description="Cluster ID (e.g. 01_business_architecture)")
    cluster_name: str = Field(..., description="Cluster Name")
    iso_aspects: List[str] = Field(..., description="ISO 42010 Architecture Aspects")
    concerns: List[str] = Field(default_factory=list, description="Primary stakeholder concerns addressed")
    viewpoints: List[str] = Field(default_factory=list, description="Associated architecture viewpoints")
    description: str = Field(..., description="Detailed scope of responsibility")
    recommended_patterns: List[str] = Field(default_factory=list, description="Relevant design pattern IDs")
    recommended_artifacts: List[str] = Field(default_factory=list, description="Relevant artifact template IDs")
    compatible_task_families: List[str] = Field(
        default_factory=list,
        description="Task family IDs most suitable to combine with this domain skill (e.g. 03_domain_modeling)"
    )



class DomainCluster(BaseModel):
    """
    Represents a Domain Cluster grouping multiple Domain Skills.
    """
    id: str = Field(..., description="Cluster ID (e.g. 01_business_architecture)")
    name: str = Field(..., description="Cluster Name")
    iso_aspect: str = Field(..., description="Primary ISO 42010 Aspect")
    description: str = Field(..., description="Cluster scope description")
    skills: List[DomainSkill] = Field(default_factory=list)
