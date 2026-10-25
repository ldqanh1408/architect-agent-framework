"""The words the console shows for the framework's internal vocabulary.

A reviewer reads `api_contract`, `consumesApi`, `required_seam` and has to translate
them in their head. This module is the one place those codes get a Vietnamese name;
the page receives the table inside the site IR (`site.labels`) and never types a word
of its own (risk V-1). The code stays visible next to the name where it matters — a
reviewer must still be able to search the repository for it.

An unknown code is shown as itself: a missing label is a gap to fill here, not a
reason to hide the value.
"""

from __future__ import annotations

import re

from architect_framework.i18n import lang as ui_lang, tr, trf, ui_table

PAGE_CLASS = {
    "overview": "Tổng quan",
    "mechanism": "Cơ chế",
    "diagram": "Sơ đồ",
    "api_contract": "Hợp đồng API",
    "requirement": "Yêu cầu",
    "verification": "Kiểm định",
    "artifact": "Thành phần",
    "data_entity": "Thực thể dữ liệu",
    "viewpoint": "Góc nhìn",
    "governance_record": "Hồ sơ quản trị",
    "event_message": "Thông điệp sự kiện",
    "test_strategy": "Chiến lược kiểm thử",
    "adr": "Quyết định kiến trúc (ADR)",
    "planning": "Kế hoạch",
    "decision": "Quyết định",
    "standard_entry": "Tiêu chuẩn",
    "repository_documentation": "Mô tả kho mã",
    "unspecified": "Chưa phân loại",
    "audit_report": "Báo cáo kiểm toán",
    "use_case": "Ca sử dụng",
    "runtime_scenario": "Kịch bản vận hành",
    "change_request": "Yêu cầu thay đổi",
    "blocking_finding": "Phát hiện chặn",
}

#: Read as "<from> <label> <to>".
EDGE_KIND = {
    "consumesApi": "gọi API của",
    "providesApi": "cung cấp API cho",
    "publishesEvent": "phát sự kiện tới",
    "subscribesEvent": "nhận sự kiện từ",
    "dependsOn": "phụ thuộc vào",
    "relatesTo": "liên quan tới",
}

OBLIGATION = {
    "mandatory": "bắt buộc",
    "required_seam": "bắt buộc, chờ bằng chứng",
    "conditional": "có điều kiện",
    "derived": "tự sinh",
}

LEVEL = {
    "seed": "hạt giống",
    "minimal": "tối thiểu",
    "standard": "tiêu chuẩn",
    "maximal": "đầy đủ",
    "portfolio": "danh mục",
}

#: The page flags of the site IR (model.py FLAG_*): one word each, everywhere (specification section 7).
FLAG = {
    "scaffold-slot": "khung trống",
    "unrendered-template": "chưa điền mẫu",
    "thin": "ít nội dung",
    "out-of-plan": "ngoài kế hoạch",
    "derived": "tự sinh",
    "template-residue": "còn chữ hướng dẫn",
}

#: The decision checkpoints' states as the overview shows them (overview.checkpoints).
CHECKPOINT_STATE = {
    "not-due": "chưa tới hạn",
    "missing": "đang chờ ký",
    "pending": "đang chờ ký",
    "valid": "đã ký",
    "stale": "cũ — tài liệu đổi sau khi ký",
    "rejected": "bị từ chối",
    "invalid": "bản ghi hỏng",
}

#: The runtime's run states (service.status) and the two the console adds.
RUN_STATE = {
    "none": "chưa có run nào",
    "waiting": "đang chờ người",
    "stalled": "đang kẹt",
    "finished": "đã xong",
    "refused": "bị từ chối khi khởi động",
    "unavailable": "không đọc được (thiếu phần runtime)",
    "static": "chỉ có ở bàn duyệt",
}

#: Kinds of clause in clarified-requirements.md.
CLAUSE_KIND = {
    "CLR": "yêu cầu",
    "ASM": "giả định",
    "OQ": "câu hỏi mở",
    "GAP": "khoảng trống",
    "NG": "ngoài phạm vi",
}

#: A decision as the sign form shows it; the stable code stays the option's value (specification).
DECISION = {
    "approve": "Đồng ý",
    "approve-with-conditions": "Đồng ý kèm điều kiện",
    "reject": "Từ chối",
}

#: A skill slot's state (the slot resolver's vocabulary), as the operations screen shows it (specification).
SLOT_STATE = {
    "licensed": "đã mua, đã cài",
    "third-party": "ruột bên ngoài",
    "empty": "khe rỗng",
    "base": "ruột miễn phí",
    "core": "đi kèm khung",
    "error": "lỗi khi đọc",
}

#: The plan's per-class questions (`workspace_plan._question`) — the same sentence for
#: every page of a class, so a list shows the class instead and the reader shows this.
QUESTION = {
    "what does this subtree own": "Nhánh này sở hữu những gì?",
    "how does this mechanism behave, and what happens when it fails":
        "Cơ chế này chạy thế nào, và khi hỏng thì sao?",
    "what is this entity, who owns it, and what is its lifecycle":
        "Thực thể này là gì, ai sở hữu, vòng đời ra sao?",
    "what is the structure this view shows": "Góc nhìn này cho thấy cấu trúc gì?",
    "what is verified, and against which contract": "Kiểm định điều gì, đối chiếu với hợp đồng nào?",
    "what does this page contain": "Trang này chứa gì?",
}
_CONTAIN = re.compile(r"^what does (.+) contain$")


def question(text: str | None) -> str:
    """The plan question in Vietnamese; a question nobody templated stays as written."""
    if not text:
        return ""
    if text in QUESTION:
        return tr(QUESTION[text])
    m = _CONTAIN.match(text)
    if m:
        return trf("Trang này chứa gì về {0}?", m.group(1))
    return text


def glossary(lang: str | None = None) -> list[dict[str, str]]:
    """The shared words of every surface (specification): `[{id, term, means}]` in one language."""
    from architect_framework import contracts

    lang = lang or ui_lang()
    if not contracts.available("ui-glossary"):
        return []
    rows = contracts.raw("ui-glossary").get("terms") or []
    return [{"id": r["id"], "term": r[lang]["term"], "means": r[lang]["means"]} for r in rows if lang in r]


def _words(names: dict[str, str]) -> dict[str, str]:
    """A table of the interface's words in the chosen language (the module constants are the Vietnamese source)."""
    return {code: tr(name) for code, name in names.items()}


def table() -> dict:
    """What the page receives as `site.labels`, in the chosen language (specification)."""
    return {"page_class": _words(PAGE_CLASS), "edge_kind": _words(EDGE_KIND), "obligation": _words(OBLIGATION),
            "level": _words(LEVEL), "flag": _words(FLAG), "checkpoint_state": _words(CHECKPOINT_STATE),
            "run_state": _words(RUN_STATE), "clause_kind": _words(CLAUSE_KIND), "decision": _words(DECISION),
            "slot_state": _words(SLOT_STATE), "glossary": glossary(), "ui": ui_table()}
