---
name: figma-trace-flows
description: >-
  Step 2 of figma-images-to-spec. Walk screens.json taps to map pages, dialogs,
  and journeys from Figma prototype actions. Use after pull-screens or when
  analyzing Figma click flows before writing a spec.
disable-model-invocation: true
---

# Trace prototype flows

Walk the **click graph** from `screens.json` → `taps`. Source is API metadata — do not guess navigation from images.

## Steps

1. **Entry screen** — usually `screens[0]`, or the obvious home/list frame.
2. **Follow every tap** on each screen:
   - `type: "screen"` → another **Page**; record under source page **Integration** in `spec.md` later.
   - `type: "popup"` → **Dialog** on the current page (`spec.md`), not a separate page.
   - `type: "back"` / `type: "close"` → **Return path** (`opens` is `null` — destination is dynamic). `back` returns to the previous frame; `close` dismisses the current overlay to its parent. Record as an **Interaction** return edge.
3. **Return paths** — the `back`/`close` taps above, plus any close/dismiss/back visible or implied (overlay → parent).
4. **Journeys** — ordered **source → destination** paths, e.g. `List → Dialog: Advanced Filters`; `List → Create Specification / General details`.

## Flow map (write before spec)

Record every edge as **Source → Destination** (page, dialog, or step):

```text
Specification List (entry)
  Specification List → Dialog: Advanced Filters [popup]
  Specification List → Dialog: Row options [popup]
  Specification List → Create Specification / General details [screen]
  Create Specification / General details → Create Specification / Additional details [step]
  Dialog: Discard message / Yes, discard → Specification List [screen]
```

## Derive pages

| In the flow | Output files |
|-------------|--------------|
| Full-screen frame | `<NN>-<slug>/spec.md` |
| Overlay / menu / filter dialog | `Dialog:` block in parent page `spec.md` |
| Multi-step wizard | One page folder; `Step1:`, `Step2:` in `spec.md` |
| Same screen, multiple entry paths | One page folder |
| Empty state / disabled Next variant | Same page; state in `spec.md` Layout, rules in `spec.md` Interactions |

Screens with no incoming taps may still be layout states — keep on the same **Page**.

**Do not** group by Figma frame order alone. **Do** let `taps` define structure first.

## Done when

- Every tap is assigned to a page, dialog, or integration edge
- Mental flow map covers all branches

Next: [read-screens](../read-screens/SKILL.md)
