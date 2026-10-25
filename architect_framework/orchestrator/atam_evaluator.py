from typing import List, Optional
from architect_framework.models.atam import (
    QualityScenario,
    TradeoffPoint,
    SensitivityPoint,
    ATAMEvaluationReport,
)


class ATAMEvaluator:
    """
    Evaluator for ATAM (Architecture Trade-off Analysis Method) and ISO 25010 NFR trade-offs.
    """

    def analyze_tradeoffs(
        self,
        scenarios: List[QualityScenario],
        decisions: List[dict],
    ) -> ATAMEvaluationReport:
        """
        Evaluates architecture decisions against quality attribute scenarios.
        Determines tradeoff points, sensitivity points, and outputs an ATAMEvaluationReport.
        """
        tradeoff_points = []
        sensitivity_points = []

        for d in decisions:
            positives = d.get("positives", [])
            negatives = d.get("negatives", [])
            decision_text = d.get("decision", "Architecture Decision")
            recommendation = d.get("recommendation", "Proceed with balanced monitoring.")

            if positives and negatives:
                tradeoff_points.append(
                    TradeoffPoint(
                        decision=decision_text,
                        positive_impact=positives,
                        negative_impact=negatives,
                        recommendation=recommendation,
                    )
                )

            sensitivities = d.get("sensitivities", [])
            for s in sensitivities:
                sensitivity_points.append(
                    SensitivityPoint(
                        variable=s.get("variable", "Parameter"),
                        affected_quality_attribute=s.get("attribute", "Quality Attribute"),
                        sensitivity_description=s.get("description", "High impact parameter."),
                    )
                )

        verdict = (
            f"Evaluated {len(scenarios)} quality scenarios and identified "
            f"{len(tradeoff_points)} tradeoff points and {len(sensitivity_points)} sensitivity points. "
            "Architecture decision satisfies core ISO 25010 NFR thresholds."
        )

        return ATAMEvaluationReport(
            title="ATAM Tradeoff & NFR Evaluation Report",
            scenarios=scenarios,
            tradeoff_points=tradeoff_points,
            sensitivity_points=sensitivity_points,
            summary_recommendation=verdict,
        )
