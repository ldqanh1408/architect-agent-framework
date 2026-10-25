#!/usr/bin/env bash
# Architect Agent Framework -- multi-harness skill & command installer (macOS / Linux / WSL / Git Bash)
# Supports: claude | codex | dsh (deepseek) | opencode | cursor | all

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CATALOG_ROOT="${SCRIPT_DIR}/exported_skills"
if [ -d "${SCRIPT_DIR}/plugins/architect-agent-framework" ]; then
  PLUGIN_ROOT="${SCRIPT_DIR}/plugins/architect-agent-framework"
else
  PLUGIN_ROOT="${SCRIPT_DIR}"
fi
PLUGIN_SKILLS_ROOT="${PLUGIN_ROOT}/skills"
COMMANDS_ROOT="${PLUGIN_ROOT}/commands"
MARKER=".architect-agent-framework"

AGENT="claude"
SCOPE="global"
DEST_OVERRIDE=""
DRY_RUN=0
FORCE=0
UNINSTALL=0
WANT_ALL=0
declare -a WANT_SKILLS=()
declare -a WANT_CLUSTERS=()

c_red=$'\033[31m'; c_grn=$'\033[32m'; c_yel=$'\033[33m'; c_dim=$'\033[2m'; c_off=$'\033[0m'
if [ ! -t 1 ]; then c_red=""; c_grn=""; c_yel=""; c_dim=""; c_off=""; fi

die()  { printf '%serror:%s %s\n' "$c_red" "$c_off" "$*" >&2; exit 1; }
warn() { printf '%swarn:%s %s\n' "$c_yel" "$c_off" "$*" >&2; }
info() { printf '%s\n' "$*"; }

usage() {
  cat <<'END_USAGE'
Architect Agent Framework -- Multi-Harness Installer (Claude Code, Codex, DeepSeek Harness / dsh)

Selection (choose at least one, may be repeated):
  --skill <id>        install one skill by id, e.g. rag-architect or 01-system-architect
  --cluster <slug>    install a whole cluster, e.g. foundation-sdd or task-10-security-design
  --all               install every skill (foundation + runtime + catalog) and 16 commands

Target:
  --agent <name>      claude | codex | dsh | deepseek | opencode | cursor | all   (default: claude)
  --project           install into the current project instead of the home dir
  --dest <path>       install into an explicit directory, ignoring --agent

Behaviour:
  --list              print the catalog (id, cluster, description) and exit
  --list-clusters     print cluster slugs and skill counts, then exit
  --dry-run           print what would happen without touching the filesystem
  --force             overwrite skills that are already installed
  --uninstall         remove the selected skills instead of installing them
  -h, --help          show this help
END_USAGE
}

LIST_MODE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --skill)          [ $# -ge 2 ] || die "--skill needs a value";   WANT_SKILLS+=("$2"); shift 2 ;;
    --cluster)        [ $# -ge 2 ] || die "--cluster needs a value"; WANT_CLUSTERS+=("$2"); shift 2 ;;
    --all)            WANT_ALL=1; shift ;;
    --agent)          [ $# -ge 2 ] || die "--agent needs a value";   AGENT="$2"; shift 2 ;;
    --dest)           [ $# -ge 2 ] || die "--dest needs a value";    DEST_OVERRIDE="$2"; shift 2 ;;
    --project)        SCOPE="project"; shift ;;
    --global)         SCOPE="global"; shift ;;
    --list)           LIST_MODE="skills"; shift ;;
    --list-clusters)  LIST_MODE="clusters"; shift ;;
    --dry-run)        DRY_RUN=1; shift ;;
    --force)          FORCE=1; shift ;;
    --uninstall)      UNINSTALL=1; shift ;;
    -h|--help)        usage; exit 0 ;;
    *)                die "unknown option: $1 (try --help)" ;;
  esac
done

[ -d "$CATALOG_ROOT" ] || [ -d "$PLUGIN_SKILLS_ROOT" ] || die "neither catalog ($CATALOG_ROOT) nor plugin skills ($PLUGIN_SKILLS_ROOT) found"

discover() {
  local skill_md source rel depth kind cluster slug
  local seen_ids=""
  if [ -d "$PLUGIN_SKILLS_ROOT" ]; then
    for sdir in "$PLUGIN_SKILLS_ROOT"/*; do
      [ -d "$sdir" ] && [ -f "${sdir}/SKILL.md" ] || continue
      sname="$(basename "$sdir")"
      printf '%s|foundation-sdd|%s\n' "$sname" "$sdir"
      seen_ids="${seen_ids}|${sname}|"
    done
  fi
  if [ -d "$CATALOG_ROOT" ]; then
    while IFS= read -r skill_md; do
      source="$(dirname "$skill_md")"
      sname="$(basename "$source")"
      case "$seen_ids" in *"|${sname}|"*) continue ;; esac
      rel="${source#"$CATALOG_ROOT"/}"
      depth="$(printf '%s' "$rel" | tr -cd '/' | wc -c)"
      case "$rel" in
        domains/*) kind="domain" ;;
        tasks/*)   kind="task" ;;
        *)         kind="orchestration" ;;
      esac
      if [ "$depth" -ge 2 ]; then
        cluster="$(printf '%s' "$rel" | cut -d/ -f2)"
        slug="$(printf '%s-%s' "$kind" "$cluster" | tr '_' '-' | tr '[:upper:]' '[:lower:]')"
      else
        slug="$kind"
      fi
      printf '%s|%s|%s\n' "$sname" "$slug" "$source"
    done < <(find "$CATALOG_ROOT" -name SKILL.md -type f | sort)
  fi
}

CATALOG="$(discover)"
[ -n "$CATALOG" ] || die "no SKILL.md packages found"

describe() {
  sed -n 's/^description:[[:space:]]*//p' "$1/SKILL.md" 2>/dev/null \
    | head -1 | sed 's/^"//; s/"$//' | cut -c1-110
}

if [ "$LIST_MODE" = "skills" ]; then
  printf '%s\n' "$CATALOG" | while IFS='|' read -r id slug path; do
    printf '%-42s %s%-40s%s %s\n' "$id" "$c_dim" "$slug" "$c_off" "$(describe "$path")"
  done
  printf '\n%s skills available\n' "$(printf '%s\n' "$CATALOG" | wc -l | tr -d ' ')"
  exit 0
fi

if [ "$LIST_MODE" = "clusters" ]; then
  printf '%s\n' "$CATALOG" | cut -d'|' -f2 | sort | uniq -c \
    | awk '{ printf "%-46s %s skills\n", $2, $1 }'
  exit 0
fi

if [ "$WANT_ALL" -eq 0 ] && [ ${#WANT_SKILLS[@]} -eq 0 ] && [ ${#WANT_CLUSTERS[@]} -eq 0 ]; then
  usage
  die "nothing selected -- pass --skill, --cluster, or --all"
fi

SELECTED=""
if [ "$WANT_ALL" -eq 1 ]; then
  SELECTED="$CATALOG"
else
  for want in ${WANT_SKILLS+"${WANT_SKILLS[@]}"}; do
    hit="$(printf '%s\n' "$CATALOG" | awk -F'|' -v w="$want" '$1 == w')"
    if [ -z "$hit" ] && [ -d "$CATALOG_ROOT" ] && find "$CATALOG_ROOT" -path "*/$want/skill-contract.yml" -print -quit | grep -q .; then
      die "'$want' is a skill slot whose content is sold separately -- run: python \"${PLUGIN_ROOT}/scripts/architect_runtime.py\" --bootstrap skills install <downloaded.zip>"
    fi
    [ -n "$hit" ] || die "unknown skill '$want' -- run --list to see valid ids"
    SELECTED="${SELECTED}${hit}"$'\n'
  done
  for want in ${WANT_CLUSTERS+"${WANT_CLUSTERS[@]}"}; do
    hit="$(printf '%s\n' "$CATALOG" | awk -F'|' -v w="$want" '$2 == w')"
    [ -n "$hit" ] || die "unknown cluster '$want' -- run --list-clusters to see valid slugs"
    SELECTED="${SELECTED}${hit}"$'\n'
  done
fi
SELECTED="$(printf '%s' "$SELECTED" | grep -v '^$' | sort -u)"

resolve_dest() {
  local agent="$1"
  if [ -n "$DEST_OVERRIDE" ]; then printf '%s' "$DEST_OVERRIDE"; return; fi
  case "$agent" in
    claude)        [ "$SCOPE" = "project" ] && printf '%s' "$PWD/.claude/skills"          || printf '%s' "$HOME/.claude/skills" ;;
    codex)         [ "$SCOPE" = "project" ] && printf '%s' "$PWD/.agents/skills"          || printf '%s' "$HOME/.agents/skills" ;;
    dsh|deepseek)  [ "$SCOPE" = "project" ] && printf '%s' "$PWD/.dsh/skills"             || printf '%s' "$HOME/.dsh/skills" ;;
    opencode)      [ "$SCOPE" = "project" ] && printf '%s' "$PWD/.opencode/skills"        || printf '%s' "$HOME/.config/opencode/skills" ;;
    cursor)        [ "$SCOPE" = "project" ] && printf '%s' "$PWD/.cursor/skills"          || printf '%s' "$HOME/.cursor/skills" ;;
    *)             die "unknown agent '$agent' -- expected claude, codex, dsh, deepseek, opencode, cursor, or all" ;;
  esac
}

resolve_cmd_dest() {
  local agent="$1"
  if [ -n "$DEST_OVERRIDE" ]; then printf ''; return; fi
  case "$agent" in
    claude)        [ "$SCOPE" = "project" ] && printf '%s' "$PWD/.claude/commands" || printf '%s' "$HOME/.claude/commands" ;;
    codex)         [ "$SCOPE" = "project" ] && printf '%s' "$PWD/.codex/prompts"   || printf '%s' "$HOME/.codex/prompts" ;;
    *)             printf '' ;;
  esac
}

if [ "$AGENT" = "all" ]; then AGENTS=(claude codex dsh opencode cursor); else AGENTS=("$AGENT"); fi

if [ "$DRY_RUN" -eq 0 ] && [ "$UNINSTALL" -eq 0 ]; then
  if command -v python3 >/dev/null 2>&1; then
    python3 "${PLUGIN_ROOT}/scripts/architect_runtime.py" --register-home "$SCRIPT_DIR" >/dev/null 2>&1 || true
  elif command -v python >/dev/null 2>&1; then
    python "${PLUGIN_ROOT}/scripts/architect_runtime.py" --register-home "$SCRIPT_DIR" >/dev/null 2>&1 || true
  fi
fi

total_ok=0 total_skip=0 total_err=0

for agent in "${AGENTS[@]}"; do
  dest="$(resolve_dest "$agent")"
  action="install"; [ "$UNINSTALL" -eq 1 ] && action="uninstall"
  printf '\n%s%s%s -> %s\n' "$c_grn" "$action" "$c_off" "$dest"
  [ "$DRY_RUN" -eq 1 ] && printf '%s(dry run: no files will be written)%s\n' "$c_dim" "$c_off"

  if [ "$DRY_RUN" -eq 0 ] && [ "$UNINSTALL" -eq 0 ]; then
    mkdir -p "$dest" || die "cannot create $dest"
    if [ -d "${PLUGIN_SKILLS_ROOT}/_shared" ]; then
      rm -rf "$dest/_shared" && cp -R "${PLUGIN_SKILLS_ROOT}/_shared" "$dest/_shared" 2>/dev/null || true
    elif [ -d "${CATALOG_ROOT}/_shared" ]; then
      rm -rf "$dest/_shared" && cp -R "${CATALOG_ROOT}/_shared" "$dest/_shared" 2>/dev/null || true
    fi
  fi

  while IFS='|' read -r id slug source; do
    [ -n "$id" ] || continue
    target="$dest/$id"

    if [ "$UNINSTALL" -eq 1 ]; then
      if [ ! -d "$target" ]; then
        total_skip=$((total_skip + 1)); continue
      fi
      if [ ! -f "$target/$MARKER" ] && [ "$FORCE" -eq 0 ]; then
        warn "$id: not installed by this script (no $MARKER) -- skipped, use --force to override"
        total_skip=$((total_skip + 1)); continue
      fi
      if [ "$DRY_RUN" -eq 1 ]; then
        printf '  would remove %s\n' "$target"
      else
        rm -rf "$target"
      fi
      total_ok=$((total_ok + 1))
      continue
    fi

    if [ -d "$target" ] && [ "$FORCE" -eq 0 ]; then
      printf '  %sskip%s   %s (already installed; --force to overwrite)\n' "$c_yel" "$c_off" "$id"
      total_skip=$((total_skip + 1)); continue
    fi

    if [ "$DRY_RUN" -eq 1 ]; then
      printf '  would install %s\n' "$id"
      total_ok=$((total_ok + 1)); continue
    fi

    rm -rf "$target"
    if cp -R "$source" "$target" 2>/dev/null; then
      find "$target" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
      printf 'installed-by: architect-agent-framework\nskill-id: %s\ncluster: %s\n' "$id" "$slug" > "$target/$MARKER"
      total_ok=$((total_ok + 1))
    else
      warn "$id: copy failed"
      total_err=$((total_err + 1))
    fi
  done <<< "$SELECTED"

  if [ "$WANT_ALL" -eq 1 ] && [ -d "$COMMANDS_ROOT" ]; then
    cmd_dest="$(resolve_cmd_dest "$agent")"
    if [ -n "$cmd_dest" ] && [ "$DRY_RUN" -eq 0 ]; then
      if [ "$UNINSTALL" -eq 1 ]; then
        for cmd_file in "$COMMANDS_ROOT"/*.md; do
          rm -f "$cmd_dest/$(basename "$cmd_file")"
        done
      else
        mkdir -p "$cmd_dest"
        for cmd_file in "$COMMANDS_ROOT"/*.md; do
          sed "s|\${CLAUDE_PLUGIN_ROOT}|${PLUGIN_ROOT}|g" "$cmd_file" > "$cmd_dest/$(basename "$cmd_file")"
        done
      fi
    fi
    if [ "$agent" = "dsh" ] || [ "$agent" = "deepseek" ] || [ "$agent" = "codex" ]; then
      for cmd_file in "$COMMANDS_ROOT"/*.md; do
        cmd_id="$(basename "$cmd_file" .md)"
        cmd_target="$dest/$cmd_id"
        if [ "$UNINSTALL" -eq 1 ]; then
          [ -f "$cmd_target/$MARKER" ] && [ "$DRY_RUN" -eq 0 ] && rm -rf "$cmd_target"
          continue
        fi
        if [ "$DRY_RUN" -eq 0 ]; then
          mkdir -p "$cmd_target"
          desc_line="$(sed -n 's/^description:[[:space:]]*//p' "$cmd_file" | head -1)"
          {
            printf -- '---\nname: %s\ndescription: %s\n---\n\n' "$cmd_id" "${desc_line:-Execute AAF command $cmd_id}"
            sed '1,/^---$/d; 1,/^---$/d' "$cmd_file" | sed "s|\${CLAUDE_PLUGIN_ROOT}|${PLUGIN_ROOT}|g"
          } > "$cmd_target/SKILL.md"
          printf 'installed-by: architect-agent-framework\nskill-id: %s\ncluster: commands\n' "$cmd_id" > "$cmd_target/$MARKER"
        fi
      done
    fi
  fi
done

printf '\n%sdone%s  ok=%s skipped=%s failed=%s\n' "$c_grn" "$c_off" "$total_ok" "$total_skip" "$total_err"
if [ "$UNINSTALL" -eq 0 ] && [ "$DRY_RUN" -eq 0 ] && [ "$total_ok" -gt 0 ]; then
  printf 'Restart your agent so it picks up the new skills and commands.\n'
fi
[ "$total_err" -eq 0 ] || exit 1
