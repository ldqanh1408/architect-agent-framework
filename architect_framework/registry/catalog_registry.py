from pathlib import Path
from typing import List, Dict, Optional
from architect_framework.registry._yaml import safe_load
from architect_framework.models.catalogs import PatternItem, ArtifactTemplate, TechKBItem


class CatalogRegistry:
    """
    Registry for Auxiliary Libraries: Pattern Catalog, Artifact Catalog, Technology KB.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        self.data_dir = data_dir
        self.patterns: Dict[str, PatternItem] = {}
        self.artifacts: Dict[str, ArtifactTemplate] = {}
        self.technologies: Dict[str, TechKBItem] = {}
        self.load_catalogs()

    def load_catalogs(self):
        pattern_file = self.data_dir / "pattern_catalog.yaml"
        if pattern_file.exists():
            with open(pattern_file, "r", encoding="utf-8") as f:
                raw_patterns = safe_load(f)
                for item in raw_patterns.get("patterns", []):
                    pattern = PatternItem(**item)
                    if pattern.id in self.patterns:
                        raise ValueError(f"Duplicate pattern ID: {pattern.id}")
                    self.patterns[pattern.id] = pattern

        artifact_file = self.data_dir / "artifact_catalog.yaml"
        if artifact_file.exists():
            with open(artifact_file, "r", encoding="utf-8") as f:
                raw_artifacts = safe_load(f)
                for item in raw_artifacts.get("templates", []):
                    artifact = ArtifactTemplate(**item)
                    if artifact.id in self.artifacts:
                        raise ValueError(f"Duplicate artifact ID: {artifact.id}")
                    self.artifacts[artifact.id] = artifact

        tech_file = self.data_dir / "technology_kb.yaml"
        if tech_file.exists():
            with open(tech_file, "r", encoding="utf-8") as f:
                raw_tech = safe_load(f)
                for item in raw_tech.get("technologies", []):
                    tech = TechKBItem(**item)
                    if tech.id in self.technologies:
                        raise ValueError(f"Duplicate technology ID: {tech.id}")
                    self.technologies[tech.id] = tech

    def get_pattern(self, pattern_id: str) -> Optional[PatternItem]:
        return self.patterns.get(pattern_id)

    def get_artifact(self, artifact_id: str) -> Optional[ArtifactTemplate]:
        return self.artifacts.get(artifact_id)

    def get_technology(self, tech_id: str) -> Optional[TechKBItem]:
        return self.technologies.get(tech_id)

    def search_patterns_by_domain(self, domain_cluster_id: str) -> List[PatternItem]:
        return [
            p for p in self.patterns.values()
            if domain_cluster_id in p.applicable_domains or not p.applicable_domains
        ]

    def list_all_patterns(self) -> List[PatternItem]:
        return list(self.patterns.values())

    def list_all_artifacts(self) -> List[ArtifactTemplate]:
        return list(self.artifacts.values())

    def list_all_technologies(self) -> List[TechKBItem]:
        return list(self.technologies.values())
