# Figma Images to Spec — a Spec Kit extension

A [GitHub Spec Kit](https://github.com/github/spec-kit) extension that turns a **Figma section's screens** into
Figma-derived specs — per-screen `spec.md` files, app-level `user-stories.md`, and a `build-order.md` — then
hands off to core `/speckit.specify`.

It adds one command:

```
/speckit.figma-images.specify <figma-section-url> [-o <module-name>]
```

Agent-agnostic: the command and pipeline are plain Markdown, so Spec Kit registers them for whichever agent you
picked at `specify init` (Claude, Cursor, Copilot, Gemini, Windsurf, …). Icon/embedded-image export runs through
a bundled **standard-library `python3` script** — no `pip install`, no `uv`, no extra CLI.

> **What makes this different from other Figma extensions:** it is *screen/image-driven*. It pulls the actual
> rendered frames, traces prototype navigation into a flow map, and emits one spec per screen in build order —
> rather than only grounding generation in design tokens/context.

## Requirements

- A Spec Kit project (`specify init` already run). See the [Spec Kit docs](https://github.com/github/spec-kit).
- `python3` >= 3.8 on your PATH (used only for the REST asset pull; standard library only).
- A Figma token: export `FIGMA_TOKEN` (or `FIGMA_ACCESS_TOKEN`), or put `FIGMA_TOKEN=...` in a `.env` file at
  the project root. Without a token the pipeline falls back to the Figma MCP server.

## Install

From your Spec Kit project root, install directly from a release archive:

```bash
specify extension add figma-images \
  --from https://github.com/YOUR-GITHUB-USERNAME/spec-kit-figma-images/archive/refs/tags/v1.0.0.zip
```

Or, for local development against a checkout of this repo:

```bash
specify extension add --dev /path/to/spec-kit-figma-images
```

Verify:

```bash
specify extension list   # should show "Figma Images to Spec (v1.0.0)"
```

> **Note on the community catalog:** the Spec Kit community catalog is *discovery-only*
> (`install_allowed: false`) — being listed there makes the extension searchable, but users still install with
> `--from <url>` above (or by copying the entry into their own `catalog.json`). See
> [`docs/PUBLISHING.md`](docs/PUBLISHING.md).

## Use

```
/speckit.figma-images.specify <figma-section-url> [-o <module-name>]
```

The pipeline runs four steps in order and then stops, handing the result to `/speckit.specify`:

| Step | What it does |
|------|--------------|
| pull-screens | Download section frames as PNGs + prototype taps → `screens.json` |
| trace-flows  | Build a flow map (pages, dialogs, journeys) |
| read-screens | Layout notes per page / dialog / step |
| write-spec   | `user-stories.md`, `build-order.md`, one `spec.md` per screen |

Design **tokens** and **typography** come from the local Figma MCP (`get_variable_defs`, `get_design_context`);
**icons** and **embedded images** come from the bundled REST helper in the background.

## Output

```
figma-specs/<module>/            ← Figma-derived design source (under the project root)
  screens.json
  resources-manifest.json
  user-stories.md
  build-order.md
  design-tokens/tokens.json      ← module-level (shared)
  typography/typography.json     ← module-level (shared)
  01-<slug>/
    spec.md
    figma-resources/
      screens/01-<slug>.png
      icons/*.svg
      embedded/*.png
  ...
```

From there, continue with core Spec Kit: `/speckit.specify` → `/speckit.plan` → `/speckit.tasks` →
`/speckit.implement`.

## Layout of this repo

```
spec-kit-figma-images/
├── extension.yml                 # Spec Kit manifest
├── commands/
│   └── speckit.figma-images.specify.md
├── scripts/
│   └── figma_pull.py             # self-contained stdlib REST helper (screens + resources)
├── figma-images-to-spec/         # the Markdown pipeline (installed alongside the command)
│   ├── SKILL.md  USER.md
│   ├── pull-screens/  trace-flows/  read-screens/  pull-resources/
│   └── write-spec/ (+ FORMAT-*.md)
├── README.md  LICENSE  CHANGELOG.md
├── .env.example  .gitignore  .extensionignore
```

## License

MIT — see [LICENSE](LICENSE).
