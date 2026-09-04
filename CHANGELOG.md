# Changelog

All notable changes to this extension are documented here. Versions follow
[Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-08-12

### Added
- `/speckit.figma-starter.import-api <swagger-url-or-file> [-m <module>] [--out <folder>] [--page <slug>]`
  — turns an OpenAPI 3.x or Swagger 2.0 document into an entity model plus
  per-page UI ↔ API bindings, then hands off to core `/speckit.specify`.
- `swagger-to-spec` Markdown pipeline: `pull-api` → `derive-entities` →
  `bind-ui` → `write-api-spec`, with `FORMAT-*.md` templates for each output.
- Bundled, standard-library-only `scripts/swagger_pull.py`, which fetches the
  document and flattens both OpenAPI 3.x and Swagger 2.0 into one
  `api-specs/.api-index.json`: `$ref`s resolved, `allOf` chains merged, pagination
  envelopes (`Page<T>`) unwrapped to the element type, and endpoints grouped
  into resources by tag or path. YAML documents need `pyyaml`; JSON needs nothing.
- **Output under `figma-starter/api-specs/`**, a sibling of the module folder
  that mirrors its page folders name for name:
  `api-specs/<NN>-<slug>/api-bindings.md` alongside `.api-index.json` and
  `entities.md` at the top. The module folder is a read-only input — the command
  reads each page's `spec.md`, its screenshots, and `user-stories.md`, and writes
  nothing into it, so a re-run cannot disturb a reviewed screen spec. Every path
  in `.api-index.json` is project-root-relative, `figmaPages[]` carrying `spec`,
  `screens[]`, and `bindings` per page.
- **`--out <folder>` gives a run its own output folder** under `figma-starter/`,
  defaulting to `api-specs`. A project whose `figma-starter/` holds several
  modules needs one per module: `entities.md` and `api-catalog.md` sit at the top
  of the output root and describe the module that was run, so a second module
  written to the same folder overwrites them — and the page folders, whose slugs
  differ, would pile up rather than collide, leaving one folder of everyone's
  pages under a catalog describing only the last run. The flag takes a single
  folder name, so every recorded path stays project-root-relative and one level
  deep, and it refuses to name a design module, which is a read-only input. Later
  steps need no flag of their own: they read `paths.apiSpecs` and
  `figmaPages[].bindings` off the index rather than assembling a path. An output
  folder is never counted as a module either — the default by name, and any
  `--out` folder by the `.api-index.json` inside it — so `-m` stays optional on a
  one-module project however many output folders sit beside it.
- **Element-level bindings.** One `api-bindings.md` per page, binding endpoints
  at *element* level with the trigger, each parameter's UI source, and what the
  response populates. Imported screens are a prerequisite: with no module folder,
  or no page folder holding a `spec.md`, the run stops and points at
  `/speckit.figma-starter.import` rather than inventing screens to bind against.
- **Pages are bound in build order** — the sequence `<module>/build-order.md`
  lays out, which is the order the user journeys run rather than the order the
  folders are numbered. `swagger_pull.py` does the sorting, joining each page's
  `WaveMaker page:` line to the build-order table, so `figmaPages[]` arrives
  ordered and every later step just walks it. Binding a page after the one that
  hands it its ids is what lets it say where they came from. A module written by
  an older import warns and falls back to folder order.
- **Lists are one call plus a field map.** A repeating row or card is stated as a
  single collection call, followed by a `Field | Card part | Value source` table
  mapping one element of the array onto one row or card — never one call per row.
  A list nested inside a card is recursed into when an API fills it and flattened
  when it does not. And one endpoint is bound once per page load however many
  parts of the screen it feeds, with the sharing named in `Notes`, so nothing
  reads as two round trips.
- **Endpoint examples.** Each page carries a `## Endpoint examples` section with
  one worked example per *distinct* endpoint it uses, in first-use order: the
  request against a real base URL, the headers that matter, the required request
  body, a trimmed response, and the interesting failure. Written once at first
  use, so the payloads live in exactly one place per page.
- **Write flows are cross-checked against the user stories.** Every save, delete,
  submit and publish a story describes has to end up bound to an endpoint or
  listed as unbound — the easiest kind of binding to miss, since a button that
  posts looks like any other button on a screenshot.
- **`api-specs/api-catalog.md`**, the module-wide summary, written last from the
  per-page bindings: every endpoint with the screens that call it, the endpoints
  nothing calls, the UI nothing serves, the values that have to be computed, and
  which screens touch each entity. It
  carries no parameters or payloads — those stay in `.api-index.json` and the
  page files, so the summary has nothing to drift from. Written on module-scoped
  runs only; a `--page` run leaves it untouched rather than rebuilding a
  module-wide claim from one screen.
- **Two scopes.** `--page <slug>` rebinds a single screen without touching the
  others, accepting `01-specification-list`, `specification-list`, or `1`.
  A page-scoped run may not declare any endpoint unused, since the other pages
  were never examined. Narrowing the scope does not narrow the reading, though:
  `user-stories.md` and the build-ordered `pagesAvailable[]` still place the page
  in the journey, so it is bound as the page at that point rather than as an
  island.
- **Derived values.** Each page's `api-bindings.md` now says, per element,
  whether a field carries what the screen shows (`direct`), whether the screen
  states something the document does not (`derived`), or whether the value is the
  same for every record (`static`). Formatting a field is not deriving a value:
  `Payments completed 120/120` is two fields printed together, while
  `Account Health: Excellent` on the same card is a rule over those fields plus a
  threshold that exists only in the design. Every `derived` value gets its own
  entry in a page-level `## Derived values` section with the **minimal** attribute
  set it reads, the call behind each attribute, which change to the record moves
  it, a one-phrase `Source` for where the rule came from, a confidence of
  `certain` / `fairly certain` / `uncertain`, and the logic as **pseudocode**.
  Only values that vary per record qualify — a label, a legend, or a count the
  pagination envelope already carries does not.
- **Derived values are BFF work**, and the spec says so — a derivation belongs in
  the backend-for-frontend layer, not the component. It does not go so far as to
  name a `GET /bff/…` route: an endpoint the document never declared is exactly
  what the rest of the pipeline exists to prevent.
- Derived values that the document cannot support are recorded as
  `not derivable` with what they would need, never as an invented field, and
  inferred thresholds are marked `uncertain` so a product owner knows which bands
  to confirm. `api-catalog.md` rolls them up module-wide — the value, the screens
  showing it, and the calls behind it — with the pseudocode left in the page files.
- **Call sequences.** A binding row says which endpoint serves an element; it
  cannot say in what order, and on a generated API one call is often not enough —
  the id a call needs is itself the result of an earlier call, a displayed name
  has to be looked up from an id, a write runs create-then-attach-then-submit.
  Each page now carries a `## Call sequences` section for those chains: the one
  part of the output that is deliberately **not** a table, since an order, a
  branch, a parallel leg and a per-row fan-out do not fit in a row. Every chain
  gets a Mermaid flowchart with the value that moves labelled on each arrow and
  the branches the document declares (`404` → empty state, `409` → duplicate
  message), and a step table of what each call **needs** and **yields**. The
  payloads are not repeated here — each step points at that endpoint's entry
  under `## Endpoint examples`, so a chain shows only the value carrying from one
  call to the next. New `write-api-spec/FORMAT-call-sequences.md` pins the shape
  down; `bind-ui` gained a step that derives the chains.
- **Chains are checkable.** Every step must name an endpoint that exists in
  `.api-index.json`, and every `Needs` must resolve to the route, a user input,
  or an earlier step's output. An unresolved one is reported as a finding — the
  screen cannot be built as designed — and a chain the document cannot complete
  stops at a `MISSING` node with what it would need, rather than being finished
  with an invented endpoint.
- **Shorter chains, from what the document already says.** `bind-ui` now mines the
  document before adding a call: server-side `q`/`sort`/`page`/filter parameters
  instead of fetching and discarding client-side, enum fields as dropdown options
  needing no call at all, nested entities already on a response instead of a
  second fetch, and `totalElements` instead of paging through to count. Per-row
  fan-outs are collapsed into one collection call and a client-side join where
  the document allows it; legs with no data dependency are marked `parallel`
  rather than implied to be ordered. The rejected option is named.
- **`api-catalog.md` lists the chains** module-wide — sequence, page, and the
  chain as `A → B → C`. Flowcharts, step tables and worked examples stay in the
  page files.
- Unbound UI and unused endpoints are recorded as findings rather than resolved
  by guessing — on a generated back-office API these are usually the most
  useful output of a run.
- `SWAGGER_TOKEN` / `API_TOKEN` environment support, plus repeatable
  `--header "Name: value"` for documents behind auth.
- Endpoints whose payload the document types only as `Object` are attributed to
  the resource's entity and flagged `entityInferred`, so an inference is never
  presented as something the document stated.

### Changed
- `README.md` documents both commands, the screens prerequisite, the two scopes,
  and the two sibling output trees (`<module>/` and `api-specs/`).

### Fixed
- `-m <module>` naming a folder that does not exist now **stops** and suggests the
  near miss (`Did you mean -m storefront?`). Previously a typo silently created
  a decoy module, found no page folders in it, and reported a clean run having
  produced no bindings.
- `figma-starter/api-specs/` is created only once the run is certain to produce
  an index, so a rejected `--page` or an unreadable document no longer leaves an
  empty folder behind.
- A run whose project still holds output from the earlier in-module layout — a
  `<module>/api/` folder, or `api-bindings.md` beside a page's `spec.md` — warns
  and names those files, so stale copies are not mistaken for this run's output.

## [1.0.0] - 2026-07-13

### Added
- Initial release as a standalone Spec Kit extension (`id: figma-starter`).
- `/speckit.figma-starter.import <figma-url> [-o <module>]` command that runs the
  figma-images-to-spec pipeline (pull-screens → trace-flows → read-screens →
  write-spec) and hands off to core `/speckit.specify`.
- `before_specify` hook offering to generate Figma-derived specs.
- Bundled, standard-library-only `scripts/figma_pull.py` for REST screen and
  asset (icon/embedded-image) export — no `pip install`, `uv`, or external CLI.
