# Install the local alpha

[English](INSTALL.md) · [Tiếng Việt](INSTALL.vi.md)

This handoff is **2.0.0**, **NOT_QUALIFIED**. Use its source or exact wheel. This handoff does not establish a published package, tag or marketplace release. Live Claude/Codex accounts, native platforms and physical passkeys have separate human verification exceptions.

From the source directory, prepare Python and the compiled console:

```bash
uv sync --frozen --all-extras
npm ci --ignore-scripts
npm run build:console
export ARCHITECT_PYTHON="$PWD/.venv/bin/python"
```

Alternatively, install the supplied wheel in your own virtual environment. Use the actual path to the extracted artifact:

```bash
python3 -m venv /path/to/aaf-env
/path/to/aaf-env/bin/python -m pip install '/path/to/architect_agent_framework-2.0.0-py3-none-any.whl[console,sdd]'
export ARCHITECT_PYTHON=/path/to/aaf-env/bin/python
```

The shell commands above use a POSIX filesystem. Native Windows execution has not been qualified. Keep the host bundle at its extracted path. Configure the host's local plugin mechanism for `plugins/architect-agent-framework`; the included Claude and Codex marketplace manifests point there. Follow the host's current local installation procedure. Exact account installation is not certified by the local launcher tests.

Verify the selected interpreter and launcher (if running inside the standalone plugin archive root, use `scripts/architect_runtime.py` instead of `plugins/architect-agent-framework/scripts/architect_runtime.py`):

```bash
"$ARCHITECT_PYTHON" -m architect_framework.cli.main --help
python plugins/architect-agent-framework/scripts/architect_runtime.py --bootstrap --help
```

Create a new empty specification directory explicitly:

```bash
python plugins/architect-agent-framework/scripts/architect_runtime.py --bootstrap sdd host-init ./my-spec --workspace-id my-project --reviewer owner
python plugins/architect-agent-framework/scripts/architect_runtime.py --bootstrap console serve ./my-spec --enroll
```

The person runs enrollment in their own terminal and confirms the reviewer fingerprint. A required task dispatch signature and final document acceptance are separate. An agent cannot enroll, trust or sign for the person. Opening a workspace does not migrate it. Use [the core guide](docs/GUIDE-SDD-CORE.md) for separate-destination migration and recovery.

The catalog has **297 slots**. The plugin includes four free catalog bodies, three foundation skills and one runtime skill: **eight included skills**. The **293 paid catalog bodies** are absent. A slot's metadata does not constitute installed authored content.

Install content that you own through the current package tool:

```bash
python plugins/architect-agent-framework/scripts/architect_runtime.py --bootstrap skills install /path/to/skill-pack.zip
```

Read [the core guide](docs/GUIDE-SDD-CORE.md) for bindings, compatibility and provenance. External content grants no workspace permissions. Preserve your user skill directory when changing versions. The local upgrade rehearsal rejects an incompatible store unchanged; it does not automatically rewrite or downgrade user state.

Read [SUPPORT-MATRIX.md](docs/SUPPORT-MATRIX.md), [CONTRIBUTING.md](CONTRIBUTING.md) and the source completion report for exact limits and evidence. No provider credential is required for public synthetic tests. Semantic/style qualification remains incomplete without independent labels and live evidence.
