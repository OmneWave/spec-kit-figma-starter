---
description: Turn a Figma section link into Figma-derived specs (user stories, build order, per-page specs) by running the figma-images-to-spec pipeline, then hand off to /speckit.specify.
tools:
  - 'figma/get_screenshot'
  - 'figma/get_metadata'
  - 'figma/get_variable_defs'
  - 'figma/get_design_context'
---

## User Input

```text
$ARGUMENTS
```

The user input **is** the Figma section link (and optionally an `-o <folder>` module-name override). You **MUST** use it. If it is empty, ask the user to paste a Figma section URL and stop.

## Purpose

Bridge design → spec. This command runs the **figma-images-to-spec** pipeline — shipped with this extension at `.specify/extensions/figma-specs/figma-images-to-spec/` — to turn a Figma section into Figma-derived specs, then hands off to core `/speckit.specify`. The pipeline is plain Markdown, so it works with any Spec Kit agent (Cursor, Claude, Copilot, Gemini, Windsurf, …).

This command **stops at the Figma-derived specs**. It does not synthesize a Spec Kit `spec.md` itself and does not generate implementation tasks — that is core Spec Kit's job. Once the pipeline finishes, you hand the written specs to `/speckit.specify`, which owns feature registration and the downstream `/speckit.plan` → `/speckit.tasks` → `/speckit.implement` chain.

## Prerequisites

1. The **figma-images-to-spec** pipeline is present at `.specify/extensions/figma-specs/figma-images-to-spec/` (installed with this extension via `specify extension add`).
2. A Figma token is available: `FIGMA_TOKEN` (or `FIGMA_ACCESS_TOKEN`) in the environment, or a `.env` file with `FIGMA_TOKEN=...` at the project root. Without a token the pipeline falls back to the Figma MCP server (`get_screenshot`, `get_metadata`, `get_variable_defs`, `get_design_context`).
3. `python3` (>=3.8) is available on the PATH — the bundled REST helper is standard-library only (no pip install).

`figma-specs/` is created automatically by the pipeline; you do not need to scaffold it.

## Steps

### Step 1: Resolve the input

- Treat `$ARGUMENTS` as the Figma section URL. Extract any `-o <folder>` override for the module name.
- If no URL is present, stop and ask for one — do not invent a link.

### Step 2: Run the figma-images-to-spec pipeline (blocking, in order)

Read `.specify/extensions/figma-specs/figma-images-to-spec/SKILL.md`, then run its pipeline steps **in order** with the resolved URL. Each step's instructions live at `.specify/extensions/figma-specs/figma-images-to-spec/<step>/SKILL.md` — read and follow each before producing its output. Do not skip steps — trace-flows must run before any spec is written.

| Step | Sub-skill (`<step>/SKILL.md`) | Output |
|------|-----------|--------|
| 1 | `pull-screens` | `screens.json` + per-page screen PNGs under `figma-specs/<module>/<NN>-<slug>/figma-resources/screens/` |
| 2 | `trace-flows` | Flow map (pages, dialogs, journeys) |
| 3 | `read-screens` | Layout notes per page / dialog / step |
| 4 | `write-spec` | `user-stories.md`, `build-order.md`, `<NN>-<slug>/spec.md` |

After `pull-screens` resolves the module name, run `pull-resources` — **do not block** the spec on it. Design **tokens and typography** come from the local Figma MCP (`get_variable_defs`, `get_design_context`); **icons and embedded images** come from the bundled REST helper (`python3 .specify/extensions/figma-specs/scripts/figma_pull.py resources ... --assets-only`) in the background.

### Step 3: Verify the output

Confirm the following exist under `figma-specs/<module>/`:

- `user-stories.md` and `build-order.md`
- One `<NN>-<slug>/` folder per screen, each with a `spec.md`

If any screen from the flow map is missing its `spec.md`, re-run `write-spec` before handing off.

## Completion Report

Report to the user:

- `MODULE` — the resolved module name
- The design source root: `figma-specs/<module>/`
- The ordered list of screen folders (from `build-order.md`)
- That the Figma-derived specs are ready to hand to `/speckit.specify`

## Handoff

The Figma-derived specs are the input to core Spec Kit. Continue with **`/speckit.specify`**, which creates the feature and its `spec.md`:

1. **Whole module:** run `/speckit.specify` and point it at `figma-specs/<module>/` — read `user-stories.md`, `build-order.md`, and every `<NN>-<slug>/spec.md`, then synthesize them into a single feature spec.
2. **Single screen:** run `/speckit.specify` and point it at one `figma-specs/<module>/<NN>-<slug>/spec.md`, following the sequence in `build-order.md`.

From there the normal chain follows: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`.

## Done When

- [ ] The figma-images-to-spec pipeline ran (steps 1–4, none skipped)
- [ ] `user-stories.md`, `build-order.md`, and one `<NN>-<slug>/spec.md` per screen exist under `figma-specs/<module>/`
- [ ] Completion reported with module name and the design source root
- [ ] Handed off to `/speckit.specify`
