"""specification — the page renderer, run at build time.

Why not a library, and why not the browser (viewer plan section 5.4, decision 5): the page
is derived, so two builds of one file must give the same bytes. A renderer that
changes with a JS or PyPI release breaks that, and the render must run where the
gates run. The cost is that every syntax the tree uses has to be listed here — and
the tree uses a small, measured set: headings, paragraphs, tables (the main content
form), lists, fenced code, block quotes, and inline code, emphasis and links.

Links to another `.md` page become `data-doc` links the viewer opens in place;
everything is escaped first, so a page cannot inject markup into the viewer.
"""

from __future__ import annotations

import html
import posixpath
import re

_FRONTMATTER = re.compile(r"\A---\r?\n.*?\r?\n---\r?\n", re.DOTALL)
_FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})\s*([\w+-]*)")
_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_LIST = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
_TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
_HR = re.compile(r"^\s*([-*_])(\s*\1){2,}\s*$")


def split_frontmatter(text: str) -> tuple[str, str]:
    """(frontmatter without the fences, body)."""
    match = _FRONTMATTER.match(text)
    if not match:
        return "", text
    return match.group(0).strip().strip("-").strip(), text[match.end():]


def _inline(text: str, base: str) -> str:
    """Inline spans. `base` is the page's own path, so relative links resolve."""
    out: list[str] = []
    for i, part in enumerate(re.split(r"(`[^`]+`)", text)):
        if i % 2:
            out.append(f"<code>{html.escape(part[1:-1])}</code>")
            continue
        s = html.escape(part, quote=False)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
        s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lambda m: _link(m.group(1), m.group(2), base), s)
        out.append(s)
    return "".join(out)


#: The only schemes a rendered page may link out to. Anything else — `javascript:`, `data:`,
#: `vbscript:` — would run on the console's own origin, where a passkey signs decisions.
_SAFE_SCHEMES = frozenset({"http", "https", "mailto"})


def _link(label: str, target: str, base: str) -> str:
    target = html.unescape(target)
    scheme = re.match(r"^\s*([A-Za-z][A-Za-z0-9+.-]*):", target)
    if scheme:
        if scheme.group(1).lower() in _SAFE_SCHEMES:
            return f'<a href="{html.escape(target.strip())}" rel="noopener noreferrer">{label}</a>'
        return f'<span class="link-local" title="{html.escape(target)}">{label}</span>'
    path, _, anchor = target.partition("#")
    if path.endswith(".md"):
        resolved = posixpath.normpath(posixpath.join(posixpath.dirname(base), path)) if base else path
        return f'<a href="#" data-doc="{html.escape(resolved)}">{label}</a>'
    if not path and anchor:
        return f'<a href="#" data-anchor="{html.escape(anchor)}">{label}</a>'
    return f'<span class="link-local" title="{html.escape(target)}">{label}</span>'


def _cells(row: str) -> list[str]:
    row = row.strip()
    row = row.removeprefix("|")
    if row.endswith("|") and not row.endswith("\\|"):
        row = row[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", row)]


def render(text: str, base: str = "") -> str:
    """Markdown body (frontmatter stripped) → HTML. Deterministic; never empty for a non-empty page."""
    _, body = split_frontmatter(text)
    lines = body.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    para: list[str] = []
    i = 0

    def flush() -> None:
        if para:
            out.append(f"<p>{_inline(' '.join(s.strip() for s in para), base)}</p>")
            para.clear()

    while i < len(lines):
        line = lines[i]
        fence = _FENCE.match(line)
        if fence:
            flush()
            marker, lang = fence.group(2), fence.group(3)
            code: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(marker[0] * len(marker)):
                code.append(lines[i])
                i += 1
            i += 1
            cls = f' class="lang-{html.escape(lang)}"' if lang else ""
            label = f'<span class="lang">{html.escape(lang)}</span>' if lang else ""
            out.append(f"<pre{cls}>{label}<code>{html.escape(chr(10).join(code))}</code></pre>")
            continue
        heading = _HEADING.match(line)
        if heading:
            flush()
            level = len(heading.group(1))
            title = heading.group(2)
            anchor = re.sub(r"[^\w\s-]", "", title.lower()).strip().replace(" ", "-")
            out.append(f'<h{level} id="{html.escape(anchor)}">{_inline(title, base)}</h{level}>')
            i += 1
            continue
        if "|" in line and i + 1 < len(lines) and _TABLE_SEP.match(lines[i + 1]):
            flush()
            head = _cells(line)
            rows: list[list[str]] = []
            i += 2
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append(_cells(lines[i]))
                i += 1
            th = "".join(f"<th>{_inline(c, base)}</th>" for c in head)
            trs = "".join("<tr>" + "".join(f"<td>{_inline(c, base)}</td>" for c in r) + "</tr>" for r in rows)
            out.append(f'<div class="table"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>')
            continue
        if line.lstrip().startswith(">"):
            flush()
            quoted: list[str] = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                quoted.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append(f"<blockquote>{render(chr(10).join(quoted), base)}</blockquote>")
            continue
        if _LIST.match(line):
            flush()
            i = _list(lines, i, out, base)
            continue
        if _HR.match(line):
            flush()
            out.append("<hr>")
            i += 1
            continue
        if not line.strip():
            flush()
            i += 1
            continue
        if line.lstrip().startswith("<!--"):
            flush()
            while i < len(lines) and "-->" not in lines[i]:
                i += 1
            i += 1
            continue
        para.append(line)
        i += 1
    flush()
    return "\n".join(out)


def _list(lines: list[str], i: int, out: list[str], base: str) -> int:
    """A (possibly nested) list starting at `lines[i]`; returns the next index."""
    first = _LIST.match(lines[i])
    indent = len(first.group(1))
    ordered = first.group(2)[0].isdigit()
    tag = "ol" if ordered else "ul"
    items: list[str] = []
    while i < len(lines):
        m = _LIST.match(lines[i])
        if not m or len(m.group(1)) < indent:
            if lines[i].strip() and not m and lines[i].startswith(" " * (indent + 2)) and items:
                items[-1] += " " + _inline(lines[i].strip(), base)
                i += 1
                continue
            break
        if len(m.group(1)) > indent:
            nested: list[str] = []
            i = _list(lines, i, nested, base)
            items[-1] += "".join(nested)
            continue
        text = m.group(3)
        box = re.match(r"^\[([ xX])\]\s+(.*)$", text)
        if box:
            mark = "☑" if box.group(1).lower() == "x" else "☐"
            items.append(f'<span class="box">{mark}</span> {_inline(box.group(2), base)}')
        else:
            items.append(_inline(text, base))
        i += 1
    out.append(f"<{tag}>" + "".join(f"<li>{x}</li>" for x in items) + f"</{tag}>")
    return i


def block_tags(rendered: str) -> dict[str, int]:
    """Count of block elements — the measure specification is graded on (viewer plan section 3.7)."""
    return {tag: len(re.findall(rf"<{tag}[\s>]", rendered))
            for tag in ("h1", "h2", "h3", "p", "pre", "table", "ul", "ol", "blockquote")}
