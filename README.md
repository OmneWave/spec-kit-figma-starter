# Figma Starter — a Spec Kit extension

A [GitHub Spec Kit](https://github.com/github/spec-kit) extension that turns a **Figma section's screens** into
Figma-derived specs — per-screen `spec.md` files, app-level `user-stories.md`, and a `build-order.md` — then
hands off to core `/speckit.specify`.

## Quick start

```bash
specify init .                              # initialize in the current folder
specify init folder_name --integration [choose your agent]   # or create a new folder
specify extension add figma-starter \
  --from https://github.com/wavemaker/spec-kit-figma-starter/archive/refs/tags/v1.0.0.zip
```

It adds one command:

```
/speckit.figma-starter.import <figma-section-url> [-o <module-name>]
```

Agent-agnostic: the command and pipeline are plain Markdown, so Spec Kit registers them for whichever agent you
picked at `specify init` (Claude, Cursor, Copilot, Gemini, Windsurf, …). Icon/embedded-image export runs through
a bundled **standard-library `python3` script** — no `pip install`, no `uv`, no extra CLI.

> **What makes this different from other Figma extensions:** it is *screen/image-driven*. It pulls the actual
> rendered frames, traces prototype navigation into a flow map, and emits one spec per screen in build order —
> rather than only grounding generation in design tokens/context.

## Where it fits

This extension adds **one step** to the Spec Kit workflow. It sits **between `/speckit.constitution` and
`/speckit.specify`** — turning your Figma screens into the Figma-derived specs that `/speckit.specify` then
consumes:

```text
specify init                    create a Spec Kit project
        │
/speckit.constitution           establish project principles
        │
/speckit.figma-starter.import     👈 THIS EXTENSION — Figma section → per-screen specs
        │
/speckit.specify                synthesize the Figma-derived specs into a feature spec
        │
/speckit.plan  →  /speckit.tasks  →  /speckit.implement
```

**You don't have to run `/speckit.constitution` first.** The import command works standalone, so you can install
the extension and run it right away. If no constitution exists yet (`.specify/memory/constitution.md`), the
command asks whether you'd like to set one up with `/speckit.constitution` **before** it hands off to
`/speckit.specify` — so you end up with a constitution either way:

```text
/speckit.figma-starter.import     run right after install — Figma section → per-screen specs
        │
   (no constitution yet?)  →    "Set one up with /speckit.constitution first?"  →  /speckit.constitution
        │
/speckit.specify  →  /speckit.plan  →  /speckit.tasks  →  /speckit.implement
```

## Getting started

### Step 1 — Install Spec Kit and initialize a project

If you don't already have a Spec Kit project, install the CLI and run `specify init`. Pick your agent with
`--integration` (e.g. `claude`, `cursor`, `copilot`, `gemini`, `windsurf`). Check the
[Spec Kit repo](https://github.com/github/spec-kit) for the latest release tag.

```bash
# install the Spec Kit CLI (replace the tag with the latest release)
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v0.12.14

# create a project, then cd into it
specify init my-app --integration claude
cd my-app
```

### Step 2 — Add this extension

From your Spec Kit project root, install directly from a release archive:

```bash
specify extension add figma-starter \
  --from https://github.com/wavemaker/spec-kit-figma-starter/archive/refs/tags/v1.0.0.zip
```

Or, for local development against a checkout of this repo:

```bash
specify extension add --dev /path/to/figma-starter
```

Verify it registered:

```bash
specify extension list   # should show "Figma Starter (v1.0.0)"
```

> **Note on the community catalog:** the Spec Kit community catalog is *discovery-only*
> (`install_allowed: false`) — being listed there makes the extension searchable, but users still install with
> `--from <url>` above (or by copying the entry into their own `catalog.json`).

### Step 3 — Set your Figma token

Export a token, or put it in a `.env` file at the project root. Without one the pipeline falls back to the
Figma MCP server.

```bash
export FIGMA_TOKEN=figd_...           # or FIGMA_ACCESS_TOKEN
# or: echo 'FIGMA_TOKEN=figd_...' >> .env
```

You also need `python3` >= 3.8 on your PATH — used only for the REST asset pull (standard library only, no
`pip install`).

### Step 4 — Run the workflow

The recommended order establishes your project principles first, generates the Figma-derived specs with this
extension, then hands off to core Spec Kit:

```text
/speckit.constitution                                       # 1. project principles
/speckit.figma-starter.import <figma-section-url> [-o <name>]  # 2. Figma → specs (this extension)
/speckit.specify                                            # 3. point it at figma-starter/<module>/
/speckit.plan                                               # 4. technical plan
/speckit.tasks                                              # 5. task list
/speckit.implement                                          # 6. build it
```

Prefer to start with the import? You can run it first — it works standalone:

```text
/speckit.figma-starter.import <figma-section-url> [-o <name>]  # run right after install
# → if no constitution exists, the command asks whether to set one up with
#   /speckit.constitution before you continue to /speckit.specify
/speckit.specify  →  /speckit.plan  →  /speckit.tasks  →  /speckit.implement
```

The import command runs four steps in order and then stops, handing the result to `/speckit.specify`:

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
figma-starter/<module>/            ← Figma-derived design source (under the project root)
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
figma-starter/
├── extension.yml                 # Spec Kit manifest
├── commands/
│   └── speckit.figma-starter.import.md
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
