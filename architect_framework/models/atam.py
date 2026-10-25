from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class QualityScenario(BaseModel):
    """
    ISO 25010 / ATAM Quality Attribute Scenario.
    """
    id: str = Field(..., description="Scenario ID (e.g. SCENARIO-PERF-01)")
    quality_attribute: str = Field(..., description="ISO 25010 attribute (e.g. Performance, Security, Reliability)")
    source: str = Field(..., description="Stimulus source (e.g. 5x spike in user traffic)")
    stimulus: str = Field(..., description="Stimulus condition")
    environment: str = Field(..., description="Operational environment (e.g. Normal operations, Peak sales)")
    artifact: str = Field(..., description="Target system component")
    response: str = Field(..., description="Required system behavior")
    response_measure: str = Field(..., description="Measurable metric (e.g. latency < 500ms, 99.99% uptime)")


class TradeoffPoint(BaseModel):
    """
    ATAM Tradeoff Point where a decision affects multiple attributes positively and negatively.
    """
    decision: str = Field(..., description="Architecture decision (e.g. Enable mTLS everywhere)")
    positive_impact: List[str] = Field(..., description="Quality attributes improved (e.g. Security)")
    negative_impact: List[str] = Field(..., description="Quality attributes degraded (e.g. Latency, CPU Overhead)")
    recommendation: str = Field(..., description="Mitigation or final balanced recommendation")


class SensitivityPoint(BaseModel):
    """
    ATAM Sensitivity Point where small changes in architecture dramatically alter a quality attribute.
    """
    variable: str = Field(..., description="Parameter/Variable (e.g. DB connection pool size)")
    affected_quality_attribute: str = Field(..., description="Primary affected attribute (e.g. Throughput)")
    sensitivity_description: str = Field(..., description="Explanation of sensitivity")


class ATAMEvaluationReport(BaseModel):
    """
    Complete report of ATAM Tradeoff Analysis.
    """
    title: str = Field(..., description="Evaluation Report Title")
    scenarios: List[QualityScenario] = Field(default_factory=list)
    tradeoff_points: List[TradeoffPoint] = Field(default_factory=list)
    sensitivity_points: List[SensitivityPoint] = Field(default_factory=list)
    summary_recommendation: str = Field(..., description="Final architectural verdict")
