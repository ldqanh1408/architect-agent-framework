from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class PatternItem(BaseModel):
    """
    Represents an architectural/design pattern in Pattern Catalog (~200 patterns).
    """
    id: str = Field(..., description="Pattern identifier (e.g. cqrs, saga, circuit-breaker)")
    name: str = Field(..., description="Pattern name")
    category: str = Field(..., description="Category (e.g. Integration, Resiliency, Data, AI)")
    problem: str = Field(..., description="Problem description solved by pattern")
    solution: str = Field(..., description="Solution design summary")
    tradeoffs: List[str] = Field(default_factory=list, description="Architectural tradeoffs and consequences")
    applicable_domains: List[str] = Field(default_factory=list, description="Domain cluster IDs applicable")


class ArtifactTemplate(BaseModel):
    """
    Represents an artifact formatting standard in Artifact Catalog (~100 artifacts).
    """
    id: str = Field(..., description="Artifact template ID (e.g. c4-container-spec, nygard-adr)")
    name: str = Field(..., description="Artifact Name")
    format_type: str = Field(..., description="Format (Markdown, Mermaid, PlantUML, OpenAPI, JSON Schema)")
    structure_schema: str = Field(..., description="Markdown structure template or schema definition")
    required_sections: List[str] = Field(default_factory=list, description="Mandatory document sections")


class TechKBItem(BaseModel):
    """
    Represents a technology entity in Technology KB (~300+ tech items).
    Declarative knowledge without procedural steps.
    """
    id: str = Field(..., description="Tech ID (e.g. postgresql, apache-kafka, redis, qdrant)")
    name: str = Field(..., description="Technology Name")
    category: str = Field(..., description="Tech Category (Database, Message Queue, Cache, Vector DB, Cloud)")
    nfr_attributes: Dict[str, Any] = Field(default_factory=dict, description="Performance, throughput, latency, ACID guarantees")
    operational_limits: List[str] = Field(default_factory=list, description="Known scaling or operational boundaries")
    cost_model: Optional[str] = Field(None, description="Licensing and cost characteristics")
    best_used_for: List[str] = Field(default_factory=list, description="Recommended use cases")
