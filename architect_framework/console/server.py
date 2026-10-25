"""specification / specification — `console serve`: the review console on 127.0.0.1.

Plan section 4.5. Standard library only; one process per workspace; loopback only.

  GET  /                   the viewer page, `mode: console`
  GET  /api/model          {site, review}
  GET  /api/packet/<id>    marks when the packet reached the screen (section 5.7 rule 4)
  POST /api/challenge      a draft decision → the digest of the record it would write
  POST /api/decide         the passkey assertion over that digest → the existing writer
  POST /api/enroll/begin   only with `--enroll`
  POST /api/enroll/finish  only with `--enroll`

Two refusals hold everything else up:

  * `POST /api/decide` has **no mode that skips the signature**. An agent that can
    reach the port can read; it cannot decide, because deciding needs a person to
    touch an authenticator (R10, risk V-9). The terminal channel is never offered
    over HTTP.
  * Enrolment — adding a key to the trust root — is off unless the person started
    the server with `--enroll`, a flag the plugin hook refuses to an agent's shell
    (risk V-12). Without it, a `curl` could enrol a key the agent holds.

`Host` must be the loopback address the server bound (DNS rebinding) and a POST's
`Origin` must be the server's own (a web page elsewhere cannot drive it; V-10).
"""

from __future__ import annotations

import importlib.util
import hashlib
import json
import secrets
import sys
import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from architect_framework import contracts
from architect_framework.console import attest
from sdd_core.model import SddError, utc_now

MAX_BODY = 1_000_000
class Refused(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


@dataclass
class ConsoleState:
    workspace: Path
    port: int = 0
    enroll: bool = False
    drafts: dict[str, dict[str, Any]] = field(default_factory=dict)
    enrolments: dict[str, str] = field(default_factory=dict)
    rendered_at: dict[str, str] = field(default_factory=dict)
    rendered_sha: dict[str, str] = field(default_factory=dict)
    lock: threading.Lock = field(default_factory=threading.Lock)
    #: UF-18: served inside the console's own page; a note that carries it is `channel: console`.
    token: str = field(default_factory=lambda: secrets.token_urlsafe(16))
    checking: threading.Lock = field(default_factory=threading.Lock)
    enrollment_approver: Any = None

    @property
    def core(self):
        from architect_framework.sdd_bridge.mode import workspace_mode
        return workspace_mode(self.workspace) == "core"

    # ---------------------------------------------------------------- origin rules
    def hosts(self) -> set[str]:
        return {f"127.0.0.1:{self.port}", f"localhost:{self.port}"}

    def origins(self) -> set[str]:
        return {f"http://{h}" for h in self.hosts()}

    # ---------------------------------------------------------------- reads
    def _core_model(self, change_id=None, *, surface="review"):
        from architect_framework.sdd_bridge.console import model
        from architect_framework.runtime.core_runs import observe
        packet = model(self.workspace, change_id, include_evidence=surface == "review")
        try: packet["runs"] = observe(self.workspace)
        except SddError as error: packet["runs"] = {"status":"ERROR", "error":error.to_dict(), "runs":[], "events":[], "coverage":"unavailable"}
        from architect_framework.sdd_bridge import engine_for
        from sdd_core.label_review import load, verified_approvals
        store = engine_for(self.workspace).store
        summaries = []
        errors = []
        for path in sorted((store.root / "label_manifests").glob("*.json")):
            try:
                corpus = load(store, path.stem)
                approvals = verified_approvals(store, corpus)
                summaries.append({"manifest_id": path.stem, "case_count": len(corpus["cases"]), "independently_reviewed": sum(len({a["actor"] for a in approvals if c["id"] in a["case_ids"]}) >= 2 for c in corpus["cases"]), "qualified": False})
            except (SddError, OSError, UnicodeError) as error:
                errors.append({"manifest_id": path.stem, "code": getattr(error, "code", "LABEL_MANIFEST_UNREADABLE"), "message": str(error)})
        packet["label_manifests"] = summaries
        packet["label_manifest_errors"] = errors
        return packet

    def model(self, surface="review"):
        if surface not in {"review", "workbench"}: raise Refused(400, "Choose review or workbench surface")
        from architect_framework.sdd_bridge.mode import classify
        state = classify(self.workspace)
        if state["state"] != "current":
            return {"site": None, "review": {"setup": state}}
        review_data = self._core_model(surface=surface)
        site_summary = {
            "workspace": review_data.get("workspace"),
            "artifact_count": len(review_data.get("artifacts", [])),
            "status": (review_data.get("report") or {}).get("status", "INCOMPLETE"),
        }
        return {"site": site_summary, "review": review_data}

    def page(self):
        from architect_framework.console.sdd_page import render
        return render(self.model()["review"], self.enroll)

    def version(self):
        from architect_framework.console.serialization import script_json
        return {"version": hashlib.sha256(script_json(self.model()).encode("utf-8")).hexdigest()}

    # ---------------------------------------------------------------- notes (UF-18)
    def note(self, body):
        raise Refused(400, "Notes and document changes use isolated core proposals")

    # ---------------------------------------------------------------- checks (UF-16)
    def check(self, body):
        if not self.core: raise Refused(409, "Initialize or migrate a current workspace first")
        return self._core_model(body.get("change_id"))

    def review_candidate(self, body):
        if not self.core: raise Refused(409, "Current core workspace required")
        if not isinstance(body.get("change_id"), str) or type(body.get("live", False)) is not bool:
            raise Refused(400, "Select a candidate and an explicit live-review choice")
        from architect_framework.sdd_bridge.language import review_candidate
        result = review_candidate(self.workspace, body["change_id"], live=body.get("live", False))
        return {"result": result, "model": self._core_model(body["change_id"])}

    def run_control(self, body):
        if not self.core: raise Refused(409, "Current core workspace required")
        from architect_framework.runtime.core_runs import control
        return control(self.workspace, body.get("run_id"), body.get("action"), body.get("task_id"))

    def challenge(self, body):
        if not self.core: raise Refused(409, "Initialize or migrate a current workspace first")
        return self._core_challenge(body)

    def _core_challenge(self, body):
        from architect_framework.sdd_bridge.console import prepare
        try:
            if body.get("kind") == "eval-labels":
                from sdd_core.label_review import prepare as prepare_labels
                from architect_framework.sdd_bridge import engine_for
                record = prepare_labels(engine_for(self.workspace).store, body.get("manifest_id"), body.get("actor"), body.get("reason"), body.get("case_ids"))
                target = {"kind": "eval-labels", "record": record}
            elif body.get("kind") == "run-gate":
                from architect_framework.runtime.core_runs import prepare_decision
                record = prepare_decision(self.workspace, body.get("run_id"), body.get("task_id"), body.get("actor"), body.get("action"), body.get("reason"), body.get("answers"))
                target = {"kind": "run-gate", "record": record}
            else:
                draft = prepare(self.workspace, body, utc_now())
                record, target = draft["record"], {"kind": "core", "draft": draft}
        except Exception as exc:
            status = getattr(exc, "status", None)
            raise Refused(409 if getattr(status, "value", status) == "STALE" else 400, str(exc)) from exc
        credentials = [r.credential_id for r in attest.load_reviewers(self.workspace) if r.name == record["actor"]]
        if not credentials:
            raise Refused(403, "The reviewer has no trusted passkey on this machine")
        token = secrets.token_urlsafe(16)
        with self.lock:
            self.drafts[token] = {"payload": record, "target": target}
        return {"draft": token, "challenge": attest.b64u(attest.payload_digest(record)), "credentials": credentials}

    def decide(self, body: dict[str, Any]) -> dict[str, Any]:
        if not self.core:
            raise Refused(409, "Initialize or migrate a current workspace first")
        with self.lock:
            draft = self.drafts.pop(str(body.get("draft") or ""), None)
        if draft is None:
            raise Refused(404, "unknown or used draft; ask for a new challenge")
        payload = draft["payload"]
        att = {
            "credential_id": str(body.get("credential_id") or ""),
            "payload_sha256": "sha256:" + attest.payload_digest(payload).hex(),
            "client_data_json": str(body.get("client_data_json") or ""),
            "authenticator_data": str(body.get("authenticator_data") or ""),
            "signature": str(body.get("signature") or ""),
        }
        target = draft["target"]
        if target["kind"] not in {"core", "run-gate", "eval-labels"}:
            raise Refused(400, "Unsupported decision kind")
        who_field, when_field = "actor", "created_at"
        signed = {**payload, "attestation": att}
        bad = attest.verify(signed, attest.load_reviewers(self.workspace), decided_by_field=who_field,
                            when_field=when_field)
        if bad:
            raise Refused(403, f"signature refused: {bad}")
        origin = json.loads(attest.unb64u(att["client_data_json"]).decode("utf-8")).get("origin")
        if origin not in self.origins():
            raise Refused(403, f"signed on {origin!r}, not on this console")
        if target["kind"] == "eval-labels":
            from sdd_core.label_review import commit
            from architect_framework.sdd_bridge import engine_for
            result = commit(engine_for(self.workspace).store, signed)
            return {"written": result, "model": self._core_model()}
        if target["kind"] == "run-gate":
            from architect_framework.runtime.core_runs import record_decision
            from architect_framework.sdd_bridge import decision_verifier
            try:
                result = record_decision(self.workspace, signed, decision_verifier(self.workspace))
            except Exception as exc:
                raise Refused(409, str(exc)) from exc
            return {"written": result, "model": self._core_model()}
        if target["kind"] == "core":
            from architect_framework.sdd_bridge.console import commit
            from sdd_core.model import instant
            if (instant(utc_now()) - instant(payload["created_at"])).total_seconds() > 300:
                raise Refused(409, "Signing challenge expired; review and sign again")
            try:
                result = commit(self.workspace, target["draft"], att)
            except Exception as exc:
                raise Refused(409, str(exc)) from exc
            return {"written": result, "model": self.model()["review"]}
        raise Refused(400, "Unsupported decision kind")

    # ---------------------------------------------------------------- enrol
    def enroll_begin(self, body: dict[str, Any]) -> dict[str, Any]:
        if not self.core:
            raise Refused(409, "Initialize or migrate a current workspace first")
        if not self.enroll:
            raise Refused(403, "enrolment is off: the person starts `console serve --enroll` in their own terminal")
        name = str(body.get("name") or "").strip()
        if self.core:
            from sdd_core.workspace import capture
            from architect_framework.runtime.core_runs import _authority
            live = capture(self.workspace)
            policy, _, _ = _authority(self.workspace, live)
            if name not in policy["reviewers"] or name in live.config.get("skills", {}):
                raise Refused(403, "Choose a configured human reviewer")
        challenge = attest.b64u(secrets.token_bytes(32))
        with self.lock:
            self.enrolments[challenge] = name
        return {"challenge": challenge, "user_id": attest.b64u(secrets.token_bytes(16))}

    def enroll_finish(self, body: dict[str, Any]) -> dict[str, Any]:
        if not self.core:
            raise Refused(409, "Initialize or migrate a current workspace first")
        if not self.enroll:
            raise Refused(403, "enrolment is off")
        try:
            client = json.loads(attest.unb64u(str(body.get("client_data_json") or "")).decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise Refused(400, "clientDataJSON is not valid") from exc
        with self.lock:
            name = self.enrolments.pop(str(client.get("challenge") or ""), None)
        if client.get("type") != "webauthn.create" or name is None or name != str(body.get("name") or ""):
            raise Refused(403, "the registration does not answer a challenge this console issued")
        if client.get("origin") not in self.origins():
            raise Refused(403, f"registered on {client.get('origin')!r}, not on this console")
        # Origin is not administrator authentication: a local HTTP client can
        # supply it. Trust must come from the terminal that enabled enrollment.
        public_key = str(body.get("public_key") or "")
        try:
            attest._public_key(public_key, int(body.get("alg") or 0))
            fingerprint = hashlib.sha256(attest.unb64u(public_key)).hexdigest()
        except (ValueError, TypeError) as exc:
            raise Refused(400, "Invalid registration public key") from exc
        candidate = {"name": name, "credential_id": str(body.get("credential_id") or ""),
                     "key_fingerprint": fingerprint}
        if self.enrollment_approver is None or not self.enrollment_approver(candidate):
            raise Refused(403, "New reviewer keys require confirmation in the console operator's terminal")
        if self.core:
            from sdd_core.workspace import capture
            from architect_framework.runtime.core_runs import _authority
            live = capture(self.workspace)
            policy, _, _ = _authority(self.workspace, live)
            if name not in policy["reviewers"] or name in live.config.get("skills", {}):
                raise Refused(409, "Human reviewer policy changed; register again")
        try:
            path = attest.enroll(self.workspace, name=name, credential_id=str(body.get("credential_id") or ""),
                                 public_key=str(body.get("public_key") or ""), alg=int(body.get("alg") or 0),
                                 when=utc_now())
        except ValueError as exc:
            raise Refused(400, str(exc)) from exc
        return {"written": str(path), "model": self.model()["review"]}


class Handler(BaseHTTPRequestHandler):
    server: ConsoleHTTPServer  # type: ignore[assignment]

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send(self, status: int, body: bytes, ctype: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'unsafe-inline'; "
                         "style-src 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, data: Any) -> None:
        self._send(status, json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _guard(self, post: bool) -> None:
        state = self.server.state
        if self.headers.get("Host", "") not in state.hosts():
            raise Refused(403, "unexpected Host header")
        if post and self.headers.get("Origin", "") not in state.origins():
            raise Refused(403, "cross-origin request refused")

    def do_GET(self) -> None:
        state = self.server.state
        try:
            self._guard(False)
            path = urlsplit(self.path).path
            # A page on another site can make the browser GET our API (an <img>, a <script>):
            # the Host matches, so the Host check lets it through. Opening a packet stamps its
            # reading time, so the API answers only this console's own page (Fetch Metadata).
            # A request without the header (curl, an old browser) is not a cross-site browser load.
            if path.startswith("/api/") and self.headers.get("Sec-Fetch-Site", "same-origin") not in ("same-origin", "none"):
                raise Refused(403, "cross-site request refused")
            if path in ("/", "/index.html"):
                self._send(200, state.page().encode("utf-8"), "text/html; charset=utf-8")
            elif path == "/api/model":
                query = parse_qs(urlsplit(self.path).query)
                self._json(200, state.model((query.get("surface") or ["review"])[0]))
            elif path == "/api/artifact":
                from architect_framework.sdd_bridge import read_artifact
                from architect_framework.console import markdown as md
                query = parse_qs(urlsplit(self.path).query)
                offset = int((query.get("offset") or [0])[0])
                limit = int((query.get("limit") or [250000])[0])
                result = read_artifact(state.workspace, (query.get("id") or [""])[0], (query.get("change") or [None])[0], offset=offset, limit=limit, max_limit=250000)
                expected = (query.get("revision") or [None])[0]
                if expected and result["revision"] != expected: raise Refused(409, "Document revision changed. Refresh before reading or signing.")
                full_text = result.get("text", "")
                frontmatter, body_only = md.split_frontmatter(full_text)
                body_slice = body_only[:200000]
                result = {**result, "rendered_html": md.render(body_slice, result.get("path", "")), "frontmatter": frontmatter}
                self._json(200, result)
            elif path == "/runs":
                if not state.core: raise Refused(409, "Initialize or migrate a core workspace first")
                from architect_framework.console.workbench_page import render
                self._send(200, render(state._core_model(surface="workbench")).encode("utf-8"), "text/html; charset=utf-8")
            elif path == "/api/evaluation-labels":
                if not state.core: raise Refused(409, "Current core workspace required")
                from sdd_core.label_review import packet
                from architect_framework.sdd_bridge import engine_for
                query = parse_qs(urlsplit(self.path).query)
                self._json(200, packet(engine_for(state.workspace).store, (query.get("manifest") or [""])[0], int((query.get("offset") or [0])[0])))
            elif path == "/api/runs":
                if not state.core: raise Refused(409, "Current core workspace required")
                from architect_framework.runtime.core_runs import observe
                query = parse_qs(urlsplit(self.path).query)
                self._json(200, observe(state.workspace, int((query.get("after") or [0])[0]), database_id=(query.get("database_id") or [None])[0], include_snapshot=(query.get("snapshot") or ["0"])[0] == "1"))
            elif path == "/api/version":
                self._json(200, state.version())
            else:
                raise Refused(404, "not found")
        except Refused as exc:
            self._json(exc.status, {"error": str(exc)})
        except Exception as exc:
            status = getattr(exc, "status", None)
            if hasattr(exc, "to_dict"):
                self._json(409 if getattr(status, "value", status) == "STALE" else 400, {"error": str(exc), **exc.to_dict()})
            elif isinstance(exc, (ValueError, TypeError)):
                self._json(400, {"error": str(exc)})
            else:
                self._json(500, {"error": "Internal console error; inspect the workspace and retry"})

    def do_POST(self) -> None:
        state = self.server.state
        try:
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError as exc:
                raise Refused(400, "bad Content-Length") from exc
            if length < 0:
                raise Refused(400, "bad Content-Length")
            if length > MAX_BODY:
                raise Refused(413, "body too large")
            # Read before refusing: a socket closed with unread input is reset, not answered.
            raw = self.rfile.read(length) if length else b""
            self._guard(True)
            try:
                body = json.loads(raw or b"{}")
            except json.JSONDecodeError as exc:
                raise Refused(400, "body is not JSON") from exc
            if not isinstance(body, dict):
                raise Refused(400, "body is not a JSON object")
            route = {"/api/challenge": state.challenge, "/api/decide": state.decide,
                     "/api/enroll/begin": state.enroll_begin, "/api/enroll/finish": state.enroll_finish,
                     "/api/note": state.note, "/api/check": state.check, "/api/review": state.review_candidate,
                     "/api/runs/control": state.run_control}
            fn = route.get(urlsplit(self.path).path)
            if fn is None:
                raise Refused(404, "not found")
            self._json(200, fn(body))
        except Refused as exc:
            self._json(exc.status, {"error": str(exc)})
        except Exception as exc:
            status = getattr(exc, "status", None)
            if hasattr(exc, "to_dict"):
                self._json(409 if getattr(status, "value", status) == "STALE" else 400, {"error": str(exc), **exc.to_dict()})
            elif isinstance(exc, (ValueError, TypeError)):
                self._json(400, {"error": str(exc)})
            else:
                self._json(500, {"error": "Internal console error; inspect the workspace and retry"})


class ConsoleHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, state: ConsoleState, port: int = 0) -> None:
        super().__init__(("127.0.0.1", port), Handler)
        self.state = state
        state.port = self.server_address[1]


def make_server(workspace: Path, *, port: int = 0, enroll: bool = False) -> ConsoleHTTPServer:
    return ConsoleHTTPServer(ConsoleState(Path(workspace).resolve(), enroll=enroll), port)


def url(server: ConsoleHTTPServer, wait: str | None = None) -> str:
    # `localhost`, not 127.0.0.1: WebAuthn refuses an IP address as the relying
    # party id, so a passkey cannot be registered or used on the IP origin.
    base = f"http://localhost:{server.state.port}/"
    return base + (f"#wait={wait}" if wait else "")
