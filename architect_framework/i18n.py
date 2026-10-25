"""The words a person reads, in the language they chose (specification specification).

The product is sold in English, and the interface was written in Vietnamese. This module is the
seam between the two. A message is written in the source language, Vietnamese, as it always was,
and `tr()` returns it unchanged when `ARCHITECT_LANG=vi`, or its English text from
`data/ui_en.yaml` otherwise. English is the default (specification).

Only what a person reads goes through here: the review console, the prompts and refusals a person
meets in a terminal. Anything a program reads back stays as it is: the answer recorded in a
ledger, a digest, a finding code, a generated page. Translating those would make a decision
signed in one language fail to verify in the other.

    tr("Ký bằng passkey")                     -> "Sign with passkey"        (default)
    trf("Đã ký {id} lúc {at}", id=i, at=t)    -> "Signed {id} at {at}"
"""

from __future__ import annotations

import functools
import os
from pathlib import Path

ENV_LANG = "ARCHITECT_LANG"
#: The languages the interface speaks. `vi` is the source language of every message.
LANGUAGES = ("en", "vi")
TABLE = Path(__file__).resolve().parent / "data" / "ui_en.yaml"


def lang() -> str:
    """`en` unless `ARCHITECT_LANG` starts with `vi`. Read on every call, so a test can switch it."""
    value = (os.environ.get(ENV_LANG) or "en").strip().lower()
    return "vi" if value.startswith("vi") else "en"


@functools.lru_cache(maxsize=1)
def table() -> dict[str, str]:
    """`{vietnamese: english}`. Absent or unreadable: empty, and every message stays as written."""
    import yaml

    try:
        data = yaml.safe_load(TABLE.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return {str(k): str(v) for k, v in (data.get("messages") or {}).items()}


def tr(message: str) -> str:
    """`message` in the chosen language; a message with no translation is shown as written."""
    if lang() == "vi":
        return message
    return table().get(message, message)


def trf(message: str, *args: object, **kwargs: object) -> str:
    """`tr(message)` with `str.format` applied: the placeholders are the same in both languages."""
    return tr(message).format(*args, **kwargs)


def ui_table() -> dict[str, str]:
    """What the browser page receives as `site.labels.ui`: empty for `vi`, whose messages are the keys."""
    return {} if lang() == "vi" else dict(table())
