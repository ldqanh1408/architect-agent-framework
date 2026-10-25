"""Small review surface for revision-bound SDD candidates; no legacy ledgers."""
from pathlib import Path
from .serialization import script_json as _safe_json
STATIC = Path(__file__).parent / "static"


def render(model, enrollment=False):
    css = (STATIC / "sdd-console.css").read_text(encoding="utf-8")
    if "setup" in model:
        from html import escape
        state = model["setup"]
        code_str = escape(str(state.get("code", "SETUP_REQUIRED")))
        next_act = escape(str(state.get("next_action", "Initialize or migrate the workspace.")))
        return (
            "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>Workspace setup</title><style>" + css + "</style></head><body>"
            "<a class='skip' href='#main'>Skip to content</a>"
            "<header id='header'><div class='workbench-brand'><h1>Workspace setup</h1></div></header>"
            "<main id='main' tabindex='-1'>"
            "<section class='card'>"
            "<span class='pill' data-state='INCOMPLETE'>" + code_str + "</span>"
            "<p>" + code_str + "</p>"
            "<p>" + next_act + "</p>"
            "<p>Initialize a new empty directory, or migrate old documents into a separate destination. Old approvals do not authorize new work.</p>"
            "<details><summary>Recovery &amp; CLI setup commands</summary>"
            "<pre>architect-runtime console serve &lt;workspace-path&gt;\n"
            "architect-runtime console verify &lt;workspace-path&gt;</pre>"
            "</details>"
            "</section></main></body></html>"
        )
    script = (
        (STATIC / "manual-evidence.js").read_text(encoding="utf-8")
        + "\n"
        + (STATIC / "language-review.js").read_text(encoding="utf-8")
        + "\n"
        + (STATIC / "sdd-console.js").read_text(encoding="utf-8")
        + "\n"
        + (STATIC / "document-graph.js").read_text(encoding="utf-8")
    )
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>SDD review</title><style>" + css + "</style></head><body>"
        "<a class='skip' href='#app'>Skip to content</a>"
        "<nav aria-label='Workspace'><a href='/runs'>Runs, task gates and observation</a>"
        "<a href='/runs#view=documents'>Document graph &amp; reader</a></nav>"
        "<main id='app' tabindex='-1'></main>"
        "<p id='message' role='status' aria-live='polite' aria-atomic='true'></p>"
        "<script>let packet=" + _safe_json(model) + ";const enrollment=" + _safe_json(enrollment) + ";"
        + script + "</script></body></html>"
    )
