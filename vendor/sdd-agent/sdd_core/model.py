from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Protocol


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    data = value if isinstance(value, bytes) else canonical(value)
    return hashlib.sha256(data).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def instant(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("A timezone is required")
    return parsed.astimezone(timezone.utc)


class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    INCOMPLETE = "INCOMPLETE"
    STALE = "STALE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    SKIPPED = "SKIPPED"


class SddError(Exception):
    def __init__(self, code: str, message: str, status: Status = Status.ERROR):
        super().__init__(message)
        self.code, self.status = code, status

    def to_dict(self) -> dict:
        return {"status": self.status.value, "code": self.code, "message": str(self)}


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    subjects: tuple[str, ...] = ()
    status: Status = Status.FAIL
    severity: str = "blocker"
    obligation_id: str | None = None
    evidence: tuple[dict, ...] = ()

    @property
    def id(self) -> str:
        return "F-" + digest(asdict(self))[:20]

    def to_dict(self) -> dict:
        return {"finding_id": self.id, **asdict(self)}


@dataclass
class Result:
    snapshot: str
    findings: list[Finding] = field(default_factory=list)
    expected: int = 0
    scanned: int = 0
    details: dict = field(default_factory=dict)

    @property
    def status(self) -> Status:
        active = [x.status for x in self.findings if x.severity == "blocker"]
        for state in (Status.ERROR, Status.STALE, Status.INCOMPLETE, Status.FAIL):
            if state in active:
                return state
        if self.scanned < self.expected:
            return Status.INCOMPLETE
        return Status.PASS

    @property
    def exit_code(self) -> int:
        return 0 if self.status == Status.PASS else 1 if self.status == Status.FAIL else 3

    def to_dict(self) -> dict:
        return {"status": self.status.value, "snapshot_digest": self.snapshot,
                "expected": self.expected, "scanned": self.scanned,
                "findings": [x.to_dict() for x in self.findings], **self.details}


@dataclass
class Artifact:
    id: str
    path: str
    kind: str
    owner: str
    text: str
    revision: str
    data: Any
    anchors: set[str] = field(default_factory=set)
    links: list[str] = field(default_factory=list)
    clauses: dict[str, dict] = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


@dataclass
class Snapshot:
    digest: str
    files: dict[str, str]
    config: dict
    artifacts: dict[str, Artifact]
    findings: list[Finding]
    engine_version: str


class JudgeProvider(Protocol):
    def review(self, packet: dict) -> dict: ...


class ContractProvider(Protocol):
    def load(self) -> dict: ...


class DecisionStore(Protocol):
    def decisions(self) -> list[dict]: ...


class SnapshotStore(Protocol):
    def save_snapshot(self, snapshot: Snapshot) -> None: ...
    def load_snapshot(self, identifier: str) -> Snapshot: ...
