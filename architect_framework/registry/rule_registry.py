from pathlib import Path
from typing import List, Dict, Optional
from architect_framework.registry import _yaml as yaml
from architect_framework.models.correspondence import CorrespondenceRule


class RuleRegistry:
    """
    Registry for ISO 42010 Correspondence Rules.
    """

    def __init__(self, data_path: Optional[Path] = None):
        if data_path is None:
            data_path = Path(__file__).parent.parent / "data" / "correspondence_rules.yaml"
        self.data_path = data_path
        self.rules: Dict[str, CorrespondenceRule] = {}
        self.load_rules()

    def load_rules(self):
        if self.data_path.exists():
            with open(self.data_path, "r", encoding="utf-8") as f:
                raw_data = yaml.safe_load(f) or {}
                for item in raw_data.get("rules", []):
                    rule = CorrespondenceRule(**item)
                    if rule.id in self.rules:
                        raise ValueError(f"Duplicate correspondence rule ID: '{rule.id}'")
                    self.rules[rule.id] = rule

    def get_rule(self, rule_id: str) -> Optional[CorrespondenceRule]:
        return self.rules.get(rule_id)

    def list_all_rules(self) -> List[CorrespondenceRule]:
        return list(self.rules.values())

    def get_rules_for_viewpoint(self, viewpoint: str) -> List[CorrespondenceRule]:
        vp_lower = viewpoint.lower()
        return [
            r for r in self.rules.values()
            if vp_lower in r.source_viewpoint.lower() or vp_lower in r.target_viewpoint.lower()
        ]
