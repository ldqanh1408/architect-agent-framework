from typing import Dict, Any, Optional
from architect_framework.adapters.base_adapter import BaseModelAdapter, AdapterConfig, AdapterOutput
from architect_framework.models.execution_matrix import OrchestrationContext


class HermesAdapter(BaseModelAdapter):
    """
    Nous Hermes / vLLM Adapter.
    Formats OrchestrationContext into ChatML format with tool definitions for Hermes 2 / Hermes 3 models.
    """

    def __init__(self, config: Optional[AdapterConfig] = None):
        if config is None:
            config = AdapterConfig(
                adapter_name="hermes",
                model_name="hermes-3-llama-3.1-405b",
                provider="nousresearch",
                temperature=0.3,
                max_tokens=4096,
                top_p=0.9,
                system_prompt_format="chatml",
                stop_sequences=["<|im_end|>"],
                extra_params={
                    "repetition_penalty": 1.1,
                    "endpoint": "http://localhost:8000/v1",
                    "chatml_tokens": {
                        "bos": "<|im_start|>",
                        "eos": "<|im_end|>"
                    }
                }
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

        # Build ChatML System Prompt for Hermes
        system_text = (
            f"You are Nous Hermes, an expert Software Architecture AI Agent executing point {matrix_id}.\n\n"
            f"### DOMAIN SKILL: {domain.name} [{domain.id}]\n"
            f"Cluster: {domain.cluster_id}\n"
            f"Description: {domain.description}\n"
            f"Concerns: {', '.join(domain.concerns)}\n"
            f"Viewpoints: {', '.join(domain.viewpoints)}\n\n"
            f"### TASK CONTRACT: {task.name} [{task.id}]\n"
            f"Description: {task.description}\n"
            f"Inputs Required: {', '.join(task.inputs_required)}\n"

            f"Outputs Expected: {', '.join(task.expected_outputs)}\n\n"
        )

        if context.bound_patterns:
            system_text += "### BOUND ARCHITECTURAL PATTERNS:\n"
            for p in context.bound_patterns:
                system_text += f"- {p.name} ({p.id}): {p.problem} -> {p.solution}\n"
            system_text += "\n"

        if context.bound_tech_items:
            system_text += "### BOUND TECHNOLOGIES KB:\n"
            for t in context.bound_tech_items:
                system_text += f"- {t.name} ({t.id}): Best for: {', '.join(t.best_used_for)} | Limits: {', '.join(t.operational_limits)}\n"

            system_text += "\n"

        system_text += (
            "Think step-by-step before producing final architectural deliverables. "
            "Ensure strict compliance with ISO/IEC/IEEE 42010 standards."
        )

        chatml_system = f"<|im_start|>system\n{system_text}\n<|im_end|>"

        prompt_body = user_request or f"Execute architectural task '{task.name}' for domain '{domain.name}'."

        messages = [
            {"role": "system", "content": system_text},
            {"role": "user", "content": prompt_body}
        ]

        payload: Dict[str, Any] = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "top_p": self.config.top_p,
            "repetition_penalty": self.config.extra_params.get("repetition_penalty", 1.1),
            "raw_chatml_prompt": f"{chatml_system}\n<|im_start|>user\n{prompt_body}\n<|im_end|>\n<|im_start|>assistant\n"
        }

        return AdapterOutput(
            adapter_name=self.config.adapter_name,
            model_name=self.config.model_name,
            provider=self.config.provider,
            system_prompt=system_text,
            user_prompt=prompt_body,
            formatted_payload=payload,
            config=self.config,
        )
