# Architect Agent Framework (AAF v2.0) — Multi-Harness Integration Guide (Claude, Codex, DeepSeek Harness) & Complete 16-Command Reference

> **Target Version:** `2.0.0` (ISO/IEC/IEEE 42010 · C4 Model · arc42 · DDD · ASD-STE100 Advisory)
> **First-Class Supported Harnesses:** **Claude Code (`claude`)**, **OpenAI Codex (`codex`)**, and **DeepSeek Harness (`dsh` / Orca / OMC)** across **Windows (PowerShell)**, **macOS**, and **Linux**.

---

## Table of Contents

1. [Architecture Overview & What Is New in AAF v2.0](#1-architecture-overview--what-is-new-in-aaf-v20)
2. [Direct Installation & Integration into Claude Code, Codex, and DeepSeek Harness (`dsh`)](#2-direct-installation--integration-into-claude-code-codex-and-deepseek-harness-dsh)
3. [Detailed Plugin Configuration: `JEV_API_KEY` (`JEV_KEY`), Environment Variables, `sdd-workspace.yml` & Adapters](#3-detailed-plugin-configuration-jev_api_key-jev_key-environment-variables-sdd-workspaceyml--adapters)
4. [Choosing an Operating Mode (`solo-author` vs `governed-team`) & Workspace Scale (`Profile`)](#4-choosing-an-operating-mode-solo-author-vs-governed-team--workspace-scale-profile)
5. [Quick Reference Table for All 16 Commands Across 3 Harnesses (Command Cheat-Sheet)](#5-quick-reference-table-for-all-16-commands-across-3-harnesses-command-cheat-sheet)
6. [Detailed Reference Guide for Each Command (16 Commands Reference)](#6-detailed-reference-guide-for-each-command-16-commands-reference)
7. [Hands-On Workflows for 8 Real-World Use Cases (`UC-01` → `UC-08`)](#7-hands-on-workflows-for-8-real-world-use-cases-uc-01--uc-08)
8. [Dual-Mode Mapping Table: MCP Tools ↔ CLI Commands (`architect-runtime`)](#8-dual-mode-mapping-table-mcp-tools--cli-commands-architect-runtime)
9. [Troubleshooting Common Issues (Windows, Claude, Codex, DSH)](#9-troubleshooting-common-issues-windows-claude-codex-dsh)

---

## 1. Architecture Overview & What Is New in AAF v2.0

**Architect Agent Framework (AAF v2.0)** is a multi-agent architecture specification engine and runtime that transforms **raw ideas, SRS/PRD documents, or existing source code** into an **ISO/IEC/IEEE 42010-compliant software architecture specification suite** backed by deterministic mathematical gates and an interactive C4 visual workbench.

### Core Improvements for Starting in 60 Seconds (Zero System Prompt):

* **Zero Manual System Prompting:** The entire 6-phase pipeline (Phase 0 Init → Phase 1 Source Intake → Phase 2 Materialize Tree → Phase 3 Multi-Wave Authoring → Phase 4 Prepare-Check & Gate Loop → Phase 5 Sharded Semantic/Language Review) is pre-packaged directly inside each command.
* **First-Class Execution Across All 3 Harnesses (`Claude Code`, `Codex`, `DeepSeek Harness / dsh`):** Supports both the **MCP Server (`architect-runtime`)** and the **CLI Fallback (`architect_runtime.py --bootstrap`)**, automatically detecting the host environment even on Windows PowerShell without `sh`.
* **Passkey-Free `solo-author` Default Mode:** Individual authors can run end-to-end automation without being blocked at step 0 by hardware WebAuthn Passkey gates (Passkey enforcement is enabled only when switching to `governed-team` mode or when recording formal release sign-off).
* **Strict Anti-Hollow Gate Verification:** Detects 100% of pages containing unresolved `TODO` or `TBD` markers, empty sections, or missing `depth_witnesses` evidence across all 9 architectural depth dimensions, while automatically normalizing page length to `180–350` lines per page.

---

## 2. Direct Installation & Integration into Claude Code, Codex, and DeepSeek Harness (`dsh`)

### Step 2.1. One-Time Common Environment Setup

System requirements: **Python 3.10+** (`uv` recommended for isolated dependency management) and **Node.js 18+** (only if rebuilding the Console UI from source).

**On Windows (PowerShell):**

```powershell
cd <repo>
uv sync --locked --all-extras
npm ci --ignore-scripts
npm run build:console

# Install all Skills, 16 Commands, and register Host Config for Claude, Codex, and DeepSeek Harness:
.\install.ps1 -All -Agent all
```

**On macOS / Linux / WSL (Bash/Zsh):**

```bash
cd /path/to/AFF
uv sync --locked --all-extras
npm ci --ignore-scripts
npm run build:console

# Install all Skills, 16 Commands, and register Host Config for Claude, Codex, and DeepSeek Harness:
./install.sh --all --agent all
```

> **Important Note:** Running `install.ps1` or `install.sh` automatically creates the locator file `~/.architect-framework/host-config.json` storing the repository root (`ARCHITECT_FRAMEWORK_HOME`) and Python interpreter path. This lets you run commands from **any project directory** on your machine without manually setting `$env:PYTHONPATH` or `$env:PYTHONUTF8=1`.

---

### Step 2.2. Integrating into **Claude Code (`claude`)**

You can integrate AAF into Claude Code using **either of two methods**:

#### Method 1: Load the Plugin Bundle Directly (Recommended — includes all 16 Slash Commands + MCP + PreToolUse Hook)

```bash
# Launch Claude Code with the plugin directory:
claude --plugin-dir "<repo>"
```

Or register it permanently in your local Claude Code Marketplace:

```bash
/plugin marketplace add "<repo>"
/plugin install architect-agent-framework@architect-agent-framework
```

#### Method 2: Install Directly into Project or User Home `.claude/` Directory

```powershell
# Install machine-wide (~/.claude/skills & ~/.claude/commands):
.\install.ps1 -All -Agent claude

# Or install only for the current project (./.claude/skills & ./.claude/commands):
.\install.ps1 -All -Agent claude -Project
```

* **How to invoke commands in Claude Code:** Type `/architect`, `/architect-init`, `/architect-clarify`, `/architect-quickstart`, `/architect-design`, `/architect-check`, `/architect-console`, etc.

---

### Step 2.3. Integrating into **OpenAI Codex (`codex`)**

OpenAI Codex supports the `.codex-plugin/plugin.json` manifest, the `.agents/skills/` skill directory (with `agents/openai.yaml`), and the `~/.codex/prompts/` prompt library.

#### Method 1: Automated Installation via the Installer for Codex

```powershell
# On Windows PowerShell (installs into ~/.agents/skills and ~/.codex/prompts):
.\install.ps1 -All -Agent codex

# Or install directly into the current project directory (./.agents/skills):
.\install.ps1 -All -Agent codex -Project
```

#### Method 2: Register the `architect-runtime` MCP Server in `~/.codex/config.toml`

Add the following block to `~/.codex/config.toml` so Codex can call all 25 AAF MCP tools directly:

```toml
[mcp_servers.architect-runtime]
command = "python"
args = [
  "<repo>",
  "--bootstrap",
  "mcp"
]

[mcp_servers.architect-runtime.env]
PYTHONUTF8 = "1"
```

* **How to invoke commands in Codex:**
  * Type `/prompts:architect-design`, `/prompts:architect-quickstart`, `/prompts:architect-check`, etc.
  * Or invoke via Codex skill syntax: `$architect-design`, `$01-system-architect`, `$00-requirement-clarifier`, etc.

---

### Step 2.4. Integrating into **DeepSeek Harness (`dsh` / Orca / Oh-My-Codex)**

DeepSeek Harness (`dsh`) manages skills via the `<available_skills>` catalog (activated through `skill(name="...")`) and executes multi-agent workflows using `subagent`, `send_message`, `list_agents`, and `pwsh` / `bash`.

#### Step 1: Install Core Skills + Command Skills into `dsh`

```powershell
# On Windows PowerShell (installs into ~/.dsh/skills, ~/.agents/skills, and ~/.claude/skills):
.\install.ps1 -All -Agent dsh

# Or install directly into the current project directory:
.\install.ps1 -All -Agent dsh -Project
```

After running the installer and restarting your `dsh` session, `<available_skills>` will include:
* **Foundation & Orchestration Skills:** `00-requirement-clarifier`, `01-system-architect`, `02-spec-critic`, `architect-runtime`, `architect-skill-orchestrator`, `adr-authoring`, `agent-workflow-design`, `arch-review-task`.
* **Command Skills (16 commands):** `architect`, `architect-init`, `architect-clarify`, `architect-quickstart`, `architect-design`, `architect-execute`, `architect-route`, `architect-audit`, `architect-change`, `architect-check`, `architect-review`, `architect-run`, `architect-status`, `architect-skills`, `architect-console`, `architect-approve`.

#### Step 2: Configure the MCP Server for `dsh` (Optional — the plugin also runs 100% via CLI `pwsh`/`bash` without MCP)

If your `dsh` setup supports `.mcp.json` in the project directory:

```json
{
  "mcpServers": {
    "architect-runtime": {
      "command": "python",
      "args": [
        "<repo>",
        "--bootstrap",
        "mcp"
      ],
      "env": {
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

* **How to invoke commands in DeepSeek Harness (`dsh`):**
  * Type directly in chat: `/architect-design --profile maximal --sources SYSTEM_REQUIREMENTS.md --out ./atlas-spec` or `$architect-quickstart`.
  * Or ask in natural language: *"Use architect-design to generate a maximal architecture specification from SYSTEM_REQUIREMENTS.md into the atlas-spec folder"* — `dsh` will automatically invoke `skill(name="architect-design")` and execute all 6 phases without requiring any manual system prompt.

---

## 3. Detailed Plugin Configuration: `JEV_API_KEY` (`JEV_KEY`), Environment Variables, `sdd-workspace.yml` & Adapters

This section explains how to configure the **Independent Judge API Key (`JEV_API_KEY` / `JEV_KEY`)**, **Runtime Environment Variables (`ARCHITECT_*`)**, **`sdd-workspace.yml`**, and **Model Adapters (`Claude`, `Codex`, `DeepSeek`)**.

---

### 3.1. Configuring `JEV_API_KEY` (`JEV_KEY` / `SDD_JUDGE_API_KEY`) for Semantic & Language Review

During **Phase 5 (`/architect-review --live` or `sdd review-candidate --live` / `sdd language-review --live`)**, the plugin invokes an **Independent Judge** (defaulting to `typesafe-jev` at `https://api.typesafe.ai/v1/systemone`, or an `openai-compatible` endpoint you specify) to cross-verify requirement obligations and evaluate the 8 technical language rules (`aaf-ste80-v1`).

> **Important Note on Variable Names (`JEV_KEY` vs `JEV_API_KEY`):**
> * In the core engine (`sdd_core/adapters/judge_http.py`), the default environment variable name is **`JEV_API_KEY`** (or **`SDD_JUDGE_API_KEY`**).
> * In the release runtime (`WO-R3.1`), `launcher.py` and `architect_runtime.py` automatically read all 3 variable names: **`JEV_API_KEY`**, **`JEV_KEY`**, and **`SDD_JUDGE_API_KEY`** (automatically mapping `JEV_KEY -> JEV_API_KEY` if you define `JEV_KEY` in `.env`).
> * **Never hard-code secret keys directly inside `sdd-workspace.yml`** (`sdd-workspace.yml` only declares the environment variable name via `api_key_env: JEV_API_KEY`).

You can configure `JEV_API_KEY` (`JEV_KEY`) using **any of the 4 methods** below depending on your harness:

#### Method 1: Place in a `.env` File (Recommended — shared across Claude, Codex, DeepSeek Harness `dsh`, and CLI)

Create a `.env` file at the **project root** (for example `<repo>`) or in the global user directory `~/.architect-framework/.env`:

```dotenv
# File: .env (or ~/.architect-framework/.env)

# 1. API Key for the Independent Judge (accepts JEV_API_KEY, JEV_KEY, or SDD_JUDGE_API_KEY)
JEV_API_KEY=jev_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
JEV_KEY=jev_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 2. (Optional) Allow empty skill slots among the 297 slots to author from base contracts
ARCHITECT_ALLOW_BASE=1

# 3. (Optional) Runtime and hook message language (en or vi)
ARCHITECT_LANG=en
```

#### Method 2: Configure Directly in **Claude Code Plugin (`userConfig.judge_api_key`)**

In `plugins/architect-agent-framework/.claude-plugin/plugin.json`, the plugin declares the sensitive option `userConfig.judge_api_key`, and `.mcp.json` automatically maps it to `JEV_API_KEY` and `SDD_JUDGE_API_KEY`:

* **Via the Claude Code UI:** When installing the plugin, enter your key in the **Independent judge API key (`judge_api_key`)** field under Plugin Settings.
* **Or via Claude Code environment variables / `.claude/settings.local.json`:**
  ```json
  {
    "env": {
      "CLAUDE_PLUGIN_OPTION_JUDGE_API_KEY": "jev_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
      "JEV_API_KEY": "jev_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
      "ARCHITECT_ALLOW_BASE": "1"
    }
  }
  ```

#### Method 3: Configure in **OpenAI Codex (`~/.codex/config.toml` or `codex.mcp.json`)**

If you use the Codex CLI or Codex Desktop App, declare the key under `[mcp_servers.architect-runtime.env]` in `~/.codex/config.toml`:

```toml
[mcp_servers.architect-runtime]
command = "python"
args = [
  "<repo>",
  "--bootstrap",
  "mcp"
]

[mcp_servers.architect-runtime.env]
JEV_API_KEY = "jev_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
SDD_JUDGE_API_KEY = "jev_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
ARCHITECT_ALLOW_BASE = "1"
PYTHONUTF8 = "1"
```

#### Method 4: Configure in **DeepSeek Harness (`dsh` / PowerShell / Bash)**

In DeepSeek Harness (`dsh`), in addition to placing the key in `.env` (Method 1), you can configure it in `.mcp.json` or export it in your PowerShell / Bash session before launching `dsh`:

**On Windows PowerShell:**
```powershell
# Load automatically from .env (if present) or assign directly:
$env:JEV_API_KEY = "jev_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
$env:ARCHITECT_ALLOW_BASE = "1"
$env:PYTHONUTF8 = "1"
```

**On macOS / Linux (Bash/Zsh):**
```bash
export JEV_API_KEY="jev_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export ARCHITECT_ALLOW_BASE="1"
export PYTHONUTF8="1"
```

---

### 3.2. Complete Plugin Environment Variables Reference

| Environment Variable | Default Value | Purpose & When to Configure |
| :--- | :--- | :--- |
| **`JEV_API_KEY`** *(or `JEV_KEY`, `SDD_JUDGE_API_KEY`)* | *(Empty)* | **API Key for the Independent Judge** when running `/architect-review --live`, `sdd review-candidate --live`, or `sdd language-review --live`. Note: if both `JEV_API_KEY` and `SDD_JUDGE_API_KEY` are set, their values must match or `CONFIG_CONFLICT` is raised. |
| **`CLAUDE_PLUGIN_OPTION_JUDGE_API_KEY`** | *(Set by Claude)* | Passed automatically by Claude Code when you configure `judge_api_key` in plugin settings. `launcher.py` maps this value to `JEV_API_KEY` and `SDD_JUDGE_API_KEY`. |
| **`ARCHITECT_ALLOW_BASE`** | `0` (`false`) | **Highly useful:** Set `ARCHITECT_ALLOW_BASE=1` to allow agents to author pages for all **293 uninstalled commercial skill slots** using the base contract (`skill-contract.yml` & `workspace-template.yml`). When `0`, `empty` slots block file writes. |
| **`ARCHITECT_FRAMEWORK_HOME`** | *(Auto-resolved via `host-config.json`)* | Absolute path pointing to the AAF source/plugin root (e.g., `<repo>`). Only set manually if you move the folder after running `install.ps1` / `install.sh`. |
| **`ARCHITECT_PYTHON`** | *(Auto-detected `.venv` or `uv`)* | Path to a Python executable with required dependencies installed (`pydantic`, `pyyaml`, `cryptography`, `httpx`, `markdown-it-py`, `jsonschema`), e.g., `<repo>`. |
| **`ARCHITECT_HOME`** *(or `ARCHITECT_STATE_HOME`)* | `~/.architect-framework` | User-level state directory (stores installed skill packs, cached slot catalog, `host-config.json`, and global `skill-bindings.yml`). |
| **`ARCHITECT_SKILLS_PATH`** | *(Empty)* | Delimited list of paths to external custom skill directories (`;` on Windows or `:` on macOS/Linux). Searched with highest priority before `~/.claude/skills/`. |
| **`ARCHITECT_SKILL_BINDINGS`** | `skill-bindings.yml` | Path to a YAML file mapping your custom skills into one or more of the 297 AAF skill slots. |
| **`ARCHITECT_VENV`** | `~/.architect-framework/venv` | Target directory for the managed Python virtual environment when the launcher bootstraps via `uv`. |
| **`ARCHITECT_MCP_TOKEN`** | *(Empty)* | Bearer authentication token (**minimum 32 characters**) required when exposing the MCP Server over HTTP (`architect-runtime mcp --http --workspace ./spec --port 8768`). |
| **`ARCHITECT_LANG`** | `en` (or system locale) | Set to `en` or `vi` to control the language of runtime CLI diagnostics and PreToolUse Hook security notices. |

---

### 3.3. Configuring `sdd-workspace.yml` (Judge Provider, Policy, Runtime & Language Glossary)

Every architecture workspace is governed by a central configuration file named **`sdd-workspace.yml`**. Below are reference configurations for the **Judge Provider (`typesafe-jev` or `openai-compatible`)**, **Governance Policy**, and **Language Glossary (`aaf-ste80-v1`)**:

#### A. Configuring `provider:` in `sdd-workspace.yml` (2 Options)

**Option 1: Standard `typesafe-jev` Provider (Recommended default for `JEV_API_KEY`)**

```yaml
provider:
  type: typesafe-jev
  endpoint: https://api.typesafe.ai/v1/systemone
  model: jev-1.14.0
  api_key_env: JEV_API_KEY          # Name of the environment variable holding the key (DO NOT paste the raw key here!)
  timeout_seconds: 60               # Maximum timeout per JEV request (seconds)
  max_attempts: 2                   # Maximum retry attempts (1 - 3)
  max_output_tokens: 4000           # Judge output token limit
  max_cost_usd: 5.0                 # Maximum budget cap (USD) per candidate (tracked in SQLite budget ledger)
  input_per_million: 1.0            # Estimated USD per 1M input tokens for conservative budget reservation
  output_per_million: 1.0           # Estimated USD per 1M output tokens
```

**Option 2: `openai-compatible` Provider (Using OpenAI / DeepSeek / OpenRouter as Semantic Judge)**

If you do not have a `typesafe-jev` account and want to use an OpenAI ChatCompletions-compatible endpoint (supporting `response_format: json_schema` for `sdd review`), configure:

```yaml
provider:
  type: openai-compatible
  endpoint: https://api.openai.com/v1/chat/completions   # Must use HTTPS without embedded user:pass credentials
  model: gpt-4o-2024-08-06
  api_key_env: OPENAI_API_KEY                            # Set OPENAI_API_KEY in your environment or .env
  timeout_seconds: 90
  max_attempts: 2
  max_output_tokens: 6000
  max_cost_usd: 5.0
  input_per_million: 2.5
  output_per_million: 10.0
```

> **Technical Note:** Live evaluation of the 8 sentence-level style rules (`sdd language-review --live`) and `JevQuestions` uses the choice-probability distribution protocol specific to **`typesafe-jev`**. Without `--live`, `sdd language-review` (or `/architect-check`) still runs the local heuristic STE-80 style checker completely offline without an API key.

#### B. Configuring `policy:` and `runtime:` in `sdd-workspace.yml`

```yaml
policy:
  mode: advisory                    # "advisory" (for solo-author) | "enforce" (for governed-team) | "shadow"
  reviewers:
    - lead-architect                # List of reviewer IDs (bound to enrolled Passkey credentials)
  decision_authority: external      # "local" or "external"
  require_human_acceptance: true    # Always separate authoring completion from human acceptance sign-off
  require_requirement_obligations: true
  require_system_review: true
  shard_system_review: true         # MUST be true for workspaces > 12 documents to shard @system review packets automatically
  max_file_bytes: 250000            # Maximum size of a single document file (bytes)
  max_packet_bytes: 200000          # Maximum size of a single review packet sent to the Judge (200 KB)
  max_workspace_documents: 512      # Maximum documents in a workspace (up to 2000 supported by schema)
  max_review_age_seconds: 2592000   # Validity window for review verdicts (30 days)
  runtime:
    max_tasks: 200                  # Maximum tasks in a single run (1 - 1000)
    max_concurrency: 4              # Maximum parallel subagents (<= 4 recommended to prevent HTTP 429)
    max_task_attempts: 2            # Maximum retries per task (1 - 3)
    deadline_seconds: 86400         # Overall run deadline (24 hours)
    lease_seconds: 1800             # Worker lease duration per claimed task (30 minutes)
    first_run_gate: auto            # "auto" (run immediately for solo-author) | "approve" (await Passkey for governed-team)
```

#### C. Configuring the Domain `language.glossary` in `sdd-workspace.yml`

So that the language gate (`aaf-ste80-v1`) recognizes domain-specific terminology in your project, declare a `language:` block in `sdd-workspace.yml`:

```yaml
language:
  profile_id: aaf-ste80-v1
  max_repair_rounds: 2
  glossary:
    workspace:
      definition: "An isolated tenant environment containing projects, artifacts, and run ledgers."
      part_of_speech: noun
      canonical_spelling: "workspace"
      source: "SRS-SECTION-2.1"
    idempotency:
      definition: "The property that repeating the same operation with the same key yields the same state."
      part_of_speech: noun
      canonical_spelling: "idempotency"
      source: "ADR-0009"
```

---

### 3.4. Configuring Custom Skill Bindings (`skill-bindings.yml`) and Model Adapters (`adapters/configs/*.yaml`)

#### A. Binding Your Own Custom Skills into the 297 Skill Slots (`~/.architect-framework/skill-bindings.yml`)

If your organization maintains internal architecture skills (for example, company standards for Spring Boot, Golang, or Kubernetes) and wants to bind them into AAF slots, create `~/.architect-framework/skill-bindings.yml` *(note: place this in `~/.architect-framework/`, not inside the spec workspace directory)*:

```yaml
schema_version: "2026.10"
bindings:
  backend-service-architect:
    path: "/opt/company-skills/golang-microservice-architect"
  security-architect:
    path: "/opt/company-skills/zero-trust-security-skill"
```

#### B. Customizing Model Adapters for Claude, Codex, and DeepSeek (`architect_framework/adapters/configs/`)

When using the Python API / CLI orchestrator (`AdapterRegistry.get_adapter("claude" | "codex" | "deepseek")`), you can customize model parameters under `architect_framework/adapters/configs/`:

* **`claude_config.yaml` (Anthropic Claude):**
  ```yaml
  adapter_name: claude
  model_name: claude-sonnet-4-20250514
  provider: anthropic
  temperature: 0.2
  max_tokens: 8192
  system_prompt_format: xml
  enable_structured_outputs: false
  ```
* **`codex_config.yaml` (OpenAI Codex / GPT-4o / o3):**
  ```yaml
  adapter_name: codex
  model_name: gpt-4o
  provider: openai
  temperature: 0.2
  max_tokens: 8192
  system_prompt_format: markdown
  enable_structured_outputs: false   # Set false when generating 10-section Markdown architecture pages (.md)
  ```
* **`deepseek_config.yaml` (DeepSeek-V3 / DeepSeek-R1 on DeepSeek Harness):**
  ```yaml
  adapter_name: deepseek
  model_name: deepseek-reasoner      # Or deepseek-chat (DeepSeek-V3)
  provider: deepseek
  temperature: 0.0
  max_tokens: 8192
  system_prompt_format: markdown
  extra_params:
    reasoning_mode: true
    strip_think_tags_on_save: true   # Automatically strips <think>...</think> blocks so YAML frontmatter stays on line 1
  ```

---

## 4. Choosing an Operating Mode (`solo-author` vs `governed-team`) & Workspace Scale (`Profile`)

### 4.1. Two Governance Presets

| Attribute | `solo-author` *(Default for individuals & new users)* | `governed-team` *(For Enterprise & Teams)* |
| :--- | :--- | :--- |
| **`policy.mode`** | `advisory` | `enforce` |
| **`first_run_gate`** | `auto` (Runs immediately without waiting for Passkey approval at step 0) | `approve` (Every new task dispatch requires a cryptographic Passkey signature) |
| **Authoring Flow** | Allows the agent to materialize the tree, author across waves, and run `prepare-check` and `sdd check` continuously. | All modifications must go through an isolated candidate (`architect_sdd_propose`) and await Reviewer WebAuthn Passkey sign-off in the Console. |
| **When to Use?** | When you want an AI agent to analyze requirements and generate an entire architecture specification end-to-end in one session. | When multiple architects collaborate on a locked baseline and require strict cryptographic change control. |

### 4.2. Four Architecture Specification Profiles (`selected_profile`)

| Profile | Expected File Count | Typical Runtime | Best Suited For |
| :--- | :--- | :--- | :--- |
| **`seed`** | `3 – 6` files | `1 – 2 min` | Early ideation, PoCs, and initial requirement clarification (`brief.md`, `clarified-requirements.md`, `index.md`). |
| **`minimal`** | `10 – 18` files | `3 – 6 min` | Single microservice, CLI tool, or small app: includes C1/C2 views, 2–3 core ADRs, and primary API & data schemas. |
| **`standard`** | `20 – 60` files | `8 – 15 min` | MVP projects or medium-sized systems (3–6 modules), expanding primary Bounded Contexts and critical runtime flows. |
| **`maximal`** | `100 – 350+` files | `25 – 60 min` | Enterprise / multi-tier SaaS platforms (such as `atlas-spec`): covers 100% of requirement universe $U$, separates every ADR, runtime scenario `SCN-*`, and state machine into dedicated files, and expands all concern slots for every Bounded Context. |

---

## 5. Quick Reference Table for All 16 Commands Across 3 Harnesses (Command Cheat-Sheet)

| # | Category | Claude Code Command | OpenAI Codex Command | DeepSeek Harness (`dsh`) Command | Direct CLI Command (`architect-runtime`) | Primary Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | Onboarding | `/architect` | `/prompts:architect` | `/architect` or `$architect` | `architect-runtime status .` | Interactive wizard to inspect the directory & suggest next steps |
| **2** | Onboarding | `/architect-init` | `/prompts:architect-init` | `/architect-init` | `architect-runtime sdd host-init <dir> ...` | Initialize a new SDD workspace (supports pre-populated folders) |
| **3** | Requirements | `/architect-clarify` | `/prompts:architect-clarify` | `/architect-clarify` | *(Via skill `00-requirement-clarifier`)* | Socratic interview to clarify requirements from a raw idea (`UC-01`) |
| **4** | Routing | `/architect-route` | `/prompts:architect-route` | `/architect-route` | `architect-runtime cli route-skills --query "..."` | Select the right Domain Skill & Task Skill for a problem (`UC-05`) |
| **5** | Design | `/architect-quickstart` | `/prompts:architect-quickstart` | `/architect-quickstart` | `architect-runtime sdd materialize --profile standard` | Fast-track standard MVP architecture in 5–10 minutes (`UC-02`) |
| **6** | Design | `/architect-design` | `/prompts:architect-design` | `/architect-design` | `architect-runtime sdd materialize --profile maximal` | Comprehensive Phase 0 → Phase 5 architecture synthesis (`UC-03`) |
| **7** | Standalone | `/architect-execute` | `/prompts:architect-execute` | `/architect-execute` | *(Executes a `--domain` & `--task` pair)* | Author a single standalone ADR, API contract, or diagram (`UC-05`) |
| **8** | Audit | `/architect-audit` | `/prompts:architect-audit` | `/architect-audit` | `architect-runtime sdd extract-sources --audit` | Audit existing codebase & test evidence against SRS/ADRs (`UC-04`) |
| **9** | Evolution | `/architect-change` | `/prompts:architect-change` | `/architect-change` | `architect-runtime sdd regression <dir> --change <id>` | Evolve architecture for new requirements & impact analysis (`UC-07`) |
| **10** | Verification | `/architect-check` | `/prompts:architect-check` | `/architect-check` | `architect-runtime sdd check <dir> --full` | Run Deterministic, Coverage & Anti-Stub quality gates (`UC-06`) |
| **11** | Critique | `/architect-review` | `/prompts:architect-review` | `/architect-review` | `architect-runtime sdd review-candidate <dir> ...` | Run `02-spec-critic` + JEV Semantic/Language evaluation (`UC-06`) |
| **12** | Orchestration | `/architect-run` | `/prompts:architect-run` | `/architect-run` | `architect-runtime start <dir> --tasks-file ...` | Schedule and resume multi-agent task execution waves |
| **13** | Status | `/architect-status` | `/prompts:architect-status` | `/architect-status` | `architect-runtime status <dir> --json` | View Run progress, 5-axis Coverage Scorecard & Gate status |
| **14** | Skills | `/architect-skills` | `/prompts:architect-skills` | `/architect-skills` | `architect-runtime skills status <dir>` | Inspect 297 skill slots and install `.zip` skill packs (`UC-08`) |
| **15** | Workbench | `/architect-console` | `/prompts:architect-console` | `/architect-console` | `architect-runtime console serve <dir>` | Launch the Web Console for C4 Maps & document review (`UC-08`) |
| **16** | Governance | `/architect-approve` | `/prompts:architect-approve` | `/architect-approve` | `architect-runtime console serve <dir> --enroll` | Guide Passkey enrollment and cryptographic release sign-off (`UC-08`) |

---

## 6. Detailed Reference Guide for Each Command (16 Commands Reference)

> **Cross-Platform CLI Path Convention:** In all CLI examples below, `<RUNTIME>` stands for:
> `python "<PLUGIN_ROOT>/scripts/architect_runtime.py" --bootstrap`
> *(Or simply `architect-runtime` if you have activated the framework's `.venv`).*

---

### 6.1. `/architect` — Interactive Discovery & Onboarding Wizard

* **When to use:** When you open a project directory for the first time and want guidance on which command to run first, or when you want a quick health summary of an existing workspace.
* **Syntax:**
  ```text
  /architect [directory_path]
  ```
* **Detailed Behavior:**
  1. If the directory **does not yet have** `sdd-workspace.yml`:
     * Automatically scans the current directory for requirement documents (`*.md`, `SRS`, `PRD`, `ADR`) and source code folders (`frontend/`, `backend/`, `src/`).
     * Presents 4 tailored workflow tracks:
       * Unclear requirements → Suggests `/architect-clarify`
       * Fast MVP architecture (`15–25` pages) → Suggests `/architect-quickstart`
       * Full Maximal architecture (`100–350` pages) → Suggests `/architect-design --profile maximal`
       * Codebase vs. specification gap audit → Suggests `/architect-audit`
  2. If the directory **already has** `sdd-workspace.yml`:
     * Summarizes completed pages vs. stub pages (`TODO`), displays the 5 coverage metrics, and prints the exact next command to run.

---

### 6.2. `/architect-init` — Initialize an SDD Architecture Workspace

* **When to use:** When you want to initialize a new architecture workspace in an empty folder or directly inside an existing project folder that already contains requirement files or code.
* **Syntax:**
  ```text
  /architect-init [path] [--id <workspace-id>] [--profile seed|minimal|standard|maximal] [--preset solo-author|governed-team] [--reviewer <your_id>]
  ```
* **Flags:**
  * `--id <slug>`: Project identifier slug (defaults to the directory name, e.g., `atlas-spec`).
  * `--profile`: Architecture specification scale (`seed`, `minimal`, `standard`, `maximal` — default: `standard`).
  * `--preset`: `solo-author` (default: `mode: advisory`, no Passkey block) or `governed-team` (`mode: enforce`, requires Passkey sign-off).
  * `--allow-existing-sources`: Allows initialization even when the directory already contains source documents (`SYSTEM_REQUIREMENTS.md`, `.git`, etc.).
* **Equivalent CLI Command:**
  ```powershell
  <RUNTIME> sdd host-init ./atlas-spec --workspace-id atlas-spec --reviewer lead-architect --profile maximal --preset solo-author --allow-existing-sources
  ```
* **Example:**
  ```text
  /architect-init ./atlas-spec --id atlas-spec --profile maximal --preset solo-author
  ```

---

### 6.3. `/architect-clarify` — Socratic Requirement Clarification (`UC-01`)

* **When to use:** When you have an initial concept (a short description) or an early `brief.md` draft with ambiguities that need to be resolved before designing the architecture.
* **Syntax:**
  ```text
  /architect-clarify <idea description or path to brief.md> [--workspace <dir>]
  ```
* **Execution Workflow:**
  1. Automatically loads skill `00-requirement-clarifier` along with `ambiguity-taxonomy.yml` and `interview-question-bank.md`.
  2. Analyzes requirements across 6 dimensions: *Actors & Roles, Core Workflows, Data & State Invariants, Scale & Latency SLOs, Security & Compliance, External Integrations*.
  3. Asks **at most 5 concise questions**, each accompanied by **2–3 Recommended Defaults** so you can reply *"Use defaults"* or customize specific items.
  4. Produces `clarified-requirements.md` with structured IDs (`FR-001..N`, `NFR-001..N`, `BR-001..N`, `ENT-001..N`, `ASM-001..N`).
* **Example:**
  ```text
  /architect-clarify Build a multi-tenant B2B SaaS invoicing and automated payment reminder platform via Email/WhatsApp for 10,000 SMEs with Stripe and local payment gateway integration.
  ```

---

### 6.4. `/architect-route` — Route an Architecture Problem to Specialist Skills (`UC-05`)

* **When to use:** When you want to identify which Domain Skill and Task Skill in AAF's 297-skill catalog own a specific design problem, and check whether those skill slots are installed.
* **Syntax:**
  ```text
  /architect-route <architecture problem description>
  ```
* **Equivalent CLI Command:**
  ```powershell
  <RUNTIME> cli route-skills --query "Design zero-loss event publishing with Transactional Outbox and Kafka"
  <RUNTIME> skills offer <skill-id>
  ```
* **Output:**
  * Routing verdict: `selected` (exact Domain × Task skill pair matched), `ambiguous` (provides a disambiguating question between candidate routes), `blocked`, or `no-route`.
  * Skill slot status (`slot state`): `licensed` / `third-party` / `core` (ready to execute) or `empty`.

---

### 6.5. `/architect-quickstart` — Fast-Track Architecture for Small Projects / MVPs (`UC-02`)

* **When to use:** When you need a complete, compact architecture specification (`12–25` pages) within **5–10 minutes** for a small-to-medium project or MVP.
* **Syntax:**
  ```text
  /architect-quickstart [requirements_file_path] [--out <target_dir>] [--profile minimal|standard]
  ```
* **Automated One-Touch Workflow:**
  1. Initializes the workspace with `selected_profile: standard` and `preset: solo-author`.
  2. Extracts the requirement inventory into `00-plan/source-manifest.md` and `concern-inventory.md`.
  3. Materializes a focused document tree: `architecture/index.md`, System Context (C1), Container View (C2), Deployment View, 3–5 core ADRs, 2–4 primary Bounded Contexts (Overview + API + Data schema), and the Risk Register.
  4. Authors all pages to completion and runs `sdd prepare-check --stamp --style-fix` and `sdd check` until `PASS`.
* **Example:**
  ```text
  /architect-quickstart ./clarified-requirements.md --out ./invoice-mvp-spec
  ```

---

### 6.6. `/architect-design` — Full Production-Grade Architecture Synthesis (`UC-03`)

* **When to use:** When you want to generate a full ISO/IEC/IEEE 42010 architecture specification (especially in `--profile maximal` mode with `100–350+` pages like `atlas-spec`) **without writing a custom System Prompt**.
* **Syntax:**
  ```text
  /architect-design [--profile portfolio|maximal|standard|minimal|seed] [--sources <source_1,source_2,...>] [--out <spec_dir>] [additional notes]
  ```
* **Automated 6-Phase Playbook Inside `/architect-design`:**
  * **Phase 0 — Clean-Slate Init:** Loads the 8 reference files of `01-system-architect` and initializes `<out>` via `sdd host-init`.
  * **Phase 1 — Exhaustive Source Intake (`U`):** Runs `<RUNTIME> sdd extract-sources` to compute SHA-256 digests, count lines across all input files, and extract 100% of `FR-*`, `NFR-*`, `BR-*`, `ADR-*`, `ENT-*`, `SCN-*`, `UC-*`, `GAP-*`, and `CNF-*` items into `source-manifest.md` and `concern-inventory.md`.
  * **Phase 2 — Mechanical Tree Materialization:** Runs `<RUNTIME> sdd materialize --harvest harvest.json --workspace <out>` to:
     * Expand every Bounded Context (Backend, Frontend SPA, AI, Security, Observability, Control Plane) into submodule folders matching `ARCHETYPE_MODULES` (`00-overview`, `11-..`, `12-..`, `20-..`, `self-audit.md`);
     * Materialize each `ADR` as an individual file under `01-global-strategy/05-governance/decisions/NNNN-<slug>.md`;
     * Materialize each runtime scenario `SCN-*` and state machine `SC-SM-*`;
     * Generate `page-spec.json`, partition micro-batches (`waves/w1..w6`, `{wave_name}-batch-{NNN}.json`), and freeze `basis_digest`.
  * **Phase 3 — Rate-Limit Safe Multi-Wave Authoring:**
     * Runs `<RUNTIME> sdd probe-models` to verify healthy subagent models.
     * Dispatches at most `4` parallel subagents (using `Task` on Claude, `codex exec` on Codex, or `subagent` + `send_message` on DeepSeek Harness), assigning `1–2 pages` per batch from `.architect-build/waves/*.json`.
     * Authors every page with all `10 canonical sections`, `180–350 lines`, and all `9 depth dimensions` including `## 3. Executable Boilerplate` and `## 4. Guardrails & Defaults`.
  * **Phase 4 — Built-in Post-Processing & Gate Verification:**
     * Automatically runs `<RUNTIME> sdd prepare-check <out> --tighten --style-fix --stamp` to normalize frontmatter, trim over-budget pages, split sentences exceeding 25 words, and stamp `depth_witnesses`.
     * Runs `<RUNTIME> sdd check <out> --full --out .architect-build/check.json` until `0` stub pages, `0` findings, and all 5 coverage metrics reach `1.0`.
  * **Phase 5 — Sharded Review & Workbench Handoff:**
     * Executes semantic and language review in shards `<= 70 KB (70,000 bytes)`, then returns the executive summary and Web Console URL (`http://localhost:8767/`).
* **Example (Reproducing the complete Atlas specification in a single command):**
  ```text
  /architect-design --profile maximal --sources SYSTEM_REQUIREMENTS.md,Atlas_Tech_Stack_and_ADR_SaaS.md,frontend/atlas-web,frontend-acceptance --out ./atlas-spec
  ```

---

### 6.7. `/architect-execute` — Direct Domain/Task Skill Pair Execution (Standalone `UC-05`)

* **When to use:** When you already know the target Domain Skill and Task Skill (or just ran `/architect-route`) and want to quickly author **a single specialized artifact** (for example, a database selection ADR, a REST API specification, a state machine contract, or an agent workflow design) directly inside your current repository without initializing a full workspace.
* **Syntax:**
  ```text
  /architect-execute --domain <domain-id> --task <task-id> [--standalone] [--out <file_path.md>] <requirement description>
  ```
* **Example:**
  ```text
  /architect-execute --domain database-architect --task adr-authoring --standalone --out ./docs/adr/0007-postgresql-system-of-record.md Compare PostgreSQL 16 against CockroachDB and MongoDB for a core financial ledger requiring strict ACID transactions and Row-Level Security.
  ```

---

### 6.8. `/architect-audit` — Audit an Existing Codebase Against Specifications (`UC-04`)

* **When to use:** When your project already has source code (`frontend/`, `backend/`) or test/acceptance reports (`frontend-acceptance/`) and you want to verify whether the implementation matches the specification (`SRS.md`, `ADR.md`).
* **Syntax:**
  ```text
  /architect-audit <code_or_evidence_path> [--against <srs_adr_path>] [--workspace <dir>]
  ```
* **Outputs:**
  * Detailed comparison matrix between **Specified Requirements** and **Actual Implementation / Test Evidence**.
  * Architecture conflict registry `CNF-01..N` (for example: *SRS mandates 2 isolated SPA applications on separate domains, but the repo only implements 1 SPA*, or *25 acceptance findings `FND-001..025` currently block release*).
  * Updates `source-manifest.md` and `architecture/04-delivery/04-audit/traceability-and-gap-audit.md` (`DELIV-AUDIT`).
* **Example:**
  ```text
  /architect-audit ./frontend/atlas-web ./frontend-acceptance --against ./SYSTEM_REQUIREMENTS.md --workspace ./atlas-spec
  ```

---

### 6.9. `/architect-change` — Requirement Change Management & Ripple Impact Analysis (`UC-07`)

* **When to use:** When you have an existing architecture workspace and need to incorporate a requirement change (adding a feature, swapping a technology, tightening an SLO/timeout, or updating an API contract).
* **Syntax:**
  ```text
  /architect-change <change description or path to change-request.md> [--workspace <dir>]
  ```
* **Execution Workflow:**
  1. Traverses the dependency graph (`sdd_core/graph.py::affected`) from modified concerns/requirements to compute the exact Impact Radius of affected pages.
  2. Updates only the affected pages while preserving the revision history of untouched pages.
  3. Verifies the historical non-regression gate **`DTG-07` (`sdd regression`)**, ensuring no prior `canonical_facts`, `guards`, or `depth_dimensions` are lost.
* **Example:**
  ```text
  /architect-change Require mandatory WebAuthn Passkey step-up authentication for Workspace deletion and tighten search P99 latency SLO from 500ms to 200ms.
  ```

---

### 6.10. `/architect-check` — Deterministic Quality, Coverage & Anti-Stub Gate Check (`UC-06`)

* **When to use:** Whenever you want to verify the completeness of your architecture workspace, detect pages with remaining `TODO`/`TBD` markers, check for broken links, or normalize formatting prior to acceptance review.
* **Syntax:**
  ```text
  /architect-check [workspace-path] [--prepare] [--full] [--change <change-id>]
  ```
* **Flags:**
  * `--prepare`: Runs the automated post-processing pipeline `sdd prepare-check --tighten --style-fix --stamp` before executing `sdd check`.
  * `--full`: Runs all 10 deterministic gates `DTG-01..10`, all 5 coverage metrics, the 180–350 line budget check, anti-stub verification (`PLACEHOLDER_CONTENT_DETECTED`), and 9-dimension `depth_witnesses` verification.
* **Equivalent CLI Command:**
  ```powershell
  <RUNTIME> sdd prepare-check ./atlas-spec --tighten --style-fix --stamp
  <RUNTIME> sdd check ./atlas-spec --full --out ./atlas-spec/.architect-build/check.json
  ```

---

### 6.11. `/architect-review` — Independent Critique (`02-spec-critic`) & AI Judge Evaluation (`UC-06`)

* **When to use:** After `/architect-check` reaches `PASS` on deterministic structure, use this command to run independent architectural critique (pre-mortem analysis, bottleneck detection, cross-document semantic consistency, and STE-80 technical writing evaluation).
* **Syntax:**
  ```text
  /architect-review [workspace-path] [--change <change-id>] [--live] [--critique-only]
  ```
* **Flags:**
  * `--critique-only`: Runs architectural critique using skill `02-spec-critic` and local heuristic style checks without calling paid external APIs.
  * `--live`: Invokes the JEV Judge API (automatically reading `JEV_API_KEY` from `.env` or plugin settings) to evaluate sharded obligation packets (`<= 70 KB/shard`).
* **Equivalent CLI Command:**
  ```powershell
  <RUNTIME> sdd review-candidate ./atlas-spec --change <change-id> --live --out ./atlas-spec/.architect-build/review.json
  <RUNTIME> sdd language-review ./atlas-spec --change <change-id> --live --out ./atlas-spec/.architect-build/lang-review.json
  ```

---

### 6.12. `/architect-run` — Orchestrate a Gated Multi-Agent Run

* **When to use:** When you want to start or resume a multi-agent task plan backed by a durable `SQLite` run ledger, worker lease management (`claim` / `heartbeat` / `complete`), and automatic crash recovery.
* **Syntax:**
  ```text
  /architect-run [workspace-path] [--only <task-id>] [--base-change <change-id>] [--max-workers 4]
  ```
* **Equivalent CLI Command:**
  ```powershell
  <RUNTIME> start ./atlas-spec --tasks-file tasks.json
  <RUNTIME> next ./atlas-spec
  <RUNTIME> control ./atlas-spec --run <run-id> --action pause|resume|cancel|retry
  ```

---

### 6.13. `/architect-status` — Unified Workspace Scorecard & System Status

* **When to use:** To inspect a complete, read-only overview of workspace health without mutating any state.
* **Syntax:**
  ```text
  /architect-status [workspace-path] [--json]
  ```
* **Displayed Information (4 Independent Layers):**
  1. **Task Execution State:** Completed, running, and human-gated tasks.
  2. **Deterministic & Coverage Scorecard:** `PASS`/`INCOMPLETE`/`FAIL` status, the 5 coverage ratios (`source_intake`, `accounting`, `design`, `critical`, `depth`), and complete vs. stub page counts.
  3. **Semantic & Language Review State:** Evaluated vs. pending obligation packets and STE-80 technical language compliance scores.
  4. **Human Acceptance State:** Baseline cryptographic sign-off status and Console launch URL.

---

### 6.14. `/architect-skills` — Manage the 297 Skill Slots & Install Skill Packs (`UC-08`)

* **When to use:** When you want to check which specialist skills out of the 297 skill slots are required by your current workspace, install additional skill packs (`.zip` or directory), or run a skill catalog health check.
* **Syntax:**
  ```text
  /architect-skills [workspace-path]
  /architect-skills install <path_to_zip_or_dir> [--replace]
  /architect-skills offer <skill-id>
  /architect-skills doctor
  ```
* **Equivalent CLI Command:**
  ```powershell
  <RUNTIME> skills status ./atlas-spec
  <RUNTIME> skills offer rag-architect ddd-architect
  <RUNTIME> skills install ./packs/domain-04-ai-architecture.zip
  <RUNTIME> skills doctor
  ```

---

### 6.15. `/architect-console` — Launch the Web Console & Interactive C4 Architecture Map (`UC-08`)

* **When to use:** When you want to visually explore the entire system architecture in your browser: navigate C4 diagrams from System Context (C1) → Bounded Contexts (C2) → Concern Slots & Detailed Documents (C3/C4), filter by runtime scenario, inspect requirement traceability, and read rendered Markdown specifications.
* **Syntax:**
  ```text
  /architect-console [workspace-path] [--port 8767]
  ```
* **Equivalent CLI Command:**
  ```powershell
  <RUNTIME> console serve ./atlas-spec --port 8767
  ```
* **Primary Views in the Web Console (`http://localhost:8767/`):**
  * **`/` (Document Review & C4 Explorer):** Interactive C4 topology map, architecture document tree, high-speed document reader (`< 20ms/page`), Source Evidence inspector, and candidate acceptance sign-off panel.
  * **`/runs` (Runs & Task Gates):** Live multi-agent task progress, task dependency DAG viewer, real-time event stream, and the `Gate Inbox`.

---

### 6.16. `/architect-approve` — Enroll a WebAuthn Passkey & Sign Off Releases (`UC-08`)

* **When to use:** When operating in `governed-team` mode or when you (Lead Architect / Reviewer) want to record a cryptographic sign-off on an architecture specification using a hardware/platform WebAuthn Passkey (Windows Hello / TouchID / YubiKey).
* **Syntax:**
  ```text
  /architect-approve [workspace-path]
  ```
* **Human-Only Ceremony Workflow (Agents cannot forge or bypass signatures):**
  1. Open a dedicated terminal window and run:
     ```powershell
     <RUNTIME> console serve ./atlas-spec --enroll
     ```
  2. Open `http://localhost:8767/` in your browser and click **Register Passkey** for your reviewer identity.
  3. Return to your terminal window, verify the **SHA-256 Fingerprint**, and type the first 8 hex characters to confirm key trust.
  4. Sign dispatch gates or click **Accept Candidate** directly in the browser console.

---

## 7. Hands-On Workflows for 8 Real-World Use Cases (`UC-01` → `UC-08`)

### Scenario 1: Starting from a Short Idea as a New User (`UC-01` → `UC-02`)
```text
Step 1: /architect-clarify Multi-clinic medical appointment booking platform with insurance verification and QR payment integration
        (Answer the agent's 5 guided questions to generate clarified-requirements.md)
Step 2: /architect-quickstart ./clarified-requirements.md --out ./clinic-spec
Step 3: /architect-console ./clinic-spec
```

### Scenario 2: Generating a 300+ Page Maximal Specification from Existing SRS + ADRs (`UC-03`)
```text
Step 1: /architect-design --profile maximal --sources SYSTEM_REQUIREMENTS.md,Atlas_Tech_Stack_and_ADR_SaaS.md --out ./atlas-spec
Step 2: /architect-check ./atlas-spec --prepare --full
Step 3: /architect-review ./atlas-spec --live
Step 4: /architect-console ./atlas-spec
```

### Scenario 3: Authoring a Single Standalone ADR or API Specification in an Existing Code Repo (`UC-05`)
```text
Step 1: /architect-route Design distributed rate limiting and circuit breaker patterns for an API Gateway
Step 2: /architect-execute --domain integration-adapter-architect --task api-gateway-design --standalone --out ./docs/api-gateway-resilience.md
```

### Scenario 4: Auditing Whether Frontend/Backend Implementation Drifted from the SRS (`UC-04`)
```text
Step 1: /architect-audit ./frontend/atlas-web ./frontend-acceptance --against ./SYSTEM_REQUIREMENTS.md --workspace ./atlas-spec
Step 2: /architect-status ./atlas-spec
```

---

## 8. Dual-Mode Mapping Table: MCP Tools ↔ CLI Commands (`architect-runtime`)

This mapping table enables agents across every harness (**Claude Code**, **Codex**, **DeepSeek Harness**) to switch seamlessly between **MCP Tools** and **CLI Commands**:

| Category | MCP Tool Name (`architect-runtime`) | Equivalent CLI Command (`architect_runtime.py --bootstrap ...`) | Authority / Notes |
| :--- | :--- | :--- | :--- |
| **Init & Probe** | `architect_sdd_init` *(New)* | `sdd host-init <ws> --workspace-id <id> --reviewer <rev> [--profile ...] [--preset ...]` | Initialize an SDD workspace |
| **Init & Probe** | `architect_capabilities` | `probe` / `--version` | Query runtime capabilities |
| **Init & Probe** | `architect_doctor` | `doctor <ws>` | Diagnose runtime environment |
| **Intake & Tree** | `architect_sdd_extract` *(New)* | `sdd extract-sources --workspace <ws> --sources <s1,s2...>` | Harvest sources & requirement universe $U$ |
| **Intake & Tree** | `architect_sdd_materialize` *(New)* | `sdd materialize --harvest <harvest.json> --workspace <ws>` | Materialize document tree & freeze digest |
| **Authoring QA** | `architect_sdd_prepare_check` *(New)* | `sdd prepare-check <ws> [--tighten] [--style-fix] [--stamp]` | Normalize frontmatter, tighten lines, stamp witnesses |
| **Check & Read** | `architect_sdd_check` | `sdd check <ws> [--full] [--change <id>] [--out <file>]` | Run Deterministic & Coverage Gates |
| **Check & Read** | `architect_sdd_read` | `sdd read <ws> --artifact <id> [--change <id>]` | Read artifact content at revision |
| **Check & Read** | `architect_style_check` | `sdd style-check <ws> --artifact <id>` | Run STE-80 style check on a single page |
| **Propose & Review** | `architect_sdd_propose` | `sdd changes propose <ws> --skill <id> --expect-snapshot <sha> --file <ops.json>` | Propose revision-bound candidate changes |
| **Propose & Review** | `architect_candidate_review` | `sdd review-candidate <ws> --change <id> [--live] [--force] [--out <file>]` | Full candidate review (Checks + JEV + Language) |
| **Propose & Review** | `architect_language_review` | `sdd language-review <ws> --change <id> [--live] [--force] [--out <file>]` | Run workspace-wide language evaluation |
| **Propose & Review** | `architect_language_repair` | `sdd language-repair <ws> --change <id> --artifact <id> --draft <f> --skill <s_id> --expect-snapshot <sha>` | Fact-preserving STE-80 language repair |
| **Runs & Tasks** | `architect_runtime_plan` | `plan <ws> [--tasks-file <f>]` | Preview multi-agent execution plan |
| **Runs & Tasks** | `architect_runs_start` | `start <ws> --tasks-file <f> [--base-change <id>]` | Start revision-bound task execution plan |
| **Runs & Tasks** | `architect_runtime_status` | `status <ws> [--run <id>] [--json]` | Inspect agent run & gate status |
| **Runs & Tasks** | `architect_runtime_next` | `next <ws> [--run <id>]` | Fetch ready-to-claim tasks |
| **Runs & Tasks** | `architect_task_claim` | `claim <ws> --run <id> --task <task_id>` | Claim task execution with `lease_token` |
| **Runs & Tasks** | `architect_task_heartbeat` | `heartbeat <ws> --run <id> --task <task_id> --lease <token>` | Renew `lease_token` during authoring |
| **Runs & Tasks** | `architect_task_complete` | `complete <ws> --run <id> --task <task_id> --lease <token> --operations-file <f>` | Complete task & commit candidate operations |
| **Runs & Tasks** | `architect_runs_observe` | `observe <ws> [--after <seq>]` | Read durable event stream |
| **Runs & Tasks** | `architect_runs_control` | `control <ws> --run <id> --action pause\|resume\|cancel\|retry [--task <id>]` | Pause / Resume / Cancel / Retry tasks |
| **Skills & Console** | `architect_runtime_skills` | `skills status <ws> [--json]` | Inspect 297 skill slots for the workspace |
| **Skills & Console** | `architect_console_url` | `console serve <ws> [--port 8767]` | Get URL and launch the Web Console |

---

## 9. Troubleshooting Common Issues (Windows, Claude, Codex, DSH)

| Symptom / Error Code | Root Cause | Permanent Fix |
| :--- | :--- | :--- |
| **`WORKSPACE_NOT_INITIALIZED`** when invoking a design command | The current directory does not yet contain `sdd-workspace.yml`. | Run `/architect-init` first (or pass `--out ./<folder-name>` to `/architect-quickstart` / `/architect-design`). |
| **`WORKSPACE_NOT_EMPTY`** when running `host-init` | The target directory already contains requirement files (`SRS.md`, `brief.md`, `.git`). | Add `--allow-existing-sources` to `sdd host-init` or target a dedicated subfolder with `--out ./project-spec`. |
| **Task stuck in `waiting-for-human`** on the very first run | The workspace was initialized with `governed-team` (`first_run_gate: approve`) without an enrolled Passkey. | For solo authoring, initialize with `--preset solo-author` (or set `policy.mode: advisory` in `sdd-workspace.yml`). To sign with a Passkey, run `/architect-approve`. |
| **`sh: command not found` on Windows PowerShell** | Legacy scripts invoked `sh "${CLAUDE_PLUGIN_ROOT}/scripts/runtime.sh"`. | Always invoke the cross-platform Python launcher: `python "<PLUGIN_ROOT>/scripts/architect_runtime.py" --bootstrap ...` (updated across all 16 commands). |
| **`429 Too Many Concurrent Requests` or `402 Plan Limit` during Subagent waves** | Spawning too many concurrent subagents (`> 5`) or hitting quota limits on the default subagent model. | Run `<RUNTIME> sdd probe-models` before wave execution; keep `--max-workers 4` and batch `1–2 pages/turn`. |
| **`UTF-8 BOM` corruption when using `> file.json` on Windows PowerShell** | Windows PowerShell 5.1 `>` redirection writes UTF-16LE or UTF-8 with BOM by default. | Always use the built-in `--out <filepath>` CLI flag (e.g., `sdd check ./spec --full --out check.json`) instead of shell redirection `>`. |
| **DeepSeek-R1 emits `<think>...</think>` tags that break YAML Frontmatter** | Leading `<think>` blocks push the opening `---` YAML frontmatter delimiter below line 1. | Run `<RUNTIME> sdd prepare-check <ws>` (or use `DeepSeekAdapter`, which strips `<think>` tags automatically before saving). |
| **`PROVIDER_NOT_CONFIGURED: Set the configured credential environment variable JEV_API_KEY`** | You defined `JEV_KEY` in `.env` without loading it into the environment, or `JEV_API_KEY` is unset. | Set `JEV_API_KEY=<your_key>` in `.env` (or export `$env:JEV_API_KEY` in PowerShell / configure `.mcp.json`). |
| **`CONFIG_CONFLICT: Conflicting judge API keys in JEV_API_KEY and SDD_JUDGE_API_KEY`** | Both `JEV_API_KEY` and `SDD_JUDGE_API_KEY` are set in the environment with different values. | Assign the exact same key to both variables or unset `SDD_JUDGE_API_KEY` so only `JEV_API_KEY` is used. |
| **`PACK_NOT_INSTALLED` or Slot in `empty` state blocks authoring** | The workspace references one of the 293 commercial domain/task skill slots that is not installed. | Set `ARCHITECT_ALLOW_BASE=1` to author from the base contract, or install the pack via `/architect-skills install <pack.zip>`. |
