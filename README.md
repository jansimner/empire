# Empire

**Continuous Context Protocol for Claude Code**

Empire is a Claude Code plugin that manages conversation context through a dynasty succession metaphor inspired by Foundation. Context has a lifecycle -- it is born (Dawn), rules (Day), advises (Dusk), and eventually retires to lineage -- preventing unbounded growth while preserving critical knowledge. Nothing is ever deleted; everything demotes gracefully through tiers.

## The Foundation Metaphor

| Foundation     | Empire                                                    |
|----------------|-----------------------------------------------------------|
| Brother Dawn   | Staged context -- prepared, learning, not yet active      |
| Brother Day    | Active context -- driving current decisions               |
| Brother Dusk   | Archived wisdom -- distilled patterns and learnings       |
| Succession     | Context rotation -- triggered by pressure or manually     |

Each dynasty member earns a regnal name (Claude I, Claude II, ...) and an epithet based on their work ("the Architect", "the Debugger"). Succession happens automatically when context pressure builds, or on demand.

## Installation

```bash
claude plugin add /path/to/empire
```

## Quick Start

```bash
# Found your dynasty
/empire init

# Then just work normally. Empire runs in the background:
# - SessionStart loads your Vault + Day briefing (~80 lines)
# - PostToolUse tracks which context entries are actively referenced
# - Stop evaluates succession pressure and prepares the next session
```

When succession triggers fire, Empire rotates context automatically: Day becomes Dusk, Dawn becomes Day, and a new Dawn is seeded from git state and past wisdom.

## Commands

| Command               | Description                                      |
|-----------------------|--------------------------------------------------|
| `/empire`             | Status dashboard -- current dynasty and pressure |
| `/empire init`        | Found a new dynasty for the current project      |
| `/empire succession`  | Manually trigger succession                      |
| `/empire vault`       | View and manage immortal context (50-line cap)   |
| `/empire deviant`     | Flag or resolve contradictions                   |
| `/empire lineage`     | Search the structured archive of retired context |
| `/empire dawn`        | View or add items staged for the next ruler      |

## How It Works

Empire uses three hooks that run automatically:

- **SessionStart** loads the Vault (permanent truths) and a pre-computed Day briefing into conversation context. Total overhead is roughly 80 lines per session.
- **PostToolUse** tracks file-path and keyword references to score which Day entries are actively relevant.
- **Stop** updates reference scores, generates the next session's briefing, and evaluates whether succession should be suggested.

Succession itself runs in a subagent to avoid polluting the main conversation. The agent categorizes entries as decisions (with sacred `Why:` fields that never compress) or observations (which compress safely since the code is the source of truth). Low-scoring entries demote to structured, searchable lineage -- never deleted, always recoverable.

Each git branch maintains its own dynasty. Switching branches switches dynasties automatically.

## Project Layout

```
empire/
  .claude-plugin/plugin.json   Plugin metadata
  commands/                     Slash command definitions
  agents/                       Subagent definitions (succession)
  hooks/                        Event hooks (Python)
  skills/succession-protocol/   Multi-file succession skill
  core/                         Shared Python utilities
  tests/                        Test suite
```

## License

MIT
