---
name: figma-write-spec
description: >-
  Step 4 (final) of figma-images-to-spec. Write app-level user-stories.md,
  build-order.md, and per-page spec.md. Use when drafting the Figma module
  documentation from a flow map and layout notes, before handing off to
  /speckit.specify.
disable-model-invocation: true
---

# Write specification

Write documentation from the flow map + layout notes. **Three layers:**

| Layer | File | Content |
|-------|------|---------|
| App | `user-stories.md` | Who, why, journeys, acceptance criteria for the whole module |
| Build order | `build-order.md` | WaveMaker implementation sequence — step, page, images, dialogs, notes |
| Page spec | `<NN>-<slug>/spec.md` | Source images, layout, dialogs, interactions, integration (complete page spec) |

Use **tabs** for hierarchy inside page files (one tab per level). Slug page folders from page names (`Specification List` → `specification-list`). **WaveMaker page** names are PascalCase (`SpecificationList`).

Do **not** write `tasks.md` or a Spec Kit `spec.md` here — that is core `/speckit.specify`'s job after this pipeline finishes.

## Output tree

```
figma-specs/<module>/
  user-stories.md
  build-order.md
  01-specification-list/
    spec.md
    figma-resources/screens/01-specification-list.png
  02-create-specification/
    spec.md
  05-final-integration-spec/
    spec.md
```

## 1 — App level: `user-stories.md`

Whole-module view. Derived from the **flow map** (all journeys across pages).

See [FORMAT-user-stories.md](FORMAT-user-stories.md).

- **User stories** — `As a … I want … so that …` (may be multiple)
- **Journeys** — end-to-end paths as numbered **source → destination** steps (cross-page)
- **Acceptance criteria** — testable outcomes for the module

Do **not** duplicate page layout or per-button behavior here.

## 2 — Module level: `build-order.md`

WaveMaker implementation sequence for the whole module. Write **after** the flow map, **before** or alongside page files.

See [FORMAT-build-order.md](FORMAT-build-order.md).

| Column | Content |
|--------|---------|
| Step | Build order (partials first, then pages) |
| WaveMaker page | PascalCase page/partial name(s) |
| Source images | `images/*.png` paths for this build step |
| Dialogs | Popups built on this page (`—` if none) |
| Notes | Wizard steps, reuse, state variants, navigation hints |

Every page folder and every PNG must appear in the table.

## 3 — Page level: `<NN>-<slug>/spec.md`

**Complete page specification** — what you see and what it does.

See [FORMAT-page-spec.md](FORMAT-page-spec.md).

| Section | Content |
|---------|---------|
| `Source images` | `figma-resources/screens/*.png` in this page folder |
| `Layout` | Static UI — chrome, tables, forms, wizard steps, disabled/enabled states |
| `Dialog: <name>` | Popup layout blocks |
| `Interactions` | In-page behavior — each line: **Source → Destination — action** |
| `Integration` | Cross-page navigation — each line: **Source → Destination — action** |

Include `WaveMaker page: <PascalCaseName>` matching `build-order.md`.

## Writing rules

- Plain sentences; non-technical reader for `user-stories.md` and `spec.md`
- No Figma frame ids
- Real labels from screenshots, not layer names
- Interactions, integration, and journeys always use **Source → Destination — action**
- List every page PNG under `Source images` in `spec.md` (paths from `screens.json`)
- Link `build-order.md` and each page folder from `README.md` when you write one
- `WaveMaker page` names must be consistent across `build-order.md` and `spec.md`

## Done when

- `user-stories.md` covers module journeys and acceptance criteria
- `build-order.md` table covers every page, partial step, PNG, and dialog
- Every page from the flow map has `<NN>-<slug>/spec.md`
- Layout, interactions, and integration in `spec.md` only
- Every page `spec.md` lists all assigned PNGs under `Source images`
- Formats match the FORMAT-*.md examples in this folder

This is the final pipeline step. Hand the written specs to core `/speckit.specify` — see [orchestrator SKILL.md](../SKILL.md#spec-kit-handoff).
