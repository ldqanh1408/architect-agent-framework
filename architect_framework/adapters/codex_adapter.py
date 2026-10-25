from typing import Dict, Any, Optional
from architect_framework.adapters.base_adapter import BaseModelAdapter, AdapterConfig, AdapterOutput
from architect_framework.models.execution_matrix import OrchestrationContext


class CodexAdapter(BaseModelAdapter):
    """
    OpenAI / Codex Adapter.
    Formats OrchestrationContext for GPT-4o, Codex, o1, and o3-mini models.
    Supports OpenAI ChatCompletions API, function tool calling schemas, and JSON Schema output format.
    """

    def __init__(self, config: Optional[AdapterConfig] = None):
        if config is None:
            config = AdapterConfig(
                adapter_name="codex",
                model_name="gpt-4o",
                provider="openai",
                temperature=0.2,
                max_tokens=4096,
                enable_structured_outputs=True,
                system_prompt_format="markdown",
                extra_params={"seed": 42}
            )
        super().__init__(config)

    def format_context(
        self,
        context: OrchestrationContext,
        user_request: Optional[str] = None,
        **kwargs
    ) -> AdapterOutput:
        domain = context.domain_skill
        task = context.task_skill
        matrix_id = context.execution_point.matrix_id

        # Markdown system prompt for Codex / OpenAI
        system_prompt = f"""# ROLE & CONTEXT
You are a Lead Software Architect operating at execution matrix point **{matrix_id}**.

## DOMAIN ARCHITECTURE: {domain.name} (`{domain.id}`)
- **Cluster**: {domain.cluster_id}
- **Description**: {domain.description}
- **Architectural Concerns**: {", ".join(domain.concerns)}
- **ISO 42010 Viewpoints**: {", ".join(domain.viewpoints)}

## TASK CONTRACT: {task.name} (`{task.id}`)
- **Description**: {task.description}
- **Required Inputs**: {", ".join(task.inputs_required)}

- **Expected Outputs**: {", ".join(task.expected_outputs)}

## BOUND PATTERNS & KNOWLEDGE
"""
        for p in context.bound_patterns:
            system_prompt += f"- **Pattern**: {p.name} (`{p.id}`): {p.problem} -> {p.solution}\n"

        system_prompt += "\n## BOUND TECHNOLOGIES\n"
        for t in context.bound_tech_items:
            system_prompt += f"- **Tech**: {t.name} (`{t.id}`): BestFor=[{', '.join(t.best_used_for)}], Limits=[{', '.join(t.operational_limits)}]\n"


        system_prompt += "\nDeliver precise, modular, and standard-compliant architectural artifacts."

        prompt_body = user_request or f"Execute task '{task.name}' for domain '{domain.name}'."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt_body}
        ]

        payload: Dict[str, Any] = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_completion_tokens": self.config.max_tokens,
        }

        output_mode = kwargs.get("output_mode") or (self.config.extra_params or {}).get("output_mode")
        if self.config.enable_structured_outputs and output_mode != "markdown_artifact":
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "architectural_deliverable",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "matrix_id": {"type": "string"},
                            "domain_skill_id": {"type": "string"},
                            "task_skill_id": {"type": "string"},
                            "architecture_decisions": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "components": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "trade_off_analysis": {"type": "string"}
                        },
                        "required": [
                            "matrix_id",
                            "domain_skill_id",
                            "task_skill_id",
                            "architecture_decisions",
                            "components",
                            "trade_off_analysis"
                        ],
                        "additionalProperties": False
                    }
                }
            }

        return AdapterOutput(
            adapter_name=self.config.adapter_name,
            model_name=self.config.model_name,
            provider=self.config.provider,
            system_prompt=system_prompt,
            user_prompt=prompt_body,
            formatted_payload=payload,
            config=self.config,
        )
