from pathlib import Path
from typing import List, Dict, Optional
from architect_framework.registry._yaml import safe_load
from architect_framework.models.task_skill import TaskTechnicalItem, TaskFamily


class TaskRegistry:
    """
    Registry for Vertical Task Skills (21 Task Families).
    """

    def __init__(self, data_path: Optional[Path] = None, *, include_installed: bool = True):
        if data_path is None:
            data_path = Path(__file__).parent.parent / "data" / "task_skills.yaml"
        self.data_path = data_path
        self.families: Dict[str, TaskFamily] = {}
        self.tasks: Dict[str, TaskTechnicalItem] = {}
        self.task_to_family: Dict[str, TaskFamily] = {}
        self.load_data()
        if include_installed and data_path == Path(__file__).parent.parent / 'data/task_skills.yaml':
            from architect_framework.registry.installed import installed_rows
            for group,row in installed_rows('task'):
                if row['id'] in self.tasks:continue
                task=TaskTechnicalItem(**row)
                family=self.families.get(group)
                if family is None:
                    family=TaskFamily(id=group,name=group,core_activity='Installed package metadata',expected_technical_output='',tasks=[])
                    self.families[group]=family
                self.tasks[task.id]=task;self.task_to_family[task.id]=family;family.tasks.append(task)

    def load_data(self):
        with open(self.data_path, "r", encoding="utf-8") as f:
            raw_data = safe_load(f)

        if not isinstance(raw_data, dict) or not isinstance(raw_data.get("families"), list):
            raise ValueError("task registry must contain a 'families' list")
        for family_data in raw_data["families"]:
            if family_data["id"] in self.families:
                raise ValueError(f"Duplicate task family ID: {family_data['id']}")
            tasks_list = []
            for task_data in family_data.get("tasks", []):
                task = TaskTechnicalItem(**task_data)
                if task.id in self.tasks:
                    raise ValueError(f"Duplicate task ID: {task.id}")
                self.tasks[task.id] = task
                tasks_list.append(task)

            family = TaskFamily(
                id=family_data["id"],
                name=family_data["name"],
                core_activity=family_data["core_activity"],
                expected_technical_output=family_data["expected_technical_output"],
                tasks=tasks_list,
            )
            self.families[family.id] = family
            for task in tasks_list:
                self.task_to_family[task.id] = family

    def get_task(self, task_id: str) -> Optional[TaskTechnicalItem]:
        return self.tasks.get(task_id)

    def get_family(self, family_id: str) -> Optional[TaskFamily]:
        return self.families.get(family_id)

    def get_family_for_task(self, task_id: str) -> Optional[TaskFamily]:
        return self.task_to_family.get(task_id)

    def list_all_tasks(self) -> List[TaskTechnicalItem]:
        return list(self.tasks.values())

    def list_all_families(self) -> List[TaskFamily]:
        return list(self.families.values())
