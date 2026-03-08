---
name: empire-lineage
description: View the structured archive of retired rulers and context
---

# /empire lineage

You are displaying the Empire Lineage — the structured, searchable archive of retired rulers and their context. Lineage is append-only and never deleted.

## File Locations

- **Lineage file:** `~/.claude/projects/<project-key>/empire/lineage.md`

To resolve `<project-key>`: take the absolute project root path containing `.empire/`, replace all `/` with `-`, strip the leading `-`.

## Prerequisite Check

Before doing anything, verify `.empire/` directory exists in the project root. If it does not:

> ⚠️ No Empire found. Run `/empire init` first to found your dynasty.

Then stop.

If `lineage.md` does not exist, there is no lineage yet:

```
📚 No lineage recorded yet. Lineage is created after the first succession.

The current ruler's context will be archived here when succession occurs.
```

## Parse Arguments

The user's input after `/empire lineage` determines the subcommand:

- **No arguments** → Show lineage for the current branch
- **`--branch <name>`** → Show lineage for a specific branch
- **`--search "keyword"`** → Search lineage entries by keyword

---

## Subcommand: Display (no arguments)

1. Read `lineage.md`
2. Get the current git branch name
3. Filter lineage entries to show only rulers from the current branch
4. Display a summary of each ruler:

```
📚 Lineage — branch: <branch>

<For each ruler, most recent first:>

## Claude <number> "<epithet>" (<branch>)
Ruled: <start_date> to <end_date> | Sessions: <count>
Entries: <decision_count> decisions, <observation_count> observations

### Key Decisions
- [decision] <summary> — Why: <why>
- [decision] <summary> — Why: <why>

### Observations
- [observation] <summary>
- [observation] <summary>
```

5. If no rulers from the current branch exist in lineage:

```
📚 No lineage for branch '<branch>' yet. Lineage is created after succession.
```

---

## Subcommand: `--branch <name>`

1. Read `lineage.md`
2. Filter lineage entries to show only rulers from the specified branch `<name>`
3. Display using the same format as the Display subcommand, but with the specified branch
4. If no rulers from that branch exist:

```
📚 No lineage for branch '<name>'. Available branches in lineage:
  - <branch1> (<count> rulers)
  - <branch2> (<count> rulers)
```

If no branches at all exist in lineage, show the "no lineage yet" message instead.

---

## Subcommand: `--search "keyword"`

1. Read `lineage.md`
2. Search all lineage entries (across all branches) for lines containing the keyword (case-insensitive)
3. Display matching entries grouped by ruler:

```
📚 Lineage search: "<keyword>"

Found <count> matches across <ruler_count> rulers:

### Claude <number> "<epithet>" (<branch>)
  - [decision] <matching entry> — Why: <why>
  - [observation] <matching entry>

### Claude <number> "<epithet>" (<branch>)
  - [observation] <matching entry>
```

4. If no matches:

```
📚 No lineage entries matching "<keyword>".
```

---

## Lineage File Format

The `lineage.md` file uses this structure:

```markdown
## Claude III "the Builder" (main)
Ruled: 2026-03-05 to 2026-03-07 | Sessions: 8

### Retired Entries
- [decision] Chose JWT RS256 — Why: asymmetric verification needed
- [observation] Rate limiter applied globally
- [observation] Redis considered, rejected

## Claude II "the Architect" (main)
Ruled: 2026-03-02 to 2026-03-05 | Sessions: 12

### Retired Entries
- [decision] Chose PostgreSQL over MongoDB — Why: relational data model with complex joins
- [observation] Set up CI pipeline with GitHub Actions
```

Each ruler entry is a level-2 heading (`##`) containing:
- **Ruler name and epithet** with branch in parentheses
- **Ruled:** date range and session count
- **Retired Entries** section with typed entries (`[decision]` or `[observation]`)
- Decisions always preserve their `Why:` field — this is sacred and never compressed

## Important

- Lineage is the safety net of the entire Empire system. Nothing is ever truly lost — it ends up here.
- Lineage is append-only. Never modify or delete existing entries.
- The `Why:` field on decisions survives all tiers of compression and must appear verbatim in lineage.
- Lineage is private working state — it lives in the Claude memory directory, not in `.empire/`.
- When displaying, show most recent rulers first (reverse chronological order).
- For `--search`, search is case-insensitive and matches against the full text of entries (descriptions, Why fields, observation text).
