---
name: swagger-to-spec
description: >-
  Turn an OpenAPI/Swagger document into an entity model, per-page UI ↔ API
  bindings, and the call sequences behind them. Orchestrates pull-api,
  derive-entities, bind-ui, and write-api-spec. Binds endpoints to the screens
  produced by figma-images-to-spec, in build order. Use when someone shares a
  Swagger link and wants specs.
---

# Swagger → entities & UI bindings

End-to-end API spec workflow. Run the **pipeline** sub-skills in order, then hand off to core `/speckit.specify`.

This pipeline is the data-side companion to [figma-images-to-spec](../figma-images-to-spec/SKILL.md). That pipeline describes *what the user sees*; this one describes *what data sits behind it*.

## Think like the developer wiring the backend to the frontend

That is the whole job. Not "document the API" — work through the screens the way someone building them would, in the order they would build them, and decide for every piece of the UI which call fills it. Everything below is in service of that.

## Imported screens are a prerequisite

There is no screenless fallback. `/speckit.figma-starter.import` runs first and produces the module this pipeline binds against; without it `pull-api` stops and says so. Never invent screens, pages, or components to bind to.

## Build order is the order

Pages are bound in the sequence `<module>/build-order.md` lays out — the order the user journeys run, which is rarely the same as folder numbering. `pull-api` does the sorting, so `figmaPages[]` arrives in the right order and every later step just walks it.

This matters because a page's data usually arrives from the page before it. Binding `Dashboard` after `Login` makes it obvious where the session and the user id come from; binding it first makes that a mystery to solve twice.

## Two scopes

A run covers **every page** or **one page**. `pull-api --page <slug>` narrows it and records `scope: "page"`, with `figmaPages[]` holding just that page.

| Scope | When | What it writes |
|-------|------|----------------|
| `module` | Default | `api-bindings.md` for every page, then `api-catalog.md` |
| `page` | `--page <slug>` given | That one page's `api-bindings.md`, and nothing else |

Page scope exists for the common case of redoing one screen after its spec changed, without disturbing the nine that were already reviewed. Because `figmaPages[]` is pre-filtered, the later steps need no scope logic — they walk the list they are given. The one thing scope changes is what you are allowed to *conclude*: with pages unexamined, nothing may be declared unused. `pagesAvailable[]` names them.

Narrowing the scope does not narrow the reading. `user-stories.md` and `pagesAvailable[]` still describe the whole journey, so a page-scoped run still places its page in the flow — which page precedes it, what that page hands over, where its own actions lead — and binds it as the page at that point, not as an island.

That is also why `api-catalog.md` is a module-scope output only. It is a statement about the whole module — what every page calls, and what nothing calls — and one page is not evidence for it. A page-scoped run leaves the existing file alone and says it is now stale.

## Pipeline (blocking — in order)

| Step | Sub-skill | Output |
|------|-----------|--------|
| 1 | [pull-api](pull-api/SKILL.md) | `api-specs/.api-index.json` — normalized endpoints, entities, resources, and the pages in build order |
| 2 | [derive-entities](derive-entities/SKILL.md) | `api-specs/entities.md` — the entity model the UI must carry |
| 3 | [bind-ui](bind-ui/SKILL.md) | Binding decisions per page, the ordered call sequences where one endpoint's response feeds the next, and which displayed values are computed rather than carried |
| 4 | [write-api-spec](write-api-spec/SKILL.md) | per-page `api-specs/<NN>-<slug>/api-bindings.md`, then module-wide `api-specs/api-catalog.md` |

The pipeline **stops at write-api-spec**. It does not synthesize a Spec Kit `spec.md` or generate tasks — core `/speckit.specify` owns that (see [handoff](#spec-kit-handoff)).

## Output layout

Everything this pipeline writes lands under **`figma-starter/api-specs/`**, a sibling of the module folders. Nothing here writes inside a module folder — the UI outputs are read-only inputs.

`api-specs` is the **default** name. `pull-api --out <folder>` renames it, which is how a project with several modules gives each one an output folder of its own instead of overwriting the last module's `entities.md` and `api-catalog.md`. Never assemble an output path by hand: the root is on the index as `paths.apiSpecs` and each page's file is on `figmaPages[].bindings`, both in full and project-root-relative, so every step below works unchanged under any name. Where these skills write `api-specs/`, read it as the default.

Inside `api-specs/`, the layout **mirrors the module's page folders**, using the same `<NN>-<slug>` names: API-wide files sit at the top, and each page's bindings sit in the folder matching that page.

```
figma-starter/
  <module>/                        ← UI outputs, from figma-images-to-spec — READ ONLY here
    user-stories.md
    build-order.md                 ← the order the pages are bound in
    01-specification-list/
      spec.md
      figma-resources/screens/…
    02-create-specification/
      spec.md
  api-specs/                       ← everything this pipeline writes
    .api-index.json                ← pull-api (normalized source of truth)
    entities.md                    ← derive-entities
    api-catalog.md                 ← the cross-page summary, written last
    01-specification-list/         ← mirrors the page folder of the same name
      api-bindings.md              ← this page's entities + bindings
    02-create-specification/
      api-bindings.md
```

Page folder **names** are the ones `figma-images-to-spec` created — mirror them exactly under `api-specs/`, and never create, rename, or renumber anything under `<module>/`. A page gets an `api-bindings.md` only if it already has a `spec.md`. `pull-api` creates the mirror folders for the pages in scope, so they exist before you write.

Every path in `.api-index.json` is **relative to the project root**, so you never have to work out which root a path hangs off: `figmaPages[].spec` and `.screens` point back into `<module>/` to read, `figmaPages[].bindings` points into `api-specs/` to write.

## Reading the module

`.api-index.json` is the only thing later steps need to read for API facts. Its shape:

| Key | Content |
|-----|---------|
| `module` | The module folder this run bound against, as resolved from `-m` or from the one module present |
| `scope` | `module` or `page` — whether `figmaPages[]` is the whole module or a subset |
| `paths` | `{uiRoot, apiSpecs, userStories, buildOrder}` — where to read the UI outputs and where to write |
| `info`, `servers` | Title, version, base URLs |
| `resources[]` | `{name, slug, endpointIds[], entities[]}` — endpoints grouped by first real path segment |
| `endpoints[]` | `{id, method, path, resource, operationId, summary, tags, parameters[], requestBody, responses[], primaryEntity, entityInferred, collection}` |
| `entities[]` | `{name, description, fields[{name, type, entity, array, required, enum, description}], usedBy[]}` |
| `figmaPages[]` | `{slug, title, wavemakerPage, buildStep, spec, screens[], bindings}` — the pages **in scope**, in build order, each with the UI files to read and the `api-specs/` file to write |
| `pagesAvailable[]` | Every page slug in the module, in scope or not, in build order |
| `source` | `{location, specVersion, fetchedAt}` — where the document came from and which flavor it was |
| `stats` | `{endpoints, entities, resources, figmaPages}` — the counts to quote in the completion report |

`primaryEntity` is already unwrapped through pagination envelopes (`Page<T>` → `T`), and `collection` is true when the endpoint yields many of them.

When a generator emits an untyped envelope (`Page` with `content: Object[]`), the element type is missing from the document itself. `pull-api` then falls back to the entity the endpoint's resource is named after and sets **`entityInferred: true`**. Treat those as strong hypotheses, not documented facts: they are usually right, but say so where it matters rather than presenting them as if the document stated them.

## spec-kit handoff

The API specs are an **input** to core Spec Kit — this pipeline does not create a feature itself.

1. **Whole module:** `/speckit.specify` pointing at `figma-starter/<module>/` **and** `figma-starter/api-specs/` — `user-stories.md`, `build-order.md`, every `<NN>-<slug>/spec.md`, plus `api-specs/entities.md`, `api-specs/api-catalog.md`, and each `api-specs/<NN>-<slug>/api-bindings.md`.
2. **Single screen:** `/speckit.specify` pointing at the pair for that screen — `figma-starter/<module>/<NN>-<slug>/spec.md` and `figma-starter/api-specs/<NN>-<slug>/api-bindings.md`.

From there the normal chain follows: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`.

## Principles

- **The document is the source of truth** — every endpoint, field, and type comes from `.api-index.json`. Never invent an endpoint, a field, or a parameter that is not in the document.
- **Bind in build order** — walk the pages the way the journeys run, so each page can say which of its ids the page before it supplied.
- **Say so when nothing matches** — unbound UI and unused endpoints are findings, not failures. Record them; do not paper over them by inventing a match.
- **Bind at element level** — bind `Specification List / search field`, not "the list page".
- **One call, however many places it shows** — the same response often fills several parts of a screen. Bind it once and say which elements share it; never bind the same endpoint twice for one page load.
- **A list is one call, then a field map** — a repeating row or card comes from a collection endpoint, not one call per row. State the call, then map each field of an element to the part of the card it fills.
- **Separate what is carried from what is computed** — a screen says more than an API stores. `Payments completed 120/120` is two fields; `Account Health: Excellent` is a rule over those fields plus a threshold nobody wrote down. Record the rule with pseudocode, its minimal inputs, and the calls behind them — see [bind-ui step 4](bind-ui/SKILL.md#4--decide-what-is-carried-and-what-is-computed).
- **Computed values belong in the BFF** — every derivation is work for the backend-for-frontend layer, not the component. Say so, and never propose a BFF route as if the document declared it.
- **Compute only what varies per record** — a derivation is worth writing down when it moves as the record moves. A fixed label is not a derivation.
- **Chart the order where one call is not enough** — when the id a call needs is itself the result of an earlier call, a row cannot say that. Those chains get a flowchart and a step-by-step with what each call needs and yields — see [bind-ui step 5](bind-ui/SKILL.md#5--chart-the-call-sequences).
- **Show each endpoint once, in full** — every endpoint a page uses gets one worked example: the request with its headers and body, and a sample response. Written once per page, at first use.
- **Take the shorter chain** — use the server-side filters, enums, nested data, and envelope counters that are already there; collapse a per-row fan-out into one collection call; run independent legs in parallel. Say what you rejected.
- **Page-wise storage** — a page's bindings live in `api-specs/<NN>-<slug>/`, the mirror of that page's folder.
- **Summarise last, from the files** — `api-catalog.md` rolls up the `api-bindings.md` files after they are written, and says only what they say.
- **Write only under `api-specs/`** — the module folder is an input; read its specs and screenshots, change nothing in it.
- **Mirror the Figma page folders** — same `<NN>-<slug>` names, never renamed or renumbered.
- **Stop at write-api-spec** — hand off to `/speckit.specify`; do not synthesize Spec Kit specs or tasks here.

See [USER.md](USER.md) for the end-user blurb.
