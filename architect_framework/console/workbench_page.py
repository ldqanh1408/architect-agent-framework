"""Operational workbench for current core task runs."""
from pathlib import Path
from .serialization import script_json

STATIC = Path(__file__).parent / "static"


def render(model):
    css = (STATIC / "workbench.css").read_text(encoding="utf-8")
    script = (STATIC / "workbench.js").read_text(encoding="utf-8") + "\n" + (STATIC / "document-graph.js").read_text(encoding="utf-8")
    return ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'><title>AAF Workbench</title>"
            "<style>" + css + "</style></head><body><a class='skip' href='#main'>Skip to content</a>"
            "<header id='header'></header><nav id='nav' aria-label='Workspace'></nav>"
            "<p id='message' role='status' aria-live='polite' aria-atomic='true'></p>"
            "<main id='main' tabindex='-1'></main><script id='core-model' type='application/json'>"
            + script_json(model) + "</script><script>" + script + "</script></body></html>")
