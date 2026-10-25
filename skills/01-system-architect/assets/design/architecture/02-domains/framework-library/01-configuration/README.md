---
primary_layer: workflow
---
# 01 — Configuration

Configuration surface of the artifact. Every knob the consumer touches has exactly one contract page here.

- [auto-configuration.md](auto-configuration.md) — `@AutoConfiguration` / `spring.factories` / equivalent registration
- [conditional-matrix.md](conditional-matrix.md) — `@ConditionalOn…` truth table
- [configuration-contract.md](configuration-contract.md) — canonical key/type/default/validation table (moved from the flat layout)

Add new files when a new configuration namespace is introduced. Never merge two namespaces into one page — they diverge over time and the reader has to compare two things they can't diff.
