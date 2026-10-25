# Open-Source Design Provenance

This package is generated from project-owned registries. It does not copy third-party skill text. Its design adapts interoperable concepts documented by these primary sources:

| Source | License/status | Adapted concept |
|---|---|---|
| [Agent Skills specification](https://agentskills.io/specification) | Code Apache-2.0; documentation CC-BY-4.0 | `SKILL.md`, progressive disclosure, scripts/references/assets, name/description/compatibility/tool metadata |
| [Anthropic skills](https://github.com/anthropics/skills) | Per-skill licensing; some source-available | Self-contained skill folders and explicit warning to test before critical use |
| [OpenAI plugins](https://github.com/openai/plugins) | Per-plugin manifest/license | Package manifest, capabilities, authentication lifecycle, marketplace metadata |
| [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) | MIT | Composable skill sources, load/read/run separation, filtering/deduplication, checkpointing and observability |
| [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai) | MIT | Dataset/solver/scorer separation, sandboxed agent evaluation, limits and transcript evidence |
| [Promptfoo](https://github.com/promptfoo/promptfoo) | MIT | Declarative eval matrices, red teaming and CI thresholds |
| [LangGraph](https://github.com/langchain-ai/langgraph) | MIT | Durable execution, interrupts and resumable state |
| [DeepEval](https://github.com/confident-ai/deepeval) | Apache-2.0 | Agent task/tool/plan metrics and trace-level evaluation concepts |

Third-party versions and licenses must be rechecked before vendoring code or data. URLs are provenance references, not runtime dependencies or endorsements.
