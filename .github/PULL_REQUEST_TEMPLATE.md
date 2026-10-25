## 📌 Pull Request Overview

### Summary of Changes
Provide a detailed explanation of what changes were made in this PR and why.

### Related Issues
Fixes #(issue number) / Closes #(issue number)

---

## 📐 Type of Change
- [ ] 🐛 Bug fix (non-breaking change fixing an issue)
- [ ] ✨ New feature (non-breaking change adding functionality)
- [ ] 🤖 New Model Adapter (added support for Hermes, Claude, Codex, etc.)
- [ ] 📦 New Skill Package or Catalog expansion
- [ ] 📝 Documentation update
- [ ] ⚙️ CI/CD / Build / Infrastructure update

---

## 🧪 Verification & Testing

- [ ] Executed `python -m pytest -v` (100% passing)
- [ ] Executed `python -m architect_framework.cli.main release-check --skilldir exported_skills` (Gate passed)
- [ ] Updated / Added unit tests in `tests/`
- [ ] Tested CLI commands (`list-skills`, `list-tasks`, `execute --adapter`, etc.)

---

## 🛡️ Checklist
- [ ] My code follows the style guidelines of this project.
- [ ] I have performed a self-review of my code.
- [ ] I have added docstrings and type hints where appropriate.
- [ ] My changes generate no new warnings or lint errors.
- [ ] All package contracts and manifests remain intact.
