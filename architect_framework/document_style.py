"""Partial STE-inspired prose checks and bounded fact-preserving repair.

This profile does not certify ASD-STE100. Missing dictionary, grammar, and
semantic evidence remain explicit. Repaired text is an unpublished candidate.
"""
from collections import Counter
import hashlib
import re
from markdown_it import MarkdownIt

PROFILE = {"id": "aaf-ste80-v1", "standard_reference": "ASD-STE100 Issue 9", "mapping_review": "UNVERIFIED", "glossary_version": "project-plain-terms/v1", "parser": "markdown-it-commonmark+table/sentence-v1", "override_policy": "Explicit versioned project profile and approved glossary exceptions; never alter identifiers or source quotes", "target_percent": 80,
           "implemented": ["sentence-length", "plain-terms", "single-instruction-heuristic"],
           "pending": ["controlled-dictionary", "part-of-speech", "active-voice", "term-consistency", "ambiguity"]}
PLAIN = {"utilize": "use", "commence": "start", "terminate": "stop", "subsequent": "next",
         "prior to": "before", "in order to": "to", "approximately": "about"}


def prose(markdown):
    parser = MarkdownIt("commonmark").enable("table")
    result, quote_depth, paragraph = [], 0, False
    for token in parser.parse(markdown):
        if token.type == "blockquote_open": quote_depth += 1
        elif token.type == "blockquote_close": quote_depth -= 1
        elif token.type in {"paragraph_open", "td_open", "th_open"}: paragraph = True
        elif token.type in {"paragraph_close", "td_close", "th_close"}: paragraph = False
        elif token.type == "inline" and paragraph and not quote_depth:
            text = " ".join(c.content for c in token.children or [] if c.type == "text")
            result.extend(s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip())
    return result


def evaluate(markdown):
    sentences, findings, passed = prose(markdown), [], 0
    for index, sentence in enumerate(sentences):
        problems = []
        if len(re.findall(r"\b[\w'-]+\b", sentence)) > 25: problems.append("sentence-length")
        for term, replacement in PLAIN.items():
            if re.search(r"\b" + re.escape(term) + r"\b", sentence, re.I): problems.append(f"plain-terms: use {replacement}")
        if ";" in sentence: problems.append("single-instruction-heuristic")
        if problems: findings.append({"sentence": index, "text": sentence, "rules": problems})
        else: passed += 1
    source_digest=hashlib.sha256(markdown.encode()).hexdigest()
    profile_digest=hashlib.sha256(__import__('json').dumps(PROFILE,sort_keys=True).encode()).hexdigest()
    return {"status": "INCOMPLETE" if sentences else "NOT_APPLICABLE", "profile": PROFILE,
            "source_digest":source_digest,"profile_digest":profile_digest,
            "numerator":0,"denominator":len(sentences),"checked_subset_numerator":passed,
            "style_coverage":0 if sentences else None,"target":0.8,
            "sentence_ids":[source_digest[:12]+":"+str(i) for i in range(len(sentences))],
            "unknown_rules":list(PROFILE['pending']),
            "exclusion_policy":{"code":"protected literal","blockquotes":"source quotation","headings":"labels","inline_code":"protected literal","prose_in_lists_and_tables":"eligible"},
            "semantic_preservation":"UNKNOWN",
            "profile_complete": False, "asd_certification": "NOT_CERTIFIED", "sentences": len(sentences),
            "checked_rule_coverage_percent": 100 * passed / len(sentences) if sentences else None,
            "full_profile_coverage_percent": 0 if sentences else None,
            "deterministic_status": "PASS" if not findings else "NEEDS_REVIEW", "findings": findings,
            "semantic_review": "NOT_RUN", "next_action": "Obtain qualified style/meaning evidence and human language review"}


def _conservative_meaning_tokens(markdown):
    """Only declared plain-term substitutions may change lexical order/content.

    Actor/action/order cannot be established by counters. Unqualified automatic
    repairs therefore preserve the full ordered token sequence conservatively.
    Broader paraphrases require an independent human candidate review.
    """
    text = markdown.lower()
    for term, replacement in sorted(PLAIN.items(), key=lambda item: -len(item[0])):
        text = re.sub(r"\b" + re.escape(term) + r"\b", replacement, text)
    return tuple(re.findall(r"[\w'-]+", text))


def protected_facts(markdown):
    # Hash full literal matches, not captured link subgroups.
    literals = [m.group(0) for m in re.finditer(r"```[\s\S]*?```|`[^`]*`|\]\([^)]*\)", markdown)]
    return {"meaning_tokens": _conservative_meaning_tokens(markdown),
            "quoted_sources": Counter(hashlib.sha256(line.encode()).hexdigest() for line in markdown.splitlines() if line.lstrip().startswith(">")),
            "normative": Counter(re.findall(r"\b(?:must(?:\s+not)?|shall(?:\s+not)?|should(?:\s+not)?|may(?:\s+not)?|never|not)\b", markdown, re.I)),
            "values": Counter(re.findall(r"\b\d+(?:[.,]\d+)*(?:\s*(?:ms|s|seconds|minutes|hours|days|MB|MiB|USD|%))?\b", markdown)),
            "identities": Counter(re.findall(r"\b[A-Z][A-Z0-9]*(?:[-_][A-Z0-9]+)*\b", markdown)),
            "literals": Counter(hashlib.sha256(s.encode()).hexdigest() for s in literals)}


def repair(markdown, rewrite, style_judge, meaning_judge, roles, max_rounds=2):
    if len(roles) != 3 or len(set(roles)) != 3: raise ValueError("Writer, style and meaning roles must differ")
    if not 1 <= max_rounds <= 2: raise ValueError("Use at most two repair rounds")
    original, safe, records = protected_facts(markdown), markdown, []
    for round_number in range(1, max_rounds + 1):
        try:
            candidate = rewrite(safe, evaluate(safe))
            if not isinstance(candidate, str) or len(candidate) > 50000 or protected_facts(candidate) != original:
                records.append({"round": round_number, "status": "FACT_CHANGE_REJECTED"})
                break
            style = style_judge(candidate, PROFILE)
            meaning = meaning_judge(markdown, candidate)
        except Exception:
            records.append({"round": round_number, "status": "PROVIDER_UNAVAILABLE"})
            break
        if not isinstance(meaning, dict) or meaning.get("status") != "PASS":
            records.append({"round": round_number, "status": "MEANING_UNCONFIRMED"})
            break
        safe = candidate
        records.append({"round": round_number, "status": "SAFE_CANDIDATE", "style": style})
        if isinstance(style, dict) and style.get("status") == "PASS": break
    return {"status": "NEEDS_HUMAN_REVIEW", "text": safe, "rounds": records, "style": evaluate(safe),
            "published": False, "qualified_style_model": False,
            "reason": "Partial checks and callback verdicts do not certify full style or semantic qualification"}


def inspect_artifact(workspace, artifact_id, change_id=None):
    """Check the explicit registered revision; this never grants acceptance."""
    from architect_framework.sdd_bridge import read_artifact
    packet=read_artifact(workspace,artifact_id,change_id,limit=50000)
    result=evaluate(packet['text'])
    return result | {'artifact_id':artifact_id,'revision':packet['revision'],
        'snapshot_digest':packet['snapshot_digest'],'change_id':change_id,
        'input_truncated':packet['has_more'],'authority':'advisory; human review required',
        'status':'INCOMPLETE' if packet['has_more'] else result['status']}
