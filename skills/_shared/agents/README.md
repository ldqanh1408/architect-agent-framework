# Agent Configuration

Each package's `agents/openai.yaml` is a portable example. The active runtime may select another model, but must preserve the package contract, tool boundaries, and deterministic validators. Model success is never inferred from process exit alone.
