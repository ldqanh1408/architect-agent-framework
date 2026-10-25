from pathlib import Path
from typing import List, Dict, Optional
from architect_framework.registry._yaml import safe_load
from architect_framework.models.domain_skill import DomainSkill, DomainCluster


class DomainRegistry:
    """
    Registry for Horizontal Domain Skills (10 Clusters / 110 Skills).
    """

    def __init__(self, data_path: Optional[Path] = None, *, include_installed: bool = True):
        if data_path is None:
            data_path = Path(__file__).parent.parent / "data" / "domain_skills.yaml"
        self.data_path = data_path
        self.clusters: Dict[str, DomainCluster] = {}
        self.skills: Dict[str, DomainSkill] = {}
        self.load_data()
        if include_installed and data_path == Path(__file__).parent.parent / 'data/domain_skills.yaml':
            from architect_framework.registry.installed import installed_rows
            for group,row in installed_rows('domain'):
                if row['id'] in self.skills:continue
                skill=DomainSkill(**row)
                cluster=self.clusters.get(group)
                if cluster is None:
                    cluster=DomainCluster(id=group,name=skill.cluster_name,iso_aspect=', '.join(skill.iso_aspects),description='Installed package metadata',skills=[])
                    self.clusters[group]=cluster
                self.skills[skill.id]=skill;cluster.skills.append(skill)

    def load_data(self):
        with open(self.data_path, "r", encoding="utf-8") as f:
            raw_data = safe_load(f)

        if not isinstance(raw_data, dict) or not isinstance(raw_data.get("clusters"), list):
            raise ValueError("domain registry must contain a 'clusters' list")
        for cluster_data in raw_data["clusters"]:
            if cluster_data["id"] in self.clusters:
                raise ValueError(f"Duplicate domain cluster ID: {cluster_data['id']}")
            skills_list = []
            for skill_data in cluster_data.get("skills", []):
                if skill_data.get("cluster_id") != cluster_data["id"]:
                    raise ValueError(f"Domain skill '{skill_data.get('id')}' has wrong cluster_id")
                if skill_data.get("cluster_name") != cluster_data["name"]:
                    raise ValueError(f"Domain skill '{skill_data.get('id')}' has wrong cluster_name")
                skill = DomainSkill(**skill_data)
                if skill.id in self.skills:
                    raise ValueError(f"Duplicate domain skill ID: {skill.id}")
                self.skills[skill.id] = skill
                skills_list.append(skill)
            cluster = DomainCluster(
                id=cluster_data["id"],
                name=cluster_data["name"],
                iso_aspect=cluster_data["iso_aspect"],
                description=cluster_data["description"],
                skills=skills_list,
            )
            self.clusters[cluster.id] = cluster

    def get_skill(self, skill_id: str) -> Optional[DomainSkill]:
        return self.skills.get(skill_id)

    def get_cluster(self, cluster_id: str) -> Optional[DomainCluster]:
        return self.clusters.get(cluster_id)

    def list_all_skills(self) -> List[DomainSkill]:
        return list(self.skills.values())

    def list_all_clusters(self) -> List[DomainCluster]:
        return list(self.clusters.values())

    def search_skills_by_aspect(self, aspect: str) -> List[DomainSkill]:
        aspect_lower = aspect.lower()
        return [
            s for s in self.skills.values()
            if any(aspect_lower in a.lower() for a in s.iso_aspects)
        ]
