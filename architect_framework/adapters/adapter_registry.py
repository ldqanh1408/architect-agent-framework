import os
from typing import Dict, Type, List, Optional
import yaml
from architect_framework.adapters.base_adapter import BaseModelAdapter, AdapterConfig
from architect_framework.adapters.claude_adapter import ClaudeAdapter
from architect_framework.adapters.hermes_adapter import HermesAdapter
from architect_framework.adapters.codex_adapter import CodexAdapter
from architect_framework.adapters.ollama_adapter import OllamaAdapter
from architect_framework.adapters.deepseek_adapter import DeepSeekAdapter


class AdapterRegistry:
    """
    Central Registry for managing and retrieving LLM Model Adapters in Architect Agent Framework.
    """

    _adapters: Dict[str, Type[BaseModelAdapter]] = {
        "claude": ClaudeAdapter,
        "hermes": HermesAdapter,
        "codex": CodexAdapter,
        "openai": CodexAdapter,
        "ollama": OllamaAdapter,
        "deepseek": DeepSeekAdapter,
    }

    @classmethod
    def list_adapters(cls) -> List[str]:
        """Returns a list of supported adapter names."""
        return list(cls._adapters.keys())

    @classmethod
    def get_adapter_class(cls, adapter_name: str) -> Type[BaseModelAdapter]:
        """Gets adapter class by name."""
        name = adapter_name.lower().strip()
        if name not in cls._adapters:
            raise ValueError(
                f"Adapter '{adapter_name}' not supported. Available adapters: {', '.join(cls.list_adapters())}"
            )
        return cls._adapters[name]

    @classmethod
    def get_adapter(
        cls,
        adapter_name: str,
        config: Optional[AdapterConfig] = None,
        config_path: Optional[str] = None
    ) -> BaseModelAdapter:
        """
        Instantiates an adapter by name, using either custom AdapterConfig, YAML config file, or defaults.
        """
        adapter_cls = cls.get_adapter_class(adapter_name)

        if config is None and config_path and os.path.exists(config_path):
            config = cls.load_config_from_yaml(config_path)

        return adapter_cls(config=config)

    @classmethod
    def register_adapter(cls, name: str, adapter_cls: Type[BaseModelAdapter]):
        """Registers a custom user-defined model adapter."""
        cls._adapters[name.lower().strip()] = adapter_cls

    @staticmethod
    def load_config_from_yaml(filepath: str) -> AdapterConfig:
        """Loads an AdapterConfig object from a YAML file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return AdapterConfig(**data)
