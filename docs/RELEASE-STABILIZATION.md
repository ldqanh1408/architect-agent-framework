# Stabilization release procedure

The current candidate is unpublished and NOT_QUALIFIED. Preparing an artifact,
software verification, native qualification, human acceptance and publication
are distinct actions. Preserve the R26 amendment and inherited requirements.

1. Use a clean commit or the explicit source manifest included in a source ZIP.
   Verify `uv lock --check`, install the locked dependencies and run the canonical
   console build. Never export by recursively scanning an arbitrary directory.
2. Run `scripts/prepare_release.py --out ../candidate-new` with the checkout's
   interpreter. It executes source and public tests, builds wheel/sdist/host/free
   bundles, performs clean-install smoke, scans the final bytes and writes an
   artifact inventory plus raw evidence. Use a new directory for every attempt.
3. Keep `source-manifest.json` and private qualification inputs private. A strict
   paid scan needs original-source coverage supplied through `--fingerprints`.
   Never commit the original corpus or its fingerprints to a public repository.
4. Inspect `qualification-local.json`. LOCAL_VERIFIED grants no publication
   authority. The public profile requires complete RG-06 plus actual native-host
   and physical-device evidence. Stable also retains live judge/language, human
   UX, downstream, contributor and recovery obligations from the master plan.
5. Provide hash-bound external reports and detached attestor signatures under
   the exact candidate root. An external evidence subject contains format
   `aaf-external-evidence/v1`, gate ID, artifact-manifest digest, source digest,
   profile, report digest, execution level and UTC creation/expiry. Trusted keys
   are provisioned separately by the operator; a key copied into a dossier is
   not trusted. Fixture keys are never production approvals.
6. Use `release_candidate.py qualify` with the immutable manifest, evidence index,
   target profile and protected `--trusted-attestors` registry. It checks raw
   reports, all mandatory cohorts, skip inventories, signatures and freshness.
   Software conformance may be inherited for the same bytes under the policy;
   it never inherits native/device/model/human execution level.
7. The authorized operator supplies a detached `aaf-release-approval/v1` subject
   containing the manifest digest, qualification digest, version, target channel
   and creation/expiry. Verify it with `release_candidate.py verify-approval`
   and a protected operator-key registry. Recheck qualification immediately
   before publication and pass that result with `--fresh-qualification`; its policy,
   evidence, profile, version and artifact binding must match the approved result. Do not rebuild between approval and upload.
8. Publish only through a protected environment and the intended repository and
   publisher account. Configure reviewers, self-review/bypass and tag restrictions
   on the account; a YAML environment name does not prove these settings exist.
9. Record each channel's remote receipt and independently verified readback.
   `promotion_ledger.py` preserves PARTIALLY_PUBLISHED when one channel succeeds.
   Resume only missing channels using the same approved bytes. Conflicts stop;
   they never overwrite an existing release or reset its history.

## Recovery and incident response

Stop new scheduling, fence stale workers and preserve accepted documents, config,
paid packs, trust registry and receipts. Cancel does not prove host process death.
Use a consistent engine/SQLite backup, not an unverified copy of a live database.
Check store compatibility before using an older binary. An incompatible writer
must remain blocked; never downgrade the database by force or reuse stale signatures.

Pack updates use an interprocess lock and a durable replacement journal. A new
install reconciles an interrupted transaction before changing another pack. A
modified destination causes PACK_RECOVERY_CONFLICT and preserves both the user's
edit and backup for explicit recovery. Process-termination tests cover this
boundary; they are not a certification against power loss or physical disk failure.

Distribution rollback is separate from state recovery. Stop promotion, identify
the affected version/digest, use the channel's withdrawal/yank procedure and
provide a new-version fix plus data recovery instructions. A PyPI yank is not
remote uninstall and exact version pins may still install that version.

Probe immediately after publication, after 24 hours and at pilot completion.
Before pilot, assign a support owner and activity floor. Do not treat an idle
7–14 day period as stability evidence. Preserve original outcomes and denominators.

No live model inference, human signature, native account action or publication
is authorized merely by a successful local script.

An uninstalled package never becomes a host method implicitly. A workspace skill
implemented by the host must explicitly declare `source: host` alongside its
capabilities and write scope. Package skills omit it or use `source: package`.
This declaration chooses the method source; accepted engine grants still control
all writes. During upgrade, review host declarations rather than copying the
setting onto a missing private package.

In the qualified workflow, locked tool installation runs before protected inputs
are provisioned. TestPyPI uses the same prepared bytes and a separate
`testpypi`-scoped detached approval. Stable RG-10/11/12 respectively require signed
live-model, native-host and human-study evidence; swapping report labels is rejected.
