---
name: empire-vault
description: View and manage immortal context (50-line cap)
---

# /empire vault

You are managing the Empire Vault — immortal context that persists across all sessions and successions. The Vault has a hard cap of 50 lines.

## File Locations

- **Vault file:** `.empire/vault.md` (project root, committed to git)
- **Dusk file:** `~/.claude/projects/<project-key>/empire/dynasty/<branch>/dusk.md` (private working state)

To resolve `<project-key>`: take the absolute project root path containing `.empire/`, replace all `/` with `-`, strip the leading `-`.

To resolve `<branch>`: run `git rev-parse --abbrev-ref HEAD`. Sanitize by replacing non-alphanumeric characters (except `_`, `-`, `.`) with `-`.

## Prerequisite Check

Before doing anything, verify `.empire/vault.md` exists. If it does not:

> ⚠️ No Empire found. Run `/empire init` first to found your dynasty.

Then stop.

## Parse Arguments

The user's input after `/empire vault` determines the subcommand:

- **No arguments** → Display vault contents
- **`add "text"`** → Add a line to the vault
- **`remove <line>`** → Remove a line by line number
- **`swap <line> "text"`** → Replace a line with new text

---

## Subcommand: Display (no arguments)

1. Read `.empire/vault.md`
2. Count the number of non-empty lines (the line count for the cap)
3. Display the vault contents with line numbers

Format:

```
🏛️ Vault: <count>/50 lines

<numbered vault contents, each line prefixed with its line number>
```

4. Then check for `[vault-candidate]` entries in Dusk. Read the Dusk file for the current branch and scan for lines containing `[vault-candidate]`.
5. If any vault candidates exist, display them:

```
📋 Waiting for promotion:
  - <candidate text from Dusk>
  - <candidate text from Dusk>
```

6. If no candidates, do not show the "Waiting for promotion" section.

---

## Subcommand: `add "text"`

1. Read `.empire/vault.md`
2. Count current non-empty lines
3. If adding one more line would exceed 50 lines, reject:

```
🏛️ Vault is full (50/50 lines). Use `swap` to replace an entry, or `remove` one first.
```

4. If there is room, append the text as a new line to `.empire/vault.md`
5. Display the updated vault contents using the Display format above
6. Show remaining capacity:

```
✅ Added to vault. <new_count>/50 lines (<remaining> remaining)
```

---

## Subcommand: `remove <line>`

1. Read `.empire/vault.md`
2. Split into lines. Validate that `<line>` is a valid line number (1-based, within range).
3. If invalid:

```
❌ Invalid line number. Vault has <count> lines (use 1-<count>).
```

4. Remove the specified line
5. Write the updated content back to `.empire/vault.md`
6. Display the updated vault contents using the Display format above
7. Confirm:

```
✅ Removed line <line>. <new_count>/50 lines (<remaining> remaining)
```

---

## Subcommand: `swap <line> "text"`

1. Read `.empire/vault.md`
2. Split into lines. Validate that `<line>` is a valid line number (1-based, within range).
3. If invalid:

```
❌ Invalid line number. Vault has <count> lines (use 1-<count>).
```

4. Replace the line at position `<line>` with the new text
5. Write the updated content back to `.empire/vault.md`
6. Display the updated vault contents using the Display format above
7. Confirm:

```
✅ Swapped line <line>. Vault: <count>/50 lines
```

---

## Line Counting Rules

- The 50-line cap counts all non-empty lines in `.empire/vault.md`
- Blank lines and lines that are purely whitespace do NOT count toward the cap
- When displaying line numbers, number ALL lines (including blanks) sequentially starting from 1
- When the user references a line number for `remove` or `swap`, use the sequential line numbering (matching what was displayed)

## Important

- The vault is THE most important context in the entire Empire system. Treat modifications with care.
- Always show the full vault contents after any modification so the user can verify the change.
- Entry types in the vault follow the same `[decision]` / `[observation]` conventions as the rest of Empire. Decisions should include a `Why:` field.
