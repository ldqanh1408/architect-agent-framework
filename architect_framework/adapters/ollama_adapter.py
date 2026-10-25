from typing import Dict, Any, Optional
from architect_framework.adapters.base_adapter import BaseModelAdapter, AdapterConfig, AdapterOutput
from architect_framework.models.execution_matrix import OrchestrationContext


class OllamaAdapter(BaseModelAdapter):
    """
    Ollama Adapter for local open-source LLM deployments (Llama3, Mistral, Qwen2.5, DeepSeek-R1-Distill).
    Generates Modelfiles and Ollama /api/chat payload formats.
    """

    def __init__(self, config: Optional[AdapterConfig] = None):
        if config is None:
            config = AdapterConfig(
                adapter_name="ollama",
                model_name="llama3:latest",
                provider="ollama",
                temperature=0.2,
                max_tokens=4096,
                top_p=0.95,
                system_prompt_format="markdown",
                extra_params={"endpoint": "http://localhost:11434"}
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

        system_prompt = (
            f"SYSTEM INSTRUCTION: You are an AI Architect Agent executing E[{domain.id}, {task.id}].\n"
            f"Domain: {domain.name} ({domain.cluster_id})\n"
            f"Task: {task.name}\n"
            f"Concerns: {', '.join(domain.concerns)}\n"
            f"Viewpoints: {', '.join(domain.viewpoints)}\n"
            f"Outputs: {', '.join(task.expected_outputs)}\n"
        )

        prompt_body = user_request or f"Execute task '{task.name}' for domain '{domain.name}'."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt_body}
        ]

        modelfile_content = (
            f"FROM {self.config.model_name}\n"
            f"SYSTEM \"\"\"{system_prompt}\"\"\"\n"
            f"PARAMETER temperature {self.config.temperature}\n"
            f"PARAMETER num_ctx {self.config.max_tokens}\n"
        )

        payload: Dict[str, Any] = {
            "model": self.config.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_ctx": self.config.max_tokens,
            },
            "modelfile": modelfile_content
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
