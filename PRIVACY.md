# Privacy

The Architect Agent Framework plugin collects nothing and sends nothing anywhere.

- **No telemetry.** The plugin, its launcher, its MCP server, its hook and its review console contain no
  analytics, no usage counters and no crash reporting.
- **No account.** Nothing asks you to sign in. The review console listens on `127.0.0.1` only, and its
  passkey signature is checked on your machine against a public key you registered there.
- **Network use.** The only network traffic the plugin starts itself is `uv` downloading the framework
  package from the Python package index the first time the launcher needs it. Your documents, requirements and
  decisions are never uploaded by the plugin. The model that reads them is the one your Claude Code session
  already uses, under that session's own terms.
- **What it writes.** Run records and the skills you install go under `~/.architect-framework/`, and the
  launcher's Python environment under `${CLAUDE_PLUGIN_DATA}` (or `~/.architect-framework/venv`). Pages the
  agents write go into the workspace you pointed them at, inside the sandbox of the job that wrote them.
  Removing those folders removes everything the plugin kept.

Questions: <https://github.com/ldqanh1408/Architect-Agent-Framework/issues>
