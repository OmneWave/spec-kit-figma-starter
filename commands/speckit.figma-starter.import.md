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

Bridge design → spec. This command runs the **figma-images-to-spec** pipeline — shipped with this extension at `.specify/extensions/figma-starter/figma-images-to-spec/` — to turn a Figma section into Figma-derived specs, then hands off to core `/speckit.specify`. The pipeline is plain Markdown, so it works with any Spec Kit agent (Cursor, Claude, Copilot, Gemini, Windsurf, …).

This command **stops at the Figma-derived specs**. It does not synthesize a Spec Kit `spec.md` itself and does not generate implementation tasks — that is core Spec Kit's job. Once the pipeline finishes, you hand the written specs to `/speckit.specify`, which owns feature registration and the downstream `/speckit.plan` → `/speckit.tasks` → `/speckit.implement` chain.

## Prerequisites

1. The **figma-images-to-spec** pipeline is present at `.specify/extensions/figma-starter/figma-images-to-spec/` (installed with this extension via `specify extension add`).
2. A Figma token is available: `FIGMA_TOKEN` (or `FIGMA_ACCESS_TOKEN`) in the environment, or a `.env` file with `FIGMA_TOKEN=...` at the project root. Without a token the pipeline falls back to the Figma MCP server (`get_screenshot`, `get_metadata`, `get_variable_defs`, `get_design_context`).
3. `python3` (>=3.8) is available on the PATH — the bundled REST helper is standard-library only (no pip install).

`figma-starter/` is created automatically by the pipeline; you do not need to scaffold it.

A project **constitution** is *not* required to run this command — this can be the first Spec Kit command you run after installing the extension. If no constitution exists yet, the command offers to set one up before handing off to `/speckit.specify` (see [Handoff](#handoff)).

## Steps

### Step 1: Resolve the input

- Treat `$ARGUMENTS` as the Figma section URL. Extract any `-o <folder>` override for the module name.
- If no URL is present, stop and ask for one — do not invent a link.

### Step 2: Run the figma-images-to-spec pipeline (blocking, in order)

Read `.specify/extensions/figma-starter/figma-images-to-spec/SKILL.md`, then run its pipeline steps **in order** with the resolved URL. Each step's instructions live at `.specify/extensions/figma-starter/figma-images-to-spec/<step>/SKILL.md` — read and follow each before producing its output. Do not skip steps — trace-flows must run before any spec is written.

| Step | Sub-skill (`<step>/SKILL.md`) | Output |
|------|-----------|--------|
| 1 | `pull-screens` | `screens.json` + per-page screen PNGs under `figma-starter/<module>/<NN>-<slug>/figma-resources/screens/` |
| 2 | `trace-flows` | Flow map (pages, dialogs, journeys) |
| 3 | `read-screens` | Layout notes per page / dialog / step |
| 4 | `write-spec` | `user-stories.md`, `build-order.md`, `<NN>-<slug>/spec.md` |

After `pull-screens` resolves the module name, run `pull-resources` — **do not block** the spec on it. Design **tokens and typography** come from the local Figma MCP (`get_variable_defs`, `get_design_context`); **icons and embedded images** come from the bundled REST helper (`python3 .specify/extensions/figma-starter/scripts/figma_pull.py resources ... --assets-only`) in the background.

### Step 3: Verify the output

Confirm the following exist under `figma-starter/<module>/`:

- `user-stories.md` and `build-order.md`
- One `<NN>-<slug>/` folder per screen, each with a `spec.md`

If any screen from the flow map is missing its `spec.md`, re-run `write-spec` before handing off.

## Completion Report

Report to the user:

- `MODULE` — the resolved module name
- The design source root: `figma-starter/<module>/`
- The ordered list of screen folders (from `build-order.md`)
- That the Figma-derived specs are ready to hand to `/speckit.specify`

## Handoff

The Figma-derived specs are the input to core Spec Kit. **Before** handing off to `/speckit.specify`, make sure a project constitution is in place:

- A Spec Kit **constitution** (`.specify/memory/constitution.md`) captures the project's governing principles and is normally established with `/speckit.constitution` before `/speckit.specify`. Because this command can be run first — right after installing the extension — the constitution may not exist yet.
- Check for it. If `.specify/memory/constitution.md` is **missing or empty**, ask the user:
  > No project constitution was found. Would you like to set one up with `/speckit.constitution` before running `/speckit.specify`?

  Then **stop and wait** for their answer. Do **not** run `/speckit.constitution` yourself — the user runs it if they say yes.
- If a constitution already exists, or the user declines, continue to `/speckit.specify`.

Then continue with **`/speckit.specify`**, which creates the feature and its `spec.md`:

1. **Whole module:** run `/speckit.specify` and point it at `figma-starter/<module>/` — read `user-stories.md`, `build-order.md`, and every `<NN>-<slug>/spec.md`, then synthesize them into a single feature spec.
2. **Single screen:** run `/speckit.specify` and point it at one `figma-starter/<module>/<NN>-<slug>/spec.md`, following the sequence in `build-order.md`.

From there the normal chain follows: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`.

## Done When

- [ ] The figma-images-to-spec pipeline ran (steps 1–4, none skipped)
- [ ] `user-stories.md`, `build-order.md`, and one `<NN>-<slug>/spec.md` per screen exist under `figma-starter/<module>/`
- [ ] Completion reported with module name and the design source root
- [ ] Checked for a project constitution (`.specify/memory/constitution.md`) and, if missing, offered to set one up with `/speckit.constitution`
- [ ] Handed off to `/speckit.specify`
