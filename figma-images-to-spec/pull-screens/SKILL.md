---
name: figma-pull-screens
description: >-
  Step 1 of figma-images-to-spec. Download Figma section frames as PNGs and
  build screens.json with prototype taps from API metadata. Use when pulling
  Figma screens or starting a Figma-to-spec workflow.
disable-model-invocation: true
---

# Pull screens

Download frames and prototype metadata from a Figma section.

## Run

```bash
# Optional: load a token from .env if you use one (else export FIGMA_TOKEN).
[ -f .env ] && set -a && . ./.env && set +a

python3 .specify/extensions/figma-images/scripts/figma_pull.py screens "<figma section url>"
```

Optional: `-o module-name` to override the output folder under `figma-specs/`.

## Output

```
figma-specs/
  <module>/
    screens.json
    01-…/figma-resources/screens/01-….png
    02-…/figma-resources/screens/02-….png
    …
```

Each frame's PNG lands in its own page folder's `figma-resources/screens/`.

## Where clicks come from

`figma_pull.py screens` calls `GET /v1/files/:key/nodes?ids=…` and walks each frame's layer tree.

| API field | Meaning |
|-----------|---------|
| `interactions[]` | Prototype triggers on that layer |
| `interactions[].actions[]` (or `.action`) | What happens on trigger |
| `action.type === "NODE"` | Navigate to another frame |
| `action.destinationId` | Target frame id |
| `action.navigation === "OVERLAY"` | Popup on current screen |
| `action.navigation === "NAVIGATE"` | Full-screen navigation |

Flattened into `screens.json` → `taps` per screen:

```json
{ "control": "<layer name>", "opens": "<destination title>", "type": "screen" | "popup" }
```

## Fallback (no token)

1. Figma MCP `get_screenshot` per frame → save as `figma-specs/<module>/01-…/figma-resources/screens/01-….png`, …
2. For `taps`, still need REST API node payload with `interactions` / `actions` — MCP `get_metadata` is structure-only (no prototype actions).
3. Write `screens.json` in the same shape as the CLI. **Do not stop** — continue to trace-flows.

## Done when

- Every frame in the section has a PNG and a `screens` entry
- Each screen has a `taps` array (empty array if none)

**Then:** kick off [pull-resources](../pull-resources/SKILL.md) (same URL/`-o`). Tokens and typography come from the local Figma MCP (`get_variable_defs`, `get_design_context`); icons and embedded images come from the bundled REST helper (`figma_pull.py resources ... --assets-only`) in the background.

Immediately continue to [trace-flows](../trace-flows/SKILL.md) — do not wait for resources.
