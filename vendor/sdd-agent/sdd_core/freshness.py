from __future__ import annotations

from datetime import timedelta
import ipaddress
import socket
from urllib.parse import urlsplit
import uuid

import httpx

from .model import Finding, SddError, Status, digest, instant, utc_now
from .parsing import parse_json, pointer


def source_binding(source):
    return digest(source)


def confirmation_binding(snapshot, source):
    from .validation import subject_revision
    obligations = [o for o in snapshot.config["obligations"] if o.get("active", True) and source["id"] in o.get("external_sources", [])]
    subjects = {s for o in obligations for s in [o["source"], *o["consumers"]]}
    return digest({"source": source_binding(source), "obligations": obligations,
                   "revisions": {s: subject_revision(snapshot, s) for s in sorted(subjects)}})


def observe(store, source: dict, transport=None, now=None):
    url = urlsplit(source["url"])
    if url.scheme != "https" or not url.hostname or url.username or url.password:
        raise SddError("SOURCE_URL_INVALID", "Sources require an explicit HTTPS URL without credentials")
    record = {"observation_id": "OBS-" + uuid.uuid4().hex, "source_id": source["id"],
              "source_binding": source_binding(source), "version": source["version"],
              "observed_at": now or utc_now(), "status": "UNKNOWN", "content_digest": None}
    try:
        # A blocked fetch is still an observation failure: do not leave an
        # older successful observation looking current after this attempt.
        if transport is None:
            try:
                addresses = {item[4][0] for item in socket.getaddrinfo(url.hostname, url.port or 443)}
            except OSError:
                addresses = set()
            if any(not ipaddress.ip_address(address).is_global for address in addresses):
                raise SddError("SOURCE_ADDRESS_DENIED", "External observation requires a public source", Status.INCOMPLETE)
        with httpx.Client(transport=transport, follow_redirects=False, trust_env=False, timeout=15) as client:
            with client.stream("GET", source["url"]) as response:
                record["http_status"] = response.status_code
                if response.status_code != 200:
                    raise SddError("SOURCE_RETRIEVAL_ERROR", f"HTTP {response.status_code}", Status.INCOMPLETE)
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > source.get("max_bytes", 1024 * 1024):
                        raise SddError("SOURCE_RESPONSE_LIMIT", source["id"], Status.INCOMPLETE)
                content = bytes(body)
                if "json_pointer" in source:
                    value = pointer(parse_json(content.decode("utf-8")), source["json_pointer"])
                    content_digest = digest(value)
                else:
                    content_digest = digest(content)
                record.update({"status": "OBSERVED", "content_digest": content_digest})
    except (httpx.HTTPError, SddError, UnicodeDecodeError) as exc:
        record["error_code"] = exc.code if isinstance(exc, SddError) else "SOURCE_RETRIEVAL_ERROR"
    with store.lock():
        record["sequence"] = 1 + max((o.get("sequence", 0) for o in store.list("observations")), default=0)
        store.write("observations", record["observation_id"], record, immutable=True)
    return record


def latest_observations(store, snapshot):
    bindings = {s["id"]: source_binding(s) for s in snapshot.config.get("external_sources", [])}
    latest = {}
    for record in store.list("observations"):
        identifier = record["source_id"]
        if record.get("source_binding") == bindings.get(identifier):
            if identifier not in latest or (record.get("sequence", 0), instant(record["observed_at"])) > (latest[identifier].get("sequence", 0), instant(latest[identifier]["observed_at"])):
                latest[identifier] = record
    return [latest[k] for k in sorted(latest)]


def freshness(store, snapshot, now=None, before=None):
    now = instant(now or utc_now())
    observations = {o["source_id"]: o for o in latest_observations(store, snapshot)}
    findings, details = [], []
    required = {s for o in snapshot.config["obligations"] if o.get("active", True) for s in o.get("external_sources", [])}
    from .policy import effective_policy, verify_authority
    policy = effective_policy(snapshot, before)
    decisions = []
    for decision in store.decisions():
        try:
            verify_authority(store, decision, policy)
        except SddError:
            continue
        decisions.append(decision)
    for source in snapshot.config.get("external_sources", []):
        if source["id"] not in required:
            continue
        observation = observations.get(source["id"])
        state, reason = "CURRENT", "Source has current, reviewed evidence"
        confirmations = [d for d in decisions if d.get("kind") == "confirm_source" and source["id"] in d.get("scope", [])
                         and d.get("actor") in snapshot.config["policy"]["reviewers"]
                         and d.get("source_version") == source["version"]
                         and d.get("confirmation_context_digest") == confirmation_binding(snapshot, source)
                         and (not d.get("expires_at") or instant(d["expires_at"]) > now)]
        if observation is None or observation["status"] != "OBSERVED":
            state, reason = "UNKNOWN", "No successful current observation; last retrieval may have failed"
        elif instant(observation["observed_at"]) > now:
            state, reason = "UNKNOWN", "Observation timestamp is in the future"
        elif source.get("expected_digest") and observation["content_digest"] != source["expected_digest"]:
            state, reason = "REVIEW_REQUIRED", "Observed source differs from the pinned contract"
        else:
            revoked_sequence = max((x.get("sequence", 0) for x in store.list("observations")
                              if x["source_id"] == source["id"] and x.get("source_binding") == source_binding(source)
                              and x.get("status") == "OBSERVED" and x.get("content_digest") != observation["content_digest"]), default=None)
            valid = [d for d in confirmations if d.get("observed_digest") == observation["content_digest"]
                     and (revoked_sequence is None or d.get("observation_sequence", -1) > revoked_sequence)
                     and any(x["observation_id"] == d.get("observation_id") and x.get("source_binding") == source_binding(source)
                             and x.get("content_digest") == observation["content_digest"] and x.get("status") == "OBSERVED"
                             for x in store.list("observations"))]
            last = max((instant(d["created_at"]) for d in valid), default=None)
            if last is None or last > now or now >= last + timedelta(seconds=source["max_age_seconds"]):
                state, reason = "REVIEW_DUE", "Fetch alone does not renew semantic validity; a source review is due"
        details.append({"source_id": source["id"], "state": state, "owner": source["owner"], "reason": reason})
        if state != "CURRENT":
            findings.append(Finding("FRESHNESS_" + state, reason, (source["id"],), Status.INCOMPLETE))
    return findings, details
