# Shared package content

One copy of the 30 files that were byte-identical in all 294 packages. Skill packages reference these rather than carrying their own copy, so a package is only valid inside a catalog that has this directory — install by cluster, not by single package.

Nothing here is skill-specific. Anything that varies per skill stays in the package.

## Validators

- `scripts/check_skill_package.py <package_dir>` — package integrity. Takes the skill id from the directory name.
- `scripts/check_output_docs.py <current_workspace>` — generated artifact checks.
- `scripts/run_postflight.py <package_dir> <output_root> <state_file>` — runs the output check and atomically persists `complete` only on success.

Commands fail closed and are safe on paths containing spaces.
