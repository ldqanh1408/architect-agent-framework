from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TaskTechnicalItem(BaseModel):
    """
    Represents a specific procedural technical task within a Task Family.
    """
    id: str = Field(..., description="Unique slug identifier (e.g. requirement-analysis)")
    name: str = Field(..., description="Technical Task Name")
    description: str = Field(..., description="Procedural task description")
    procedural_steps: List[str] = Field(..., description="Sequential mental or engineering steps")
    expected_outputs: List[str] = Field(..., description="Deliverable artifacts or specifications")
    inputs_required: List[str] = Field(default_factory=list, description="Contextual inputs needed")
    compatible_domain_clusters: List[str] = Field(
        default_factory=list,
        description="Domain cluster IDs most suitable to combine with this task (e.g. 02_domain_architecture)"
    )


class TaskFamily(BaseModel):
    """
    Represents a Vertical Task Family (Procedural Knowledge).
    """
    id: str = Field(..., description="Family ID (e.g. 01_discovery)")
    name: str = Field(..., description="Task Family Name")
    core_activity: str = Field(..., description="Core engineering activity")
    expected_technical_output: str = Field(..., description="High-level deliverable summary")
    tasks: List[TaskTechnicalItem] = Field(default_factory=list, description="Sub-tasks in family")
