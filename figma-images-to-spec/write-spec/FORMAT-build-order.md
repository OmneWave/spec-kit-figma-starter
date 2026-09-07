# Build order (`build-order.md`)

Module-level **implementation sequence**. Write this after the flow map is complete and before or alongside page files. Derive from `screens.json`, the flow map, and page grouping — not from Figma frame order alone.

Place at `specs/<folder>/build-order.md`. Link from `README.md`.

## Table

| Step | Page name | Source images | Dialogs | Notes |
|------|----------------|---------------|---------|-------|
| 1 | `MainHeader`, `MainLeftnav` | `images/10-…6824.png` | — | Shared partials; extract once, reuse on all pages |
| 2 | `ContractSpecificationList` | `images/10-…6824.png`, `images/11-…4218.png`, `images/12-…7416.png` | Row options, Delete message | Contract tab selected; table, search, pagination, success toast state |
| 3 | `CreateContractSpecification` | `images/01-…6782.png` … `images/05-…7298.png` | Discard message | 3-step wizard: General details → Additional details → Review |
| 4 | `EditContractSpecification` | `images/06-edit-….png` | Discard message | Reuse create wizard structure; prefilled data |
| 5 | `ViewContractSpecification` | `images/09-…8929.png` (or review step PNG) | — | Read-only review; Back and Edit actions |

## Column rules

| Column | Content |
|--------|---------|
| **Step** | Build order (1, 2, 3…). Partials/scaffold before pages that reference them. |
| **Page name** | PascalCase page or partial name the implementation step will create (e.g. `CreateContractSpecification`). Multiple partials on one step: comma-separated in one cell. |
| **Source images** | `images/NN-….png` paths from this module. List every PNG that informs this page (wizard steps = multiple images on one row). |
| **Dialogs** | Dialog names built on this page (`Row options`, `Delete message`, …). Use `—` when none. Popups are never separate pages. |
| **Notes** | Implementation hints: wizard vs single page, reuse partials, state variants (disabled Next, success toast), navigation targets, shared structure with another page. |

## Ordering rules

1. **Shared partials first** — header, leftnav, footer before any page that references them.
2. **Entry/list page early** — usually the main hub before create/edit/view flows.
3. **Create before edit/clone** — edit and clone often reuse create layout.
4. **Dialogs on the parent page row** — list dialogs under the page where they open, not as separate steps (unless a dialog is large enough to warrant its own partial; note in Notes).
5. **Every PNG** appears in exactly one row's Source images column (or Notes if it's a state variant of an already-listed image).
6. **Every `<NN>-<slug>/` page folder** has a matching row (except when multiple partials share step 1).

## Markdown template

```markdown
# Build order

Implementation sequence for [Module Name].

[Figma section](<url from screens.json>)

| Step | Page name | Source images | Dialogs | Notes |
|------|----------------|---------------|---------|-------|
| 1 | `MainHeader`, `MainLeftnav` | `images/01-….png` | — | Shared chrome |
| 2 | `ExampleList` | `images/10-….png` | Advanced Filters | Entry page |
```
