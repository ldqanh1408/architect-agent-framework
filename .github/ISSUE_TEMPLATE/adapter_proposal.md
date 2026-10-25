---
name: Model adapter proposal
about: Propose a new LLM model adapter (e.g. Llama 3.3, Command R+, Qwen 2.5)
title: '[ADAPTER] '
labels: 'adapter-proposal'
assignees: ''
---

## 🤖 Target LLM & Provider
- **Adapter Name**: `e.g. command-r`
- **Model Name**: `command-r-plus`
- **Provider**: `cohere`

## 📝 Prompt Formatting & Payload Schema
- **Format Mode**: `xml` / `chatml` / `markdown` / `json_schema`
- **Tool Calling Style**: Cohere tool specification / native tools

## ⚙️ Default Hyperparameters
- **Temperature**: `0.2`
- **Max Tokens**: `4096`
- **Stop Sequences**: `[...]`

## 🧪 Verification & Test Coverage
Outline how unit tests will validate context resolution for this adapter.
