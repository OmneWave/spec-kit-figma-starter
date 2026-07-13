# Figma → specs

Paste your Figma **section** link in Cursor and ask:

> Write the user stories and page specs.

## One-time setup

1. Install the extension into your Spec Kit project (see the extension README).
2. Set a Figma token — either export `FIGMA_TOKEN=...` or add it to a `.env` file at the project root. (Without a token the pipeline falls back to the Figma MCP server.)
3. Open the project in your coding agent. `figma-specs/` is created under the project root the first time the pipeline runs.

## You get

Everything under `figma-specs/<module>/`. Tokens and typography are shared module-level; each screen owns a nested `figma-resources/` with its screens, icons, and embedded images.

```
figma-specs/
  <module>/
    screens.json
    resources-manifest.json
    user-stories.md
    build-order.md
    design-tokens/tokens.json
    typography/typography.json
    01-list-page/
      spec.md
      figma-resources/
        screens/01-list-page.png
        icons/*.svg
        embedded/*.png
    02-create-page/
      spec.md
      figma-resources/…
    …
```

## spec-kit handoff

This pipeline stops at the Figma-derived specs. Hand them to core `/speckit.specify`, which creates the feature and its `spec.md`.

**Whole module:**

```
/speckit.specify using figma-specs/<module>/ (user-stories.md + build-order.md + each screen spec.md)
```

**Single screen (in build-order sequence):**

```
/speckit.specify using figma-specs/<module>/01-list-page/spec.md
```

Then continue the normal chain: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`.

## Sub-skills

| Step | Skill |
|------|-------|
| 1 | pull-screens |
| 2 | trace-flows |
| 3 | read-screens |
| 4 | write-spec |
| background | pull-resources |

All under `.specify/extensions/figma-images/figma-images-to-spec/` (installed with the Figma Images to Spec extension).
