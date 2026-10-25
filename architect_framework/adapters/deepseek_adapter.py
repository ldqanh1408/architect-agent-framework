from typing import Dict, Any, Optional
from architect_framework.adapters.base_adapter import BaseModelAdapter, AdapterConfig, AdapterOutput
from architect_framework.models.execution_matrix import OrchestrationContext


class DeepSeekAdapter(BaseModelAdapter):
    """
    DeepSeek Adapter (DeepSeek-V3 / DeepSeek-R1 reasoning models).
    Formats OrchestrationContext to leverage reasoning capabilities (<think> tag output).
    """

    def __init__(self, config: Optional[AdapterConfig] = None):
        if config is None:
            config = AdapterConfig(
                adapter_name="deepseek",
                model_name="deepseek-reasoner",
                provider="deepseek",
                temperature=0.0,
                max_tokens=8192,
                system_prompt_format="markdown",
                extra_params={"reasoning_mode": True, "strip_think_tags_on_save": True}
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

        system_prompt = f"""# DEEPSEEK ARCHITECT SYSTEM PROMPT
You are a Principal Software Architect running at matrix coordinate **{matrix_id}**.

## DOMAIN CONTRACT
- **Domain ID**: `{domain.id}` ({domain.name})
- **Cluster**: `{domain.cluster_id}`
- **ISO 42010 Concerns**: {", ".join(domain.concerns)}
- **Viewpoints**: {", ".join(domain.viewpoints)}

## TASK CONTRACT
- **Task ID**: `{task.id}` ({task.name})
- **Required Inputs**: {", ".join(task.inputs_required)}

- **Expected Deliverables**: {", ".join(task.expected_outputs)}

## REASONING & OUTPUT INSTRUCTION
Analyze trade-offs thoroughly. If using reasoning mode, encapsulate internal chain-of-thought inside `<think>...</think>` before presenting the final architecture specification.
"""
        prompt_body = user_request or f"Execute architectural task '{task.name}' for domain '{domain.name}'."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt_body}
        ]

        payload: Dict[str, Any] = {
            "model": self.config.model_name,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
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

    @staticmethod
    def strip_thinking_blocks(text: str) -> str:
        from architect_framework.sdd_bridge.authoring_qa import strip_thinking_blocks as _strip
        return _strip(text)
