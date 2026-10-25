from typing import Dict, Any, Optional
from architect_framework.adapters.base_adapter import BaseModelAdapter, AdapterConfig, AdapterOutput
from architect_framework.models.execution_matrix import OrchestrationContext


class ClaudeAdapter(BaseModelAdapter):
    """
    Anthropic Claude Adapter.
    Formats OrchestrationContext into structured XML system prompts and Anthropic Messages API payloads.
    """

    def __init__(self, config: Optional[AdapterConfig] = None):
        if config is None:
            config = AdapterConfig(
                adapter_name="claude",
                model_name="claude-3-5-sonnet-20241022",
                provider="anthropic",
                temperature=0.2,
                max_tokens=8192,
                system_prompt_format="xml",
                extra_params={
                    "anthropic_version": "2023-06-01",
                    "preferred_claude4_model": "claude-sonnet-4-20250514",
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

        # Build XML structured system prompt
        xml_system_prompt = f"""<system_instructions>
<role>You are a Principal Software Architect operating at execution matrix point {matrix_id}.</role>

<domain_context id="{domain.id}">
  <title>{domain.name}</title>
  <cluster>{domain.cluster_id}</cluster>
  <description>{domain.description}</description>
  <architectural_concerns>
    {"".join(f'<concern>{c}</concern>' for c in domain.concerns)}
  </architectural_concerns>
  <viewpoints>
    {"".join(f'<viewpoint>{v}</viewpoint>' for v in domain.viewpoints)}
  </viewpoints>
</domain_context>

<task_contract id="{task.id}">
  <title>{task.name}</title>
  <description>{task.description}</description>
  <inputs>
    {"".join(f'<input>{i}</input>' for i in task.inputs_required)}
  </inputs>

  <outputs>
    {"".join(f'<output>{o}</output>' for o in task.expected_outputs)}
  </outputs>
</task_contract>

<bound_patterns>
"""
        for p in context.bound_patterns:
            xml_system_prompt += f"""  <pattern id="{p.id}">
    <name>{p.name}</name>
    <category>{p.category}</category>
    <problem>{p.problem}</problem>
    <solution>{p.solution}</solution>
  </pattern>\n"""
        xml_system_prompt += "</bound_patterns>\n\n<bound_technologies>\n"

        for t in context.bound_tech_items:
            xml_system_prompt += f"""  <technology id="{t.id}">
    <name>{t.name}</name>
    <category>{t.category}</category>
    <best_used_for>{", ".join(t.best_used_for)}</best_used_for>
    <operational_limits>{", ".join(t.operational_limits)}</operational_limits>

  </technology>\n"""
        xml_system_prompt += "</bound_technologies>\n</system_instructions>"

        prompt_body = user_request or f"Execute task '{task.name}' for domain '{domain.name}'."

        messages = [
            {"role": "user", "content": prompt_body}
        ]

        payload: Dict[str, Any] = {
            "model": self.config.model_name,
            "system": xml_system_prompt,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }

        if self.config.top_p is not None:
            payload["top_p"] = self.config.top_p

        return AdapterOutput(
            adapter_name=self.config.adapter_name,
            model_name=self.config.model_name,
            provider=self.config.provider,
            system_prompt=xml_system_prompt,
            user_prompt=prompt_body,
            formatted_payload=payload,
            config=self.config,
        )
