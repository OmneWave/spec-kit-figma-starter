---
name: swagger-write-api-spec
description: >-
  Step 4 (final) of swagger-to-spec. Write per-page api-bindings.md, then the
  module-wide api-catalog.md, under figma-starter/api-specs/. Use when writing
  the API documentation from .api-index.json and the binding decisions, before
  handing off to /speckit.specify.
disable-model-invocation: true
---

# Write API specification

Write documentation from `.api-index.json` + the binding decisions. Everything goes under **`figma-starter/api-specs/`** — never inside the module folder, which is an input here. **Three layers:**

| Layer | File | Content |
|-------|------|---------|
| API-wide | `api-specs/entities.md` | The entity model (written in [derive-entities](../derive-entities/SKILL.md)) |
| Page | `api-specs/<NN>-<slug>/api-bindings.md` | This page's entities, its bindings section by section, the chains where one call is not enough, the values it has to compute, and one worked example per endpoint it uses |
| Module | `api-specs/api-catalog.md` | Every endpoint with the pages that call it, plus what nothing calls, what nothing serves, what has to be orchestrated, and what has to be computed — **written last** |

The page folders under `api-specs/` **mirror the module's page folders** — same `<NN>-<slug>` names, so `api-specs/01-specification-list/api-bindings.md` is obviously the counterpart of `<module>/01-specification-list/spec.md`. `figmaPages[].bindings` gives you the exact path; `pull-api` has already created the folder.

Write the pages in the order `figmaPages[]` gives them, which is build order — the same order `bind-ui` walked them in. A page written after the one that hands it its ids can say so; one written first cannot.

**The catalog is a coverage view, not a restatement of the document.** `.api-index.json` already holds every endpoint with its parameters, entity, and `summary`, so copying those into Markdown would only create a second version to keep in step. What the index cannot say is *which page calls this*, and that is the whole point of writing the catalog after the page files: it is a roll-up of bindings that now exist. Keep it to endpoint, entity, and who binds it — the moment a parameter list appears in it, it has become the copy this pipeline is avoiding.

Do **not** write `tasks.md` or a Spec Kit `spec.md` here — that is core `/speckit.specify`'s job after this pipeline finishes.

## Output tree

Each page's bindings sit in the `api-specs/` folder mirroring that page:

```
figma-starter/
  <module>/                      ← input, unchanged by this step
    01-specification-list/spec.md
    02-create-specification/spec.md
  api-specs/
    .api-index.json
    entities.md
    api-catalog.md               ← written last, once every page below exists
    01-specification-list/
      api-bindings.md
    02-create-specification/
      api-bindings.md
```

Never write inside `figma-starter/<module>/`, and never invent a page folder name — the `api-specs/` page folders mirror the module's, and `pull-api` created them. Write `api-bindings.md` only for pages listed in `figmaPages[]`, at the `bindings` path each entry carries. When `scope` is `page` that list holds one page, so one file is written and the rest are left untouched — `pagesAvailable[]` names the pages you are deliberately not writing.

## 1 — Page level: `api-specs/<NN>-<slug>/api-bindings.md`

**Complete data contract for one page** — what it shows, what it calls, which of its values the API actually carries, what has to be computed, and what does not line up. Written as **one `##` section per UI section on the page, with one table in each**.

See [FORMAT-page-bindings.md](FORMAT-page-bindings.md).

The body is **not** organised by concern. It follows the page's own sections — `Header`, `Cards Section`, `Filters`, `Table`, `Dialog: Row options` — using the same names and order as that page's `spec.md` `Layout` block, so the two files can be read side by side.

| Section | Columns |
|---------|---------|
| `## Entities` | Entity, Fields used, Surfaces as |
| `## <UI section>` | Element, Trigger, Endpoint, Sends, Populates, Value source, Notes |
| `## Dialog: <name>` | Same columns; one table per dialog |
| `## Call sequences` | Not a table — one `###` per chain: flowchart and step table |
| `## Derived values` | Not a table — one `###` per value: bullets and pseudocode |
| `## Endpoint examples` | Not a table — one `###` per distinct endpoint the page uses |
| `## Integration` | Source, Destination, Data passed, Destination loads |
| `## Unused endpoints` | Endpoint, Note |

**One table per section, and that table is self-contained.** Everything a reader needs about that region of the screen is in it — no jumping to a separate parameters, responses, or unbound section. So each section's table carries:

- What the section **loads on arrival** *and* how it **behaves when used** — the `Trigger` column separates them. Do not split those into `Layout` and `Interactions` sections; a search field belongs with the rest of the `Filters` region.
- **Parameters**, in `Sends`, each with `← <source>` naming the UI input, entity field, or previous page that supplies it.
- **Responses**, in `Populates`.
- **Whether a field carries the value**, in `Value source` — `direct`, `derived → [<name>](#derived-values)`, `static`, or `—`.
- **Unbound elements**, as rows with `—` in `Endpoint` and an `Unbound: <what it would need>` note.

There is no page-level `## Parameters`, `## Responses`, or `## Unbound UI` section. The four page-level sections after the UI ones are page-level because they are not about one region — a chain, a formula, and an endpoint's payload each span sections, and one of them is often shared by two elements, so the section row names it and the page-level section states it once.

### Lists get a field map

A repeating row or card is **one call, then a field map** — never one call per row. Write the call as a single row in the section's table, then follow it with a `Field | Card part | Value source` table describing one element of the array onto one row or card. A derived field in that map points at `## Derived values` like any other. See [FORMAT-page-bindings.md](FORMAT-page-bindings.md#lists-tables-and-repeating-cards).

### One call, however many places it shows

The same response often fills a table, a set of summary cards, and a dialog. Bind it once, at first use, and say in `Notes` which other elements share it. Two rows naming the same endpoint for one page load read as two round trips, and someone will build them that way.

`## Call sequences` is where `bind-ui`'s step 5 lands, and it is **not a table**. A row can hold one element, one endpoint, one trigger; it cannot hold an order, a branch, a parallel leg, or a per-row fan-out. So each chain gets a `###` with a Mermaid flowchart, a step table saying what each call needs and yields, and a `**Payload shapes:**` line pointing at `## Endpoint examples`. **No payloads in the sequence itself** — they live once, under the endpoint. See [FORMAT-call-sequences.md](FORMAT-call-sequences.md).

Write a sequence for every element whose data takes more than one call — an id that only an earlier response supplies, a name that has to be looked up from an id, an ordered write, an aggregate needing every page, a fan-out per row, or a section no single endpoint serves. A single call whose parameters the screen already has is not a sequence. The section row points at the chain in `Notes` as `sequence: [<name>](#call-sequences)` and does not restate it. A page where every element is served by one call keeps the heading and one line saying so.

`## Derived values` is where `bind-ui`'s step 4 lands: one `###` per value the screen states that no field holds, with where it shows, its minimal inputs and the call behind each, what change moves it, where the rule came from, a confidence of `certain` / `fairly certain` / `uncertain`, and the logic as pseudocode. **Every one of these is BFF work** — say so, and never write a BFF route as if the document declared it. A value the document cannot support at all is recorded as `not derivable — <what it would need>`, never as an invented field. A page that computes nothing keeps the heading and one line saying so.

`## Endpoint examples` is where `bind-ui`'s step 6 lands: one `###` per **distinct** endpoint the page uses, in first-use order — the request line against a real base URL, the headers that matter, the required request body, a trimmed response, and the interesting failure. Written once per page however many sections call it.

Head the file with `# <Page name>` matching the page's `spec.md`.

Do **not** repeat implementation-framework details here — the WaveMaker page name and the layout belong to `spec.md`. This file is about data only.

Keep empty sections — heading plus a `—` row or one line — so a reader can tell a concern was considered rather than skipped.

## 2 — Module level: `api-specs/api-catalog.md`

**The summary across every page**, written **after the last `api-bindings.md` is on disk** — it is a roll-up of what those files say, so writing it earlier means summarising bindings that do not exist yet.

See [FORMAT-api-catalog.md](FORMAT-api-catalog.md).

| Section | Columns |
|---------|---------|
| `## Coverage` | (blank), Count, Note |
| `## Endpoints` | Endpoint, Returns, Bound by, Notes — one `###` per resource |
| `## Unused endpoints` | Endpoint, Entity, Note |
| `## Unbound UI` | Page, Element, What it would need |
| `## Call sequences` | Sequence, Page, Chain, Note |
| `## Derived values` | Value, Pages, Needs, Note |
| `## Entity coverage` | Entity, Pages, Note |

Every endpoint in `.api-index.json` appears exactly once under `## Endpoints`, with `Bound by` naming the pages that call it. The last five sections are the cross-page questions no page file can answer: what nothing calls, what nothing serves, what has to be orchestrated across several calls, what the design asks for that the API does not hold, and which screens touch each entity.

`## Call sequences` rolls up every `###` from every page — the sequence, its page, and the chain written as `A → B → C`. It is the cheapest way to see where this API makes the UI work hardest, and that only becomes visible once every page is in one table. Keep the flowcharts, the step tables, and the worked examples in the page files.

`## Derived values` rolls up every page's `## Derived values` — the value, the pages showing it, and the endpoints the computation needs. One row per value even when two pages show it, so a reviewer can see that the same rule has to hold in both places. Keep it to endpoints: the pseudocode and thresholds stay in the page files, or this becomes another copy to keep in step.

Build it by reading back the `api-bindings.md` files you just wrote, not from memory of the binding decisions. It must describe the files that exist.

**Not written under `scope: page`.** Leave the existing `api-catalog.md` exactly as it is. A page-scoped run has walked one page, so it cannot say what the module as a whole calls, and rewriting the file from one page's evidence would wrongly mark most of the API unused. Tell the user it is now stale for that page and a module-scoped run will refresh it.

## Writing rules

- Plain sentences; a non-technical reader should follow `api-bindings.md`
- API paths, methods, parameter names, and field names verbatim from `.api-index.json`
- Real UI labels from the screenshots, not Figma layer names
- One `##` section per UI section, and one table in each: **Element | Trigger | Endpoint | Sends | Populates | Value source | Notes**
- Section names and their order come from the page's `spec.md`, verbatim
- One endpoint, one row per page load — the elements sharing a response are named in `Notes`, never bound a second time
- A list, table, or repeating card is one call plus a `Field | Card part | Value source` map, never one call per row
- Every value-showing element is classified `direct`, `derived`, or `static` — formatting a field is not deriving a value
- Every `derived` value has a `###` in `## Derived values` with where it shows, its minimal inputs and their calls, what moves it, its `Source`, a confidence of `certain` / `fairly certain` / `uncertain`, and pseudocode — stated as BFF work, with no invented BFF route
- Every element needing more than one call has a `###` in `## Call sequences` with a Mermaid flowchart, a step table whose every `Needs` resolves, and a `**Payload shapes:**` line — and the section row links to it instead of restating the chain
- Sequence flowcharts label every edge with the value that moves along it, mark parallel legs parallel, show fan-outs as `×N`, and use a `MISSING` node rather than an endpoint the document does not have
- Every distinct endpoint the page uses has one `###` in `## Endpoint examples`, marked illustrative, with real field names and real enum members, and responses trimmed to the fields the page consumes
- A rule is never satisfied by a batch, projection, `expand`, or aggregate parameter that is not in `.api-index.json`
- Housekeeping-only wide responses, unpaginated collection endpoints, growing-collection dropdowns, and every-page aggregates are noted in a clause, never given a row of their own
- Backtick every API path, method, parameter name, entity name, and field name
- Never invent an endpoint, parameter, field, page, or BFF route — including a field that would make a derivation work
- The `# <Page name>` heading must match the page's `spec.md`; no WaveMaker or other framework names in this file
- `api-catalog.md` carries endpoint, entity, who binds it, which chains it belongs to, and which values need computing — never parameters, payloads, field lists, pseudocode, or flowcharts
- Formats match the FORMAT-*.md examples in this folder

## Done when

- `api-specs/entities.md` exists from step 2
- Everything written sits under `figma-starter/api-specs/`; nothing under `figma-starter/<module>/` was created or changed
- Every page in `figmaPages[]` has an `api-specs/<NN>-<slug>/api-bindings.md` mirroring it, written in the order that list gives them
- Each `api-bindings.md` has one section per UI section from its `spec.md`, in the same order, with one table in each
- Every data-moving element is bound or listed as unbound, and no endpoint is bound twice for one page load
- Every list, table, and repeating card has its field map, and every field of the card is accounted for
- Every action a user story calls for — every save, delete, submit, publish — has a row with the endpoint behind it, or is listed as unbound
- Every value-showing element carries a `Value source`, and each `derived` one resolves to a `###` in that page's `## Derived values`
- Every `## Derived values` entry names its inputs and their calls, its `Source`, one of the three confidence values, and its pseudocode — or is `not derivable` with what it would need. No BFF route is named
- Every page has a `## Call sequences` section — a `###` per multi-call chain, or one line saying every element is served by a single call — and no sequence repeats a payload
- Every sequence step names an endpoint in `.api-index.json` or a `MISSING` node, and every `Needs` traces to the route, a user input, the previous page, or an earlier step
- Every distinct endpoint used by the page appears exactly once under `## Endpoint examples`
- Each page's `## Unused endpoints` section names the endpoints for its entities that it does not call
- **`scope: page`:** exactly one `api-bindings.md` was written, no other page's file changed, `api-catalog.md` was left untouched, and no endpoint was newly marked `unused`
- **Module scope:** `api-specs/api-catalog.md` was written last, lists every endpoint in `.api-index.json` exactly once with the pages that call it, rolls up every page's call sequences and derived values, and carries no parameter, payload, pseudocode, or flowchart detail
- No invented endpoints, fields, screens, or BFF routes

This is the final pipeline step. Hand the written specs to core `/speckit.specify` — see [orchestrator SKILL.md](../SKILL.md#spec-kit-handoff).
