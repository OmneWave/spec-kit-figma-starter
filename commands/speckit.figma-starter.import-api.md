---
description: Turn an OpenAPI/Swagger document into an entity model and per-page UI-to-API bindings by running the swagger-to-spec pipeline, then hand off to /speckit.specify.
---

## User Input

```text
$ARGUMENTS
```

The user input **is** the OpenAPI/Swagger source — a URL or a local JSON/YAML path — plus optionally:

| Flag | Purpose |
|------|---------|
| `-m <folder>` | Module folder to read the UI outputs from |
| `--out <folder>` | Folder under `figma-starter/` to write this run's output to (default: `api-specs`) |
| `--header "Name: value"` | Auth or other request header; repeatable |
| `--page <slug>` | Bind only this page; repeatable. Omit to bind every page |

You **MUST** use it. If it is empty, ask the user for a Swagger/OpenAPI URL or file path and stop.

## Purpose

Bridge API → spec. This command runs the **swagger-to-spec** pipeline — shipped with this extension at `.specify/extensions/figma-starter/swagger-to-spec/` — to turn an API document into an entity model plus per-page UI ↔ API bindings, then hands off to core `/speckit.specify`. The pipeline is plain Markdown, so it works with any Spec Kit agent (Cursor, Claude, Copilot, Gemini, Windsurf, …).

It is the data-side companion to `/speckit.figma-starter.import`. That command describes *what the user sees*; this one describes *what data sits behind it*.

**Work like the developer wiring the backend to the frontend.** Not "document the API against the UI" — wire it. Walk the screens in the order they would be built, and for every piece of each one decide which call fills it, where its parameters come from, and what has to happen before it can run.

Everything it writes goes to **`figma-starter/api-specs/`** — a sibling of the module folder, laid out the same way, one folder per page. The module folder is a **read-only input**: this command reads the page specs and screenshots the import produced and never writes into them.

`api-specs` is the default output folder; `--out <folder>` renames it. **A project with several modules needs one output folder per module** — `entities.md` and `api-catalog.md` sit at the top of the output root and describe the module that was run, so a second module written to the same folder overwrites them.

Pages are bound in **build order** — the sequence `<module>/build-order.md` lays out, which is the order the user journeys run and rarely the order the folders are numbered. That matters because a page's ids usually arrive from the page before it: binding `Dashboard` after `Login` makes the session obvious, binding it first makes it a mystery.

Binding an endpoint is only half the answer. A screen states more than an API stores, so each page also records **which of its values a field actually carries and which have to be computed**: `Payments completed 120/120` is two fields printed together, while `Account Health: Excellent` is a rule over those same fields plus a threshold that exists only in the design. Those get the rule as pseudocode, the smallest set of attributes it needs, the calls behind them, what has to change for the value to move, and how sure the rule is — or an honest "not derivable" where the document cannot support them at all. **Every derivation is BFF work**, said as such, and never as an invented `/bff/…` route.

A binding row also cannot say **in what order**. On a generated API one call is often not enough: the id a call needs is itself the result of an earlier call, a displayed name has to be looked up from an id, a write has to run create-then-attach-then-submit. So each page carries a `## Call sequences` section for the chains where one call will not do — the only part of the output that is not a table, because an order, a branch, a parallel leg, and a per-row fan-out do not fit in a row. Each chain gets a Mermaid flowchart with the value that moves along every arrow and a step table saying what each call needs and where that comes from. Chains are charted the way they should be built — server-side filters over client-side work, one collection call instead of N per-row calls, independent legs in parallel — and a chain the document cannot complete stops at a `MISSING` node rather than being finished with an invented endpoint.

Payloads live in one place per page: a `## Endpoint examples` section with one worked example per **distinct** endpoint the page uses — the request, the headers that matter, the body, and a trimmed response.

This command **stops at the API-derived specs**. It does not synthesize a Spec Kit `spec.md` itself and does not generate implementation tasks — that is core Spec Kit's job.

## Prerequisites

1. **`/speckit.figma-starter.import` has already run** for this module. This pipeline binds endpoints to screens, so screens are required — there is no screenless fallback. Without a module folder holding `<NN>-<slug>/spec.md` pages, `pull-api` stops and says so.
2. The **swagger-to-spec** pipeline is present at `.specify/extensions/figma-starter/swagger-to-spec/` (installed with this extension via `specify extension add`).
3. The API document is reachable — a URL (`/v3/api-docs`, `/v2/api-docs`, `swagger.json`, `openapi.json`) or a local file. If it is behind auth, `SWAGGER_TOKEN` (or `API_TOKEN`) is set in the environment or in a `.env` file at the project root, or the user passes `--header "Authorization: Bearer …"`.
4. `python3` (>=3.8) is available on the PATH — the bundled helper is standard-library only (no pip install). YAML documents additionally need `pyyaml`; JSON documents need nothing.

## Scope: whole module or one page

By default a run rebinds every page. Pass `--page <slug>` to work on **one page only** — the usual reason being that a single screen's `spec.md` changed and you do not want to disturb pages already reviewed. It is repeatable, and accepts a folder name (`01-specification-list`), the bare slug (`specification-list`), or the number (`1`).

`pull-api` narrows `figmaPages[]` to the pages in scope and sets `scope: "page"`, so the later steps need no scope logic. What scope does change:

- Only the pages in scope get an `api-bindings.md` written under `api-specs/`. **No other page's file is touched**, and no API-wide file is rewritten — including `api-catalog.md`, which is a claim about the whole module and cannot be rebuilt from one page. Say in the report that it is now stale for the page you rebound.
- **Nothing may be declared unused.** You have not looked at the other pages; an endpoint unused here may be another page's whole purpose. Report it as unused *by this page*.

Narrowing the scope does **not** narrow the reading. `user-stories.md` and the build-ordered `pagesAvailable[]` still describe the whole journey, so still place the page in the flow — which page precedes it, what that page hands over, where its own actions lead — and bind it as the page at that point, not as an island.

If `--page` matches no page folder, the script stops and lists the pages that exist. Pick one of those — do not fall back to binding everything.

## Steps

### Step 1: Resolve the input

- Treat `$ARGUMENTS` as the Swagger/OpenAPI source. Extract any `-m <folder>` override, `--out <folder>`, `--header`, and `--page` flags, and pass them straight through to `pull-api`.
- If no source is present, stop and ask for one — do not invent a URL.
- The module names where the **input** comes from; `--out` names where the output goes. If `figma-starter/` already holds exactly one module, that module is the target and `-m` is unnecessary (output folders are this command's own and never count as modules, whatever `--out` called them). If it holds **several** and no `-m` was given, ask the user which module this API belongs to before running — the script refuses rather than guess. When you do bind one module of several, pass `--out` as well, or this run overwrites the last one's module-wide files; suggest `--out api-specs-<module>` and say so in the report.
- Read the output root back from `paths.apiSpecs` on `.api-index.json`, and each page's file from `figmaPages[].bindings`. Never assemble an `api-specs/…` path by hand — under `--out` it would be the wrong folder.
- If `figma-starter/` holds **no module**, or the module holds no page folder with a `spec.md`, the script stops. Relay its message: `/speckit.figma-starter.import` has to run first. Do **not** hand-write page folders to get past it.
- If the script warns there is **no `build-order.md`**, pages fall back to folder order. Say so in the report — folder order is a numbering, not a journey.
- If the script warns that **output from the previous layout** is still present — a `<module>/api/` folder, or `api-bindings.md` files sitting beside the page specs — those are from before this command moved its output to `api-specs/`. Nothing reads them now. Report them to the user as stale copies to delete, and do not treat them as input.
- If `--page` was given, resolve the module **before** running, since a page slug means nothing without it.

### Step 2: Run the swagger-to-spec pipeline (blocking, in order)

Read `.specify/extensions/figma-starter/swagger-to-spec/SKILL.md`, then run its pipeline steps **in order** with the resolved source. Each step's instructions live at `.specify/extensions/figma-starter/swagger-to-spec/<step>/SKILL.md` — read and follow each before producing its output.

| Step | Sub-skill (`<step>/SKILL.md`) | Output |
|------|-----------|--------|
| 1 | `pull-api` | `figma-starter/api-specs/.api-index.json` — endpoints, entities, resources, and the pages in build order |
| 2 | `derive-entities` | `figma-starter/api-specs/entities.md` |
| 3 | `bind-ui` | Per-page binding decisions, call sequences, derived values, and endpoint examples |
| 4 | `write-api-spec` | per-page `api-specs/<NN>-<slug>/api-bindings.md`, then module-wide `api-specs/api-catalog.md` |

Do not skip steps — `bind-ui` must run before any binding is written. It reads the page `spec.md`, **the page screenshots**, and `user-stories.md` alongside the API document; the screenshots are where column headers, field labels, and filter options come from, so do not skip them.

Walk `figmaPages[]` in the order it is given. It is already in build order — do not re-sort it.

Those inputs all live in the module folder, and the output goes to its mirror under the output root — written `api-specs/` in the table above, which is the default name; under `--out` it is the folder that flag named. Do not assemble either path by hand: `.api-index.json` records each in full, relative to the project root — `figmaPages[].spec`, `.screens[]`, and `.bindings` per page, and `paths.userStories` and `paths.buildOrder` for the module.

### Step 3: Verify the output

Confirm the following under `figma-starter/api-specs/`:

- `.api-index.json` and `entities.md` exist
- Nothing was written under `figma-starter/<module>/` — it is an input, and the run must leave it as the import left it
- Every page in `figmaPages[]` has an `api-bindings.md`, in an `api-specs/` folder named exactly as that page's folder under the module
- Each `api-bindings.md` has one section per UI section named in its `spec.md` `Layout` block, in the same order, with one table in each — read the two files side by side and confirm the sections line up
- **No endpoint is bound twice for one page load.** Where a response fills a table and a set of cards, there is one row and a `Notes` clause naming the other elements, not two rows
- **Every list, table, and repeating card** has one call and a `Field | Card part | Value source` map beneath it, with every part of the card accounted for
- **Every action a user story calls for** — each save, delete, submit, publish — has a row with the endpoint behind it, or is listed as unbound. Read `user-stories.md` back and check them off; a write flow the stories describe and the bindings omit is the easiest thing to miss
- Every element that shows a value carries a `Value source`, and each `derived` one has a matching `###` in that page's `## Derived values` giving its minimal inputs with the calls behind them, what moves it, its `Source`, one of `certain` / `fairly certain` / `uncertain`, and pseudocode. A value that cannot be computed from the document says `not derivable` rather than naming a field that does not exist — check each input against `.api-index.json`. No `###` names a BFF route
- Every page has a `## Call sequences` section — a `###` per multi-call chain with a flowchart and a step table, or one line saying every element is served by a single call. Check two things per chain: every step names an endpoint that exists in `.api-index.json` (or is a `MISSING` node), and every `Needs` resolves to the route, a user input, the previous page, or an earlier step's `Yields`. An unresolved `Needs` is a real finding — the screen cannot be built as designed
- Any section row whose element needs a chain links to it as `sequence: [<name>](#call-sequences)`, and no row restates the order in prose
- Every distinct endpoint the page uses appears exactly once under `## Endpoint examples`, and no payload is repeated inside a call sequence
- **Module scope:** `api-catalog.md` exists, was written after the page files, accounts for every endpoint in `.api-index.json` exactly once, its `Bound by` names page files that really contain those bindings, and its `## Call sequences` roll-up has a row for every `###` in every page file — the chain only, no flowcharts or payloads
- **`scope: page`:** only that page's `api-bindings.md` was written or changed, `api-catalog.md` is untouched, and no endpoint was newly marked `unused`

If a page from `figmaPages[]` is missing its `api-bindings.md`, re-run `write-api-spec` before handing off — and rebuild `api-catalog.md` afterwards, since it summarises a set of files that just changed.

## Completion Report

Report to the user:

- `MODULE` — the resolved module name
- `SCOPE` — `module`, or `page` naming the page(s) bound and how many were left alone
- `ORDER` — the pages in the order they were bound, and whether that came from `build-order.md` or fell back to folder order
- Counts — endpoints, entities, resources, and pages bound
- The API spec root this run wrote — `paths.apiSpecs`, which is `figma-starter/api-specs/` unless `--out` renamed it — and the module it was bound against
- Any stale output from the previous layout the script warned about, named as files to delete
- **Unbound UI** and **unused endpoints** — the gaps found, as findings the team should look at
- **Call sequences** — how many screen elements need more than one call, and any chain the document cannot complete
- **Derived values** — how many values the screens state that no field carries, which of them are not computable from this API at all, and which are `uncertain`. All of them are BFF work — say so once
- That the API-derived specs are ready to hand to `/speckit.specify`

Surface the gaps plainly. An element with no endpoint, an endpoint nothing calls, and a card the API cannot fill are exactly the kind of thing this command exists to find. All three are already tallied in `api-catalog.md`, so point the user at it as the one place the whole picture is: coverage counts, every endpoint with who calls it, the chains, and the leftover lists.

Call out every `uncertain` derived value. Those are the rows a product owner has to confirm — the arithmetic can be checked against the document, but a cut-off between `Good` and `Excellent` cannot, because it is not in the document to check. In a page-scoped run there is no whole picture — say which pages were **not** examined, and that `api-catalog.md` was deliberately left as the last module-scoped run wrote it, so nothing here reads as a module-wide conclusion.

## Handoff

The API-derived specs are an input to core Spec Kit, alongside the Figma-derived ones. Continue with **`/speckit.specify`**:

Below, `<api-specs>` is this run's output folder — `paths.apiSpecs` on the index, `figma-starter/api-specs/` unless `--out` renamed it. Name the real folder when you tell the user, so a multi-module project gets the right one.

1. **Whole module:** run `/speckit.specify` pointing at `figma-starter/<module>/` **and** `<api-specs>/` — `user-stories.md`, `build-order.md`, every `<NN>-<slug>/spec.md`, plus `<api-specs>/entities.md`, `<api-specs>/api-catalog.md`, and each `<api-specs>/<NN>-<slug>/api-bindings.md`.
2. **Single screen:** run `/speckit.specify` pointing at the matching pair — `figma-starter/<module>/<NN>-<slug>/spec.md` and `<api-specs>/<NN>-<slug>/api-bindings.md` — following the sequence in `build-order.md`.

If `.specify/memory/constitution.md` is **missing or empty**, ask the user:

> No project constitution was found. Would you like to set one up with `/speckit.constitution` before running `/speckit.specify`?

Then **stop and wait** for their answer. Do **not** run `/speckit.constitution` yourself — the user runs it if they say yes.

From there the normal chain follows: `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`.

## Done When

- [ ] The swagger-to-spec pipeline ran in order, against a module the Figma import had already produced
- [ ] `.api-index.json` and `entities.md` exist under the output folder (`paths.apiSpecs` — `figma-starter/api-specs/` unless `--out` renamed it)
- [ ] Everything written sits under that one folder; `figma-starter/<module>/` was read but not modified, and no other module's output folder was touched
- [ ] Every page in `figmaPages[]` has an `api-bindings.md` mirroring it at its `figmaPages[].bindings` path, bound in build order
- [ ] Every value-showing element is classified `direct`, `derived`, or `static`, and every `derived` value has its pseudocode, its minimal inputs, the calls it needs, its `Source` and one of the three confidence values — stated as BFF work, with no invented BFF route
- [ ] Every list is one call plus a field map, and no endpoint is bound twice for one page load
- [ ] Every write flow the user stories describe is bound or listed as unbound
- [ ] Every page has a `## Call sequences` section, every multi-call element has a chain with a flowchart and a step table, and every `Needs` in every chain resolves
- [ ] Every distinct endpoint used by a page has exactly one worked example under `## Endpoint examples`
- [ ] Fan-outs are collapsed where a collection endpoint allows it, and independent legs are marked parallel
- [ ] Module scope: `api-catalog.md` was written last and accounts for every endpoint; page scope: it was left untouched and reported as stale
- [ ] No invented endpoints, fields, pages, or BFF routes — everything traces to the API document, including every attribute a derivation reads and every step in every chain
- [ ] Completion reported with module, scope, build order, counts, and the unbound/unused/derived findings
- [ ] Checked for a project constitution and, if missing, offered to set one up with `/speckit.constitution`
- [ ] Handed off to `/speckit.specify`
