# App-level user stories

```markdown
# Specification Module

[Figma section](<url from screens.json>)

## User stories

As a product manager, I want to browse and filter specifications so that I can find the right record quickly.

As a product manager, I want to create a new specification through a guided flow so that required fields are captured consistently.

## Journeys

Each journey is a sequence of **source → destination** steps. Use page names (and step or dialog names when relevant). Every step names where the user starts and where they end up.

### Journey 1: Browse and filter specifications

1. **Specification List** → **Specification List** (filtered table) — type in search field
2. **Specification List** → **Dialog: Advanced Filters** — tap filter icon
3. **Dialog: Advanced Filters** → **Specification List** (filtered table) — tap Search with criteria

### Journey 2: Create a new specification

1. **Specification List** → **Create Specification** (General details) — tap Create
2. **Create Specification** (General details) → **Create Specification** (Additional details) — tap Next when valid
3. **Create Specification** (Additional details) → **Create Specification** (Review) — tap Next
4. **Create Specification** (Review) → **Specification List** (success toast) — tap Submit

### Journey 3: Row actions from the list

1. **Specification List** → **Dialog: Row options** — tap row kebab menu
2. **Dialog: Row options** → **View Specification** — tap View
3. **Dialog: Row options** → **Edit Specification** (General details) — tap Edit
4. **Dialog: Row options** → **Create Specification** (General details, prefilled) — tap Clone
5. **Dialog: Row options** → **Dialog: Delete message** — tap Delete
6. **Dialog: Delete message** → **Specification List** (row removed) — confirm Delete

### Journey 4: Discard in-progress create

1. **Create Specification** (any step) → **Dialog: Discard message** — tap Discard
2. **Dialog: Discard message** → **Specification List** — tap Yes, discard
3. **Dialog: Discard message** → **Create Specification** (same step) — tap Stay on page

## Acceptance criteria

- User can filter the table via search and via Advanced Filters.
- User can open row actions (View, Edit, Clone, Delete) from the more-options menu.
- User can start create from the list and move through wizard steps; Next enables when required fields are valid.
- User can navigate from the list to Create Specification and back via Discard or Submit.
```

## Journey rules

- One numbered step per navigation or meaningful state change.
- Every step uses **Source → Destination — action** (bold the source and destination in markdown).
- Source and destination must match page names used in `<NN>-<slug>/spec.md` and `build-order.md`.
- Dialogs use `Dialog: <name>`; wizard steps use `Page name (Step name)`.
- Journeys must reflect **real click paths** from the flow map (`screens.json` taps), not Figma frame order.
- Include return paths (Discard, Back, Cancel, close dialog) when they appear in the prototype.
