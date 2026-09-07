# Swagger → entities & UI bindings

Paste your **Swagger / OpenAPI** link (or file path) in your agent and ask:

> Generate the API spec and bind it to the screens.

Run `/speckit.figma-starter.import` **first**. This pipeline binds endpoints to screens, so the screens have to exist — without them it stops and tells you to import.

## One-time setup

1. Install the extension into your Spec Kit project (see the extension README).
2. Have the API document reachable — a URL (`/v3/api-docs`, `/v2/api-docs`, `swagger.json`, `openapi.json`) or a local JSON/YAML file.
3. If the document is behind auth, export `SWAGGER_TOKEN=...` (or add it to `.env`), or pass `--header "Authorization: Bearer …"`.

JSON needs nothing extra. YAML documents need `pip install pyyaml`.

## You get

Everything under `figma-starter/api-specs/`, alongside the module folder your screens live in. The API model is kept apart from the design output but laid out the same way, page folder for page folder, so you can read a screen and its data contract side by side.

```
figma-starter/
  <module>/                   your screens, from the Figma pipeline — untouched
    01-list-page/spec.md
    02-create-page/spec.md
  api-specs/                  everything this pipeline writes
    .api-index.json           every endpoint + entity, normalized
    entities.md               the entity model the UI must carry
    api-catalog.md            every endpoint and which screens call it
    01-list-page/
      api-bindings.md         this page's entities, UI → endpoint table, call sequences
    02-create-page/
      api-bindings.md
```

### Several modules? One output folder each

`api-specs/` is the default. If your `figma-starter/` holds more than one module, give each run its own output folder with `--out`, because `entities.md` and `api-catalog.md` sit at the top of it and describe the module that was run:

```
/speckit.figma-starter.import-api <doc> -m storefront --out api-specs-storefront
/speckit.figma-starter.import-api <doc> -m checkout   --out api-specs-checkout
```

Without it the second run overwrites the first module's catalog. The extra output folders sit beside your modules without being mistaken for one, so `-m` keeps working as before.

Each `api-bindings.md` answers one question per page: **which endpoint backs which piece of this screen** — plus what is left over on both sides (UI with no endpoint, endpoints with no UI).

Pages are worked through in the order `build-order.md` lays out — the order the journeys run, not the order the folders are numbered. That is what lets a page say where its ids came from: usually the page before it.

A list is **one call, then a map**. A table of ten rows is one collection call, followed by a table saying which field of one element fills which part of one row or card — never ten calls. Same rule when one response fills a table *and* a set of summary cards above it: bound once, with a note saying what else it feeds.

Where one call is not enough, you also get **the order they run in**. A schedule table keyed by a loan id the screen never receives takes three calls, each one supplying the id for the next — and a row in a table cannot say that. Those chains get their own `Call sequences` section: a flowchart of the calls with the value that moves along each arrow, the branches the document declares (`404` → empty state, `409` → duplicate message), and a step table showing what each call needs and yields. Where a chain needs a call the API does not have, the chart stops at a `MISSING` node instead of quietly inventing one.

Every endpoint a page uses gets **one worked example** — the request, its headers, the body, and a sample response — under `Endpoint examples`, written once however many parts of the screen call it.

It also separates **what the API carries from what your screen works out**. A card reading `Payments completed 120/120` is two fields printed together. `Account Health: Excellent` on the same card is not stored anywhere — it is a rule over those fields plus a threshold that only the design knows. Those get their own `Derived values` section per page, with the smallest set of attributes the rule needs, the calls behind each one, the logic as pseudocode, what has to change for the value to move, and how sure the rule is — `certain`, `fairly certain`, or `uncertain`. **All of it is work for your BFF layer**, said as such. Where a card cannot be filled from the API at all, it says so instead of inventing a field.

`api-catalog.md` is the view from above, written once every page is bound: each endpoint with the screens that call it, the endpoints nothing calls, the UI nothing serves, every chain that has to be orchestrated, and every value that has to be computed with the calls it needs. Start there to see how much of the API the design actually uses.

## spec-kit handoff

This pipeline stops at the API-derived specs. Hand them to core `/speckit.specify`.

**Whole module (design + data):**

```
/speckit.specify using figma-starter/<module>/ and figma-starter/api-specs/ (user-stories.md, build-order.md, each spec.md + its api-bindings.md, plus entities.md and api-catalog.md)
```

**Single screen:**

```
/speckit.specify using figma-starter/<module>/01-list-page/spec.md and figma-starter/api-specs/01-list-page/api-bindings.md
```

Then continue the normal chain: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`.

## Sub-skills

| Step | Skill |
|------|-------|
| 1 | pull-api |
| 2 | derive-entities |
| 3 | bind-ui |
| 4 | write-api-spec |

All under `.specify/extensions/figma-starter/swagger-to-spec/` (installed with the Figma Starter extension).
