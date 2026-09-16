# Graft Context Layer Integration for AI Coding Agents

## 1. What is Graft?

[Graft](https://github.com/trailhq/Graft) (published on npm as `@nanonets/graft`) is a specialized **codebase context layer** and **Model Context Protocol (MCP) server** designed for autonomous AI coding agents (Claude Code, Antigravity / Gemini, Cursor, Codex).

### The Problem it Solves
When an AI agent is tasked with building or refactoring code in a multi-module repository, standard behavior is reactive:
1. Agent lists directories (`list_dir`).
2. Agent runs multiple string/regex greps (`grep_search`).
3. Agent reads several candidate files (`view_file`), consuming tokens and accumulating context window bloat.
4. Latency increases with every round-trip tool call.

```
Without Graft:
[User Prompt] ──> [Tool: list_dir] ──> [Tool: grep] ──> [Tool: view_file] ──> [Agent Reasoning]
(High token usage, 40-60% extra latency, risk of missing subtle cross-module linkages)
```

### The Solution: Deterministic Code Graphs
Graft parses your repository using **Tree-sitter** (deterministic Abstract Syntax Tree parsing) and maps all classes, functions, modules, and cross-file dependencies into a linked graph of lightweight markdown nodes in a local `graft/` folder:

```
With Graft:
[User Prompt] ──> [Graft Context Graph / MCP Query] ──> [Targeted Precise Action]
(Immediate topological orientation, fewer exploratory tool calls, lower latency)
```

---

## 2. Two-Tiered Architecture: Structural vs. Concept Layers

Graft operates in two modes:

1. **Deterministic Structural Graph (`graft build`)**:
   - Uses local AST parsing via Tree-sitter.
   - Zero LLM API calls, completely free and instant.
   - Maps symbols, function signatures, import chains, and class definitions.
   - Works immediately on uncommitted, dirty git working trees.

2. **Semantic Concept Layer (`graft build --deep`)**:
   - Leverages an LLM provider (Azure OpenAI, OpenAI, or Anthropic).
   - Generates plain-English summaries explaining *why* specific subsystems exist and how data flows across architectural boundaries.

---

## 3. Repository Integration Architecture

```
Azure_VoiceAI/
├── .gitignore                <-- Add 'graft/' to prevent committing large graph state
├── graft/                    <-- Local graph cache (nodes, AST links, symbol indices)
├── .claude/ or mcp_config    <-- Agent wiring configuration (MCP server entry)
└── src/                      <-- Source code parsed by Tree-sitter
    ├── core/
    ├── telephony/
    ├── speech/
    ├── brain/
    ├── rag/
    ├── actions/
    └── merger/
```

### Why Graft Fits the MedFront / AuraCare Architecture
Our repository uses the **5-Module Isolated Architecture** (`telephony`, `speech`, `brain`, `rag`, `actions`, `merger`). As the team implements independent modules, Graft automatically maintains the dependency graph between:
- `src/core/config.py` settings and their consumers in `src/brain/` or `src/telephony/`.
- Function-calling tool schemas in `src/actions/` and their orchestrator in `src/brain/`.
- Audio streams in `src/speech/` and the WebSocket handler in `src/merger/`.
