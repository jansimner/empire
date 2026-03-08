---
name: empire-dawn
description: View and manage staged items for the next ruler
---

# /empire dawn

You are managing Dawn — staged items prepared for the next ruler. Dawn contents become the new Day when succession occurs.

## File Locations

- **Dawn file:** `~/.claude/projects/<project-key>/empire/dynasty/<branch>/dawn.md`

To resolve `<project-key>`: take the absolute project root path containing `.empire/`, replace all `/` with `-`, strip the leading `-`.

To resolve `<branch>`: run `git rev-parse --abbrev-ref HEAD`. Sanitize by replacing non-alphanumeric characters (except `_`, `-`, `.`) with `-`.

## Prerequisite Check

Before doing anything, verify `.empire/` directory exists in the project root. If it does not:

> ⚠️ No Empire found. Run `/empire init` first to found your dynasty.

Then stop.

If the dynasty directory for the current branch does not exist, or `dawn.md` does not exist, that is fine — treat it as an empty Dawn.

## Parse Arguments

The user's input after `/empire dawn` determines the subcommand:

- **No arguments** → Display dawn contents
- **`add "note"`** → Add a note to dawn
- **`remove <line>`** → Remove a line by line number

---

## Subcommand: Display (no arguments)

1. Read the dawn file for the current branch
2. If the file is empty or does not exist:

```
🌅 Dawn: empty — no items staged for the next ruler.

Use `/empire dawn add "note"` to stage items.
```

3. If the file has content, display it with line numbers:

```
🌅 Dawn: <count> staged items

<numbered dawn contents, each line prefixed with its line number>
```

---

## Subcommand: `add "note"`

1. Read the current dawn file (create if it does not exist)
2. Ensure the dynasty directory exists (create it if needed using `mkdir -p`)
3. Append the note as a new line to the dawn file
4. Display the updated dawn contents using the Display format above
5. Confirm:

```
✅ Added to Dawn. <count> items staged.
```

---

## Subcommand: `remove <line>`

1. Read the current dawn file
2. If the file is empty or does not exist:

```
🌅 Dawn is empty — nothing to remove.
```

3. Split into lines. Validate that `<line>` is a valid line number (1-based, within range).
4. If invalid:

```
❌ Invalid line number. Dawn has <count> lines (use 1-<count>).
```

5. Remove the specified line
6. Write the updated content back to the dawn file
7. Display the updated dawn contents using the Display format above
8. Confirm:

```
✅ Removed line <line> from Dawn. <count> items remaining.
```

---

## Important

- Dawn is seeded automatically during succession (from git state + Dusk wisdom), but users can also manually add items they want the next ruler to know about.
- Dawn is private working state — it lives in the Claude memory directory, not in the project's `.empire/` folder.
- Keep Dawn lean. It should typically have 20-30 lines at most. If the user is adding excessive content, gently suggest that Day entries or Vault entries might be more appropriate.
