from __future__ import annotations

import json
import math
import re
import unicodedata
from urllib.parse import unquote, urlsplit
from pathlib import PurePosixPath

from markdown_it import MarkdownIt
import yaml

from .model import Artifact, Finding, SddError, Status, digest


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in result
        except TypeError as exc:
            raise SddError("YAML_KEY", "Only scalar mapping keys are supported") from exc
        if duplicate:
            raise SddError("DUPLICATE_KEY", f"Duplicate mapping key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def parse_yaml(text):
    try:
        value = yaml.load(text, Loader=UniqueLoader)
        bounded_json_tree(value)
        return value
    except (yaml.YAMLError, RecursionError) as exc:
        raise SddError("PARSE_ERROR", str(exc)) from exc


def bounded_json_tree(value, depth=0, ancestors=None, budget=None):
    budget = [100000] if budget is None else budget
    budget[0] -= 1
    if budget[0] < 0:
        raise SddError("DATA_SIZE_UNSUPPORTED", "Expanded structured data exceeds the supported node limit", Status.INCOMPLETE)
    if depth > 80:
        raise SddError("DATA_DEPTH_UNSUPPORTED", "Structured data exceeds the supported nesting limit", Status.INCOMPLETE)
    if isinstance(value, (dict, list)):
        ancestors = ancestors or set()
        if id(value) in ancestors:
            raise SddError("DATA_CYCLE_UNSUPPORTED", "Recursive YAML aliases are not supported", Status.INCOMPLETE)
        parents = ancestors | {id(value)}
        if isinstance(value, dict):
            if any(not isinstance(k, str) for k in value):
                raise SddError("DATA_KEY_UNSUPPORTED", "Use string object keys")
            children = value.values()
        else:
            children = value
        for child in children:
            bounded_json_tree(child, depth + 1, parents, budget)
    elif value is not None and type(value) not in {str, int, float, bool}:
        raise SddError("DATA_TYPE_UNSUPPORTED", "Use JSON-compatible scalar values; quote YAML dates/timestamps", Status.INCOMPLETE)
    elif type(value) is float and not math.isfinite(value):
        raise SddError("DATA_NUMBER_INVALID", "NaN/infinite values cannot be certified")


def unique_json(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise SddError("DUPLICATE_KEY", f"Duplicate JSON key: {k}")
        result[k] = v
    return result


def parse_json(text):
    try:
        value = json.loads(text, object_pairs_hook=unique_json,
                           parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
        bounded_json_tree(value)
        return value
    except (ValueError, TypeError, RecursionError) as exc:
        raise SddError("PARSE_ERROR", str(exc)) from exc


def relative_path(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise SddError("UNSAFE_PATH", repr(value))
    path = PurePosixPath(value)
    if path.is_absolute() or any(p in {"..", ".sdd", ".git"} for p in path.parts) or ":" in path.parts[0]:
        raise SddError("UNSAFE_PATH", value)
    if str(path) != value or value == ".":
        raise SddError("UNSAFE_PATH", value)
    return value


def slug(text: str) -> str:
    return re.sub(r"[^\w\- ]", "", unicodedata.normalize("NFC", text).lower()).replace(" ", "-")


def pointer(data, path: str):
    if path == "":
        return data
    if not path.startswith("/"):
        raise SddError("POINTER_INVALID", path)
    try:
        for token in path[1:].split("/"):
            key = token.replace("~1", "/").replace("~0", "~")
            data = data[int(key)] if isinstance(data, list) else data[key]
        return data
    except (KeyError, IndexError, ValueError, TypeError) as exc:
        raise SddError("POINTER_MISSING", path, Status.INCOMPLETE) from exc


def parse_artifact(identifier: str, meta: dict, text: str) -> Artifact:
    path = relative_path(meta["path"])
    suffix = PurePosixPath(path).suffix.lower()
    data, links, anchors, spans = {}, [], set(), {}
    if re.search(r"(?m)^(<<<<<<< |>>>>>>> )", text):
        raise SddError("MERGE_CONFLICT", path)
    if suffix in {".yaml", ".yml"}:
        data = parse_yaml(text)
    elif suffix == ".json":
        data = parse_json(text)
    elif suffix in {".md", ".markdown", ".txt", ".mmd", ".puml"}:
        body, offset = text, 0
        lines = text.splitlines(keepends=True)
        if lines and lines[0].strip() == "---":
            end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
            if end is None:
                raise SddError("FRONTMATTER_UNCLOSED", path)
            data = parse_yaml("".join(lines[1:end])) or {}
            if not isinstance(data, dict):
                raise SddError("FRONTMATTER_INVALID", path)
            offset = end + 1
            body = "".join(lines[offset:])
        if isinstance(data, dict) and data.get("artifact_id", identifier) != identifier:
            raise SddError("IDENTITY_CONFLICT", f"{path}: frontmatter disagrees with registry")
        tokens = MarkdownIt("commonmark", {"html": True}).parse(body)
        counts = {}
        headings = []
        for i, token in enumerate(tokens):
            if token.type == "heading_open" and i + 1 < len(tokens):
                raw = tokens[i + 1].content
                explicit = re.search(r"\s*\{#([\w.-]+)\}\s*$", raw)
                base = explicit.group(1) if explicit else slug(raw)
                n = counts.get(base, 0)
                name = f"{base}-{n}" if n else base
                counts[base] = n + 1
                anchors.add(name)
                headings.append((name, token.map[0] + offset))
            for child in token.children or []:
                if child.type == "link_open":
                    links.append(child.attrGet("href") or "")
                elif child.type == "image":
                    links.append(child.attrGet("src") or "")
        for i, (name, start_line) in enumerate(headings):
            stop_line = headings[i + 1][1] if i + 1 < len(headings) else len(lines)
            start = len("".join(lines[:start_line]))
            end = len("".join(lines[:stop_line]))
            spans[name] = {"start": start, "end": end, "digest": digest(text[start:end].encode())}
    else:
        raise SddError("FORMAT_UNSUPPORTED", path, Status.INCOMPLETE)
    clauses = {}
    for clause in meta.get("clauses", []):
        if clause["id"] in clauses:
            raise SddError("DUPLICATE_ID", clause["id"])
        if clause["anchor"] not in spans:
            raise SddError("CLAUSE_ANCHOR_MISSING", f"{clause['id']}:{clause['anchor']}")
        clauses[clause["id"]] = {**clause, **spans[clause["anchor"]]}
    return Artifact(identifier, path, meta["kind"], meta["owner"], text, digest(text.encode()),
                    data, anchors, links, clauses, meta)


def resolve_link(source: str, href: str) -> tuple[str, str] | None:
    url = urlsplit(href)
    if url.scheme or url.netloc:
        return None
    path = unquote(url.path)
    if path.startswith("/"):
        raise SddError("LINK_OUTSIDE_WORKSPACE", href)
    parts = list(PurePosixPath(source).parent.parts)
    for part in path.split("/") if path else []:
        if part == "..":
            if not parts:
                raise SddError("LINK_OUTSIDE_WORKSPACE", href)
            parts.pop()
        elif part not in {"", "."}:
            parts.append(part)
    target = "/".join(parts) if path else source
    return target, unquote(url.fragment)
