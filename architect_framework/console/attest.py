"""specification / specification — a decision signed with a passkey, checked offline.

Plan section 4.3: the challenge the browser signs **is** the SHA-256 of the record the
server is about to write (canonical JSON, the `attestation` block left out). So the
signature cannot be detached from the content: change one word of the rationale and
step 1 fails; paste the signature onto another decision and step 3 fails. Nothing
here needs the server that took the signature, or the network — a gate re-runs all
seven steps from the record and `.architect/reviewers.yml`.

The trust root is `.architect/reviewers.yml` (section 4.4): names, credential ids, public
keys. It is committed, owned in CODEOWNERS, and write-denied to agents by the hook.
Attestation is `none`, so this cannot prove the key lives in hardware; a key added
later cannot validate an earlier decision (`enrolled_at` must not be after
`decided_at`), and adding one is a diff on an owned file (risk V-12).

Verification needs the optional `console` extra (`cryptography`). Without it,
`verify` returns a problem naming the install, never a silent pass (specification).
"""

from __future__ import annotations

import base64
import datetime as _dt
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import yaml

ATTESTATION = "attestation"
CHANNEL_PASSKEY = "console-passkey"
CHANNEL_TERMINAL = "terminal"
REVIEWERS_DIR = ".architect"
REVIEWERS_FILE = "reviewers.yml"
LOOPBACK = ("127.0.0.1", "localhost", "[::1]", "::1")
FLAG_UP = 0x01
FLAG_UV = 0x04
ALG_ES256 = -7
ALG_RS256 = -257
INSTALL_HINT = "pip install -e \".[console]\" (the `cryptography` package) to verify passkey signatures"


def b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def unb64u(text: str) -> bytes:
    text = str(text or "")
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def canonical(record: dict[str, Any]) -> bytes:
    """The signed bytes: the record without its attestation, as sorted compact JSON."""
    body = {k: v for k, v in record.items() if k != ATTESTATION}
    return json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str).encode("utf-8")


def payload_digest(record: dict[str, Any]) -> bytes:
    return hashlib.sha256(canonical(record)).digest()


# --------------------------------------------------------------------------- #
# Reviewers — the trust root
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Reviewer:
    name: str
    credential_id: str
    public_key: str
    alg: int
    enrolled_at: str


def project_root(workspace: Path) -> Path:
    """Where `.architect/` lives: the nearest ancestor that has one, else the git root, else the workspace."""
    start = Path(workspace).resolve()
    for base in (start, *start.parents):
        if (base / REVIEWERS_DIR).is_dir():
            return base
    for base in (start, *start.parents):
        if (base / ".git").exists():
            return base
    return start


def reviewers_path(workspace: Path) -> Path:
    return project_root(workspace) / REVIEWERS_DIR / REVIEWERS_FILE


def listed_reviewers(workspace: Path) -> list[Reviewer]:
    """Every reviewer `.architect/reviewers.yml` lists, trusted on this machine or not."""
    path = reviewers_path(workspace)
    if not path.is_file():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    out = []
    for row in data.get("reviewers") or []:
        if isinstance(row, dict) and row.get("credential_id") and row.get("public_key"):
            out.append(Reviewer(str(row.get("name") or ""), str(row["credential_id"]), str(row["public_key"]),
                                int(row.get("alg") or ALG_ES256), str(row.get("enrolled_at") or "")))
    return out


def load_reviewers(workspace: Path) -> list[Reviewer]:
    """The reviewers whose signatures count here.

    `reviewers.yml` is a file in the workspace, and anything that can write it can
    list a software key of its own and sign with it (LP 20, H-2). So once this
    machine has trusted any key for the project, only the keys it trusted count:
    one enrolled here, or confirmed by the person with `console trust-reviewers`
    in their own terminal. A project with no trusted key has no authorised reviewer yet.
    """
    listed = listed_reviewers(workspace)
    trusted = trusted_credentials(workspace)
    if trusted is None:
        return []  # a copied reviewers.yml cannot establish trust on a new machine
    return [r for r in listed if r.credential_id in trusted]


TRUST_FILE = "trusted-reviewers.yml"


def _trust_path() -> Path:
    from architect_framework.runtime.host_state import state_home

    return state_home() / TRUST_FILE


def _trust_key(workspace: Path) -> str:
    return str(project_root(workspace))


def trusted_credentials(workspace: Path) -> set[str] | None:
    """The credential ids this machine trusts for the project, None when it has trusted none yet."""
    path = _trust_path()
    if not path.is_file():
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    row = (data.get("projects") or {}).get(_trust_key(workspace))
    if row is None:
        return None
    if not isinstance(row, dict):
        return set()  # old id-only pins must be explicitly re-trusted
    return {r.credential_id for r in listed_reviewers(workspace)
            if row.get(r.credential_id) == _reviewer_fingerprint(r)}


def _reviewer_fingerprint(reviewer: Reviewer) -> str:
    # Pin identity, key and enrollment time, not only a mutable credential id.
    import dataclasses
    return hashlib.sha256(json.dumps(dataclasses.asdict(reviewer), sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def trust(workspace: Path, credential_ids: list[str]) -> Path:
    """Add credential ids to what this machine trusts for the project. Only enrolment and the person call this."""
    path = _trust_path()
    data = (yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else None) or {}
    projects = data.setdefault("projects", {})
    key = _trust_key(workspace)
    previous = projects.get(key)
    pins = dict(previous) if isinstance(previous, dict) else {}
    listed = {r.credential_id: r for r in listed_reviewers(workspace)}
    for credential in credential_ids:
        if credential not in listed:
            raise ValueError("Cannot trust an unlisted credential")
        pins[credential] = _reviewer_fingerprint(listed[credential])
    projects[key] = pins
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=True, allow_unicode=True), encoding="utf-8", newline="\n")
    return path


def enroll(workspace: Path, *, name: str, credential_id: str, public_key: str, alg: int, when: str) -> Path:
    """specification: append one reviewer. Refuses a duplicate credential and a non-person name."""
    from architect_framework.sdd_bridge import require_core
    from sdd_core.workspace import capture
    from sdd_core.policy import effective_policy
    from sdd_core.storage import Store
    require_core(workspace)
    live, store = capture(workspace), Store(workspace)
    baseline = store.baseline()
    accepted = store.load_snapshot(baseline["snapshot_digest"]) if baseline else None
    policy = effective_policy(live, accepted)
    if name not in policy["reviewers"] or name in live.config.get("skills", {}): raise ValueError("Choose a configured human reviewer")
    if alg not in (ALG_ES256, ALG_RS256):
        raise ValueError(f"alg {alg} is not supported; ES256 (-7) or RS256 (-257)")
    _public_key(public_key, alg)  # refuse a key that does not parse
    path = reviewers_path(workspace)
    data: dict[str, Any] = {"schema_version": 1, "kind": "reviewers", "reviewers": []}
    if path.is_file():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or data
    rows = data.setdefault("reviewers", [])
    if any(str(r.get("credential_id")) == credential_id for r in rows if isinstance(r, dict)):
        raise ValueError("this credential is already enrolled")
    rows.append({"name": name, "credential_id": credential_id, "public_key": public_key, "alg": alg,
                 "enrolled_at": when})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=200), encoding="utf-8",
                    newline="\n")
    trust(workspace, [credential_id])  # enrolled here, by the person at the console: trusted here
    return path


# --------------------------------------------------------------------------- #
# The seven steps
# --------------------------------------------------------------------------- #


def _public_key(der_b64u: str, alg: int):
    try:
        from cryptography.hazmat.primitives.serialization import load_der_public_key
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise RuntimeError(INSTALL_HINT) from exc
    key = load_der_public_key(unb64u(der_b64u))
    return key


def _verify_signature(reviewer: Reviewer, signed: bytes, signature: bytes) -> bool:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import ec, padding

    key = _public_key(reviewer.public_key, reviewer.alg)
    try:
        if reviewer.alg == ALG_ES256:
            key.verify(signature, signed, ec.ECDSA(hashes.SHA256()))  # type: ignore[call-arg]
        else:
            key.verify(signature, signed, padding.PKCS1v15(), hashes.SHA256())  # type: ignore[call-arg]
    except InvalidSignature:
        return False
    return True


def _time(value: Any) -> _dt.datetime | None:
    if isinstance(value, _dt.datetime):
        return value if value.tzinfo else value.replace(tzinfo=_dt.timezone.utc)
    try:
        parsed = _dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=_dt.timezone.utc)


def verify(record: dict[str, Any], reviewers: list[Reviewer], *, decided_by_field: str = "decided_by",
           when_field: str = "decided_at") -> str | None:
    """None when the record's passkey signature holds; otherwise what failed, in words."""
    att = record.get(ATTESTATION)
    if not isinstance(att, dict):
        return "no attestation block"
    try:
        import cryptography  # noqa: F401
    except ImportError:
        return INSTALL_HINT
    digest = payload_digest(record)
    # 1. the payload digest recorded is the one the content has now
    if str(att.get("payload_sha256") or "") != "sha256:" + digest.hex():
        return "step 1: the record changed after it was signed (payload digest differs)"
    try:
        client_raw = unb64u(att.get("client_data_json", ""))
        client = json.loads(client_raw.decode("utf-8"))
        auth = unb64u(att.get("authenticator_data", ""))
        signature = unb64u(att.get("signature", ""))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return "attestation fields are not valid base64url / JSON"
    # 2. an assertion, not a registration
    if client.get("type") != "webauthn.get":
        return f"step 2: clientData type is {client.get('type')!r}, not 'webauthn.get'"
    # 3. the challenge is exactly this record's digest
    if client.get("challenge") != b64u(digest):
        return "step 3: the signed challenge is not this record's digest"
    # 4. a loopback origin
    origin = urlsplit(str(client.get("origin") or ""))
    if origin.scheme not in ("http", "https") or origin.hostname not in [h.strip("[]") for h in LOOPBACK]:
        return f"step 4: origin {client.get('origin')!r} is not a loopback console"
    if len(auth) < 37:
        return "authenticator data is too short"
    if auth[:32] != hashlib.sha256(str(origin.hostname).encode("utf-8")).digest():
        return "the authenticator signed for another relying party id"
    # 5. user present and user verified
    flags = auth[32]
    if not flags & FLAG_UP or not flags & FLAG_UV:
        return "step 5: the authenticator did not report user presence and user verification (UP+UV)"
    # 6. a known key, of the person named, enrolled before the decision
    rid = str(att.get("credential_id") or "")
    reviewer = next((r for r in reviewers if r.credential_id == rid), None)
    if reviewer is None:
        return "step 6: credential is not in .architect/reviewers.yml"
    if reviewer.name != str(record.get(decided_by_field) or ""):
        return f"step 6: credential belongs to {reviewer.name!r}, not {record.get(decided_by_field)!r}"
    enrolled, decided = _time(reviewer.enrolled_at), _time(record.get(when_field))
    if enrolled and decided and enrolled > decided:
        return "step 6: the key was enrolled after the decision it claims to sign"
    # 7. the signature over authenticatorData ‖ SHA-256(clientDataJSON)
    if not _verify_signature(reviewer, auth + hashlib.sha256(client_raw).digest(), signature):
        return "step 7: the signature does not verify with the enrolled key"
    return None
