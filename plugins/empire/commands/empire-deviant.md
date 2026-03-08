---
name: empire-deviant
description: Flag and resolve contradictions between context sources
---

# /empire deviant

You are managing Deviants — contradictions found between Vault, Day, Dusk, and the actual codebase. Deviants track when context says one thing but reality says another.

## File Locations

- **Deviants file:** `~/.claude/projects/<project-key>/empire/deviants.md`
- **Dynasty state:** `~/.claude/projects/<project-key>/empire/dynasty/<branch>/dynasty.json`

To resolve `<project-key>`: take the absolute project root path containing `.empire/`, replace all `/` with `-`, strip the leading `-`.

## Prerequisite Check

Before doing anything, verify `.empire/` directory exists in the project root. If it does not:

> ⚠️ No Empire found. Run `/empire init` first to found your dynasty.

Then stop.

If `deviants.md` does not exist, treat it as having no deviants.

## Parse Arguments

The user's input after `/empire deviant` determines the subcommand:

- **No arguments** → List all deviants
- **`"description"`** → Flag a new deviant
- **`resolve <id>`** → Resolve deviant by ID number

---

## Subcommand: List (no arguments)

1. Read `deviants.md`
2. Parse all deviant entries (format described below)
3. Read `dynasty.json` for the current branch to get `sessions_since_succession` for session age calculation
4. If no deviants exist:

```
⚡ No deviants recorded. The Empire's context is consistent.

Use `/empire deviant "description"` to flag a contradiction.
```

5. If deviants exist, display them grouped by status:

```
⚡ Deviants: <unresolved_count> unresolved, <resolved_count> resolved

Unresolved:
  #<id> (session <age>) — <description>
  #<id> (session <age>) — <description>

Resolved:
  #<id> [<resolution>] — <description>
```

6. For unresolved deviants at session age 5+, append a nudge:

```
  ⏰ #<id> has been unresolved for <age> sessions. Consider resolving it.
```

7. For unresolved deviants at session age 10+, append a stronger prompt:

```
  🚨 #<id> has been unresolved for <age> sessions! This needs attention. Run `/empire deviant resolve <id>`.
```

---

## Subcommand: Flag new deviant (`"description"`)

1. Read `deviants.md` (or start with empty content)
2. Determine the next ID: find the highest existing `#<id>` and add 1. If no deviants exist, start at 1.
3. Get today's date in `YYYY-MM-DD` format
4. Read `dynasty.json` for the current session count
5. Append a new deviant entry to `deviants.md` in this format:

```markdown
## Deviant #<id> (unresolved, session <current_session>)
Description: <description>
Flagged: <date>
```

6. If the user's description mentions specific files, add a `Files:` line:

```markdown
Files: <file1> vs <file2>
```

7. Ensure the deviants directory exists (create with `mkdir -p` if needed)
8. Write the updated content
9. Confirm:

```
⚡ Deviant #<id> flagged.

## Deviant #<id> (unresolved, session <current_session>)
Description: <description>
Flagged: <date>

Use `/empire deviant resolve <id>` when ready to address it.
```

---

## Subcommand: `resolve <id>`

1. Read `deviants.md`
2. Find the deviant with the matching `#<id>`
3. If not found:

```
❌ Deviant #<id> not found. Use `/empire deviant` to see all deviants.
```

4. If already resolved:

```
ℹ️ Deviant #<id> is already resolved ([<resolution>]).
```

5. If found and unresolved, present the deviant details and the four resolution options:

```
⚡ Resolving Deviant #<id>:

<deviant description and details>

Choose a resolution:
  1. **fix** — Update the conflicting context entry or vault line to match what the code actually does
  2. **update** — Update the code to match what the context says it should do
  3. **accept** — Mark as known tech debt. Keep both the context and code as-is, acknowledge the contradiction
  4. **dismiss** — Remove the deviant. No action needed (false alarm or already fixed)

Which resolution? (fix/update/accept/dismiss)
```

6. Wait for the user's response.

7. Once the user chooses a resolution, update the deviant entry in `deviants.md`:
   - Change `(unresolved, session <n>)` to `(resolved: <resolution>, session <n>)`
   - Add a `Resolved:` date line

8. For **fix** resolution: Ask the user which context entry or vault line needs updating, then help them make the change (e.g., suggest an `/empire vault swap` command).

9. For **update** resolution: Ask the user what code change is needed to match the context. Help them identify the file and make the change.

10. For **accept** resolution: Simply mark it resolved. No further action.

11. For **dismiss** resolution: Simply mark it resolved. No further action.

12. After resolution, confirm:

```
✅ Deviant #<id> resolved ([<resolution>]).
```

---

## Deviant File Format

The `deviants.md` file uses this structure:

```markdown
## Deviant #1 (unresolved, session 3)
Description: Vault says REST-only but GraphQL resolver exists
Files: src/graphql/resolver.ts vs vault line 12
Flagged: 2026-03-08

## Deviant #2 (resolved: accept, session 5)
Description: Config says Redis but we use in-memory cache
Files: src/cache.ts vs vault line 8
Flagged: 2026-03-07
Resolved: 2026-03-08
```

Each deviant entry is a level-2 heading (`##`) with the following fields:
- **Status** in parentheses: `unresolved, session <n>` or `resolved: <type>, session <n>`
- **Description:** — the contradiction description
- **Files:** (optional) — conflicting file paths
- **Flagged:** — date the deviant was created
- **Resolved:** (only for resolved deviants) — date resolved

## Session Age Calculation

The "session age" of a deviant is: `current_session - deviant_session`. Read the current session count from `dynasty.json` field `sessions_since_succession` (or total session count if available). The deviant's session is recorded in its header.

## Important

- Deviants are advisory — they never block anything in the Empire system.
- v1 auto-detection is limited to file-path conflicts (detected during succession). This command handles the manual flagging path.
- Nudge at 5 sessions unresolved, explicit resolution prompt at 10 sessions. These are reminders, not blockers.
- The deviants file is private working state — it lives in the Claude memory directory, not in `.empire/`.
