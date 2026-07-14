---
name: figma-images-to-spec
description: >-
  Turn a Figma design section into app-level user stories plus per-page specs.
  Orchestrates pull-screens, trace-flows, read-screens, and write-spec.
  Optionally runs pull-resources in the background. Ends with a handoff to core
  /speckit.specify. Use when someone shares a Figma section link and wants specs.
---

# Figma → user stories & page specs

End-to-end spec workflow. Run the **pipeline** sub-skills in order, then hand off to core `/speckit.specify`. **Resources are optional and run in the background** — never block the spec on them.

## Pipeline (blocking — in order)

| Step | Sub-skill | Output |
|------|-----------|--------|
| 1 | [pull-screens](pull-screens/SKILL.md) | `screens.json`, per-page screen PNGs under `figma-starter/<module>/<NN>-<slug>/figma-resources/screens/` |
| 2 | [trace-flows](trace-flows/SKILL.md) | Flow map (pages, dialogs, journeys) |
| 3 | [read-screens](read-screens/SKILL.md) | Layout notes per page / dialog / step |
| 4 | [write-spec](write-spec/SKILL.md) | `user-stories.md`, `build-order.md`, `<NN>-<slug>/spec.md` per screen |

The pipeline **stops at write-spec**. It does not synthesize a Spec Kit `spec.md` or generate tasks — core `/speckit.specify` owns that (see [handoff](#spec-kit-handoff)).

## Background (parallel — do not wait)

| Task | Sub-skill | Output |
|------|-----------|--------|
| Pull resources | [pull-resources](pull-resources/SKILL.md) | module `design-tokens/`, `typography/`, per-page `figma-resources/icons` + `embedded` |

After **pull-screens** resolves the module name (`<module>`), run **pull-resources** in two parts. Continue the pipeline immediately.

**Part 1 — tokens and typography via local Figma MCP** (inline, do not block):

- `get_variable_defs` → `design-tokens/tokens.json`
- `get_design_context` → `typography/typography.json`

Always use the Figma MCP for these; the REST CLI is not used for tokens/typography.

**Part 2 — icons + images via bundled REST helper** (background):

```bash
python3 .specify/extensions/figma-starter/scripts/figma_pull.py resources "<url>" -o <module> --assets-only &   # icons + embedded only
```

## Output layout

`figma-starter/` is created under the project root (where `.specify/` lives). Everything for a module lives under `figma-starter/<module>/`. Tokens and typography are **module-level** (shared across screens); each screen owns a nested **`figma-resources/`** with the screens, icons, and embedded images needed to build it.

```
figma-starter/
  <module>/
    screens.json
    resources-manifest.json
    user-stories.md
    build-order.md
    design-tokens/tokens.json       ← module-level (shared)
    typography/typography.json       ← module-level (shared)
    01-list-page/
      spec.md
      figma-resources/
        screens/01-list-page.png
        icons/*.svg
        embedded/*.png
    02-create-page/
      spec.md
      figma-resources/…
    05-final-integration-spec/
      spec.md                        ← cross-page integration spec
```

Page folders use **`{order}-{slug}/`** directly under the module (no `pages/` subfolder). Order matches `screens.json` (`01`, `02`, …).

## spec-kit handoff

The Figma-derived specs are the **input** to core Spec Kit — this pipeline does not create a feature itself.

1. **Whole module:** `/speckit.specify` pointing at `figma-starter/<module>/` (`user-stories.md` + `build-order.md` + every `<NN>-<slug>/spec.md`).
2. **Single screen:** `/speckit.specify` pointing at one `figma-starter/<module>/<NN>-<slug>/spec.md` (follow `build-order.md`).

From there the normal chain follows: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`.

## Principles

- **API `taps` first** — prototype actions define navigation; screenshots describe layout.
- **Per-screen resources** — each screen's icons/images/screens live in its own `figma-resources/`; tokens and typography stay module-level.
- **Numbered page folders** — `01-list-page/spec.md`, not `pages/list-page/spec.md`.
- **Do not skip pipeline steps** — especially trace-flows before writing.
- **Stop at write-spec** — hand off to `/speckit.specify`; do not synthesize Spec Kit specs or tasks here.

See [USER.md](USER.md) for the end-user blurb.
