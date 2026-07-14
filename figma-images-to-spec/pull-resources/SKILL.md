---
name: figma-pull-resources
description: >-
  Optional background task for figma-images-to-spec. Extract module-level color
  tokens and typography via the local Figma MCP, plus per-screen icons and
  embedded images via the bundled figma_pull.py REST helper, into
  figma-specs/<module>/. Tokens and typography always come from the Figma
  MCP; icons and images always come from the REST helper.
  Independent of the spec pipeline — run in parallel after pull-screens.
disable-model-invocation: true
---

# Pull resources (background)

Extract design assets into `figma-specs/<module>/`. There are two fixed sources:

- **Design tokens and typography** — always via the **local Figma MCP** (`get_variable_defs`, `get_design_context`). Module-level (shared across screens).
- **Icons and embedded images** — always via the **bundled REST helper** (`figma_pull.py resources --assets-only`). Per screen, in each page's `figma-resources/`.

**Independent of the spec pipeline** — do not block trace-flows or write-spec.

## When to run

- Right after [pull-screens](../pull-screens/SKILL.md) knows `<module>`
- In parallel while steps 2–4 run
- On its own anytime someone only wants assets exported

## Two-part execution

### Part 1 — tokens and typography (local Figma MCP)

Always use the **local Figma MCP** for these — the REST API is unreliable for variables and text styles:

1. **Color tokens** — call `get_variable_defs` with the Figma URL.
   Write the result to `figma-specs/<module>/design-tokens/tokens.json`.

2. **Typography** — call `get_design_context` with the Figma URL.
   Extract all text styles (fontFamily, fontWeight, fontSize, lineHeightPx, letterSpacing).
   Write to `figma-specs/<module>/typography/typography.json` as a JSON array.

Tokens and typography are module-level — the Figma MCP returns document-level data, so it is not scoped per screen.

If the local Figma MCP is not connected, connect it first (it exposes `get_variable_defs` and `get_design_context`). Do **not** substitute the REST CLI for tokens/typography — that path is unreliable and is reserved for icons and images.

### Part 2 — icons and images (bundled REST helper, background)

```bash
[ -f .env ] && set -a && . ./.env && set +a
python3 .specify/extensions/figma-specs/scripts/figma_pull.py resources "<figma section url>" -o <module> --assets-only &
```

`--assets-only` pulls **only** icons and embedded images — tokens and typography come from the MCP in Part 1, so the helper never touches them. Use the same `-o module-name` as pull-screens. **Do not wait** for this process.

## Output

```
figma-specs/<module>/
  resources-manifest.json                 ← index of tokens, typography, per-page assets
  design-tokens/tokens.json               ← module-level; local Figma MCP (get_variable_defs)
  typography/typography.json              ← module-level; local Figma MCP (get_design_context)
  01-…/figma-resources/icons/*.svg        ← per screen; figma_pull.py resources
  01-…/figma-resources/embedded/*.png     ← per screen; embedded rasters
```

| Path | Contents | Source |
|------|----------|--------|
| `design-tokens/tokens.json` | Color variables and fills (module-level) | Local Figma MCP `get_variable_defs` |
| `typography/typography.json` | Text styles (module-level) | Local Figma MCP `get_design_context` |
| `<NN>-<slug>/figma-resources/icons/` | SVG icons for that screen | `figma_pull.py resources --assets-only` |
| `<NN>-<slug>/figma-resources/embedded/` | Embedded rasters for that screen | `figma_pull.py resources --assets-only` |

## Done when

- `design-tokens/tokens.json` exists (from the Figma MCP `get_variable_defs`)
- `typography/typography.json` exists (from the Figma MCP `get_design_context`)
- Per-screen icons and embedded images saved when present in the design

No "next step" — this task is standalone. The spec pipeline continues at [trace-flows](../trace-flows/SKILL.md) without waiting.
