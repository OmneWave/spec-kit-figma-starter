---
name: swagger-bind-ui
description: >-
  Step 3 of swagger-to-spec. Wire the API to the screens: walk the pages in
  build order, match endpoints to each UI section, map list responses onto the
  cards they fill, work out which displayed values have to be computed in the
  BFF, chart the ordered call sequences, and write one worked example per
  endpoint. Produces the per-page binding decisions that write-api-spec records.
disable-model-invocation: true
---

# Bind UI

Work out, **page by page**, which endpoint backs which piece of the screen — and, where one call is not enough, the order the calls have to run in.

Do this the way the developer wiring the backend to the frontend would: take the journeys in the order they run, take each screen a section at a time, and for every piece of it decide which call fills it. Not "document the API against the UI" — *wire it*.

## Inputs — use all four

Binding is a judgement call, and it is only as good as the evidence. For **each** page in `figmaPages[]` — which holds one page when `scope` is `page`, every page otherwise — read:

Three of the four live in the **UI outputs** under `figma-starter/<module>/` — the folder `figma-images-to-spec` wrote. Read them there; nothing you produce goes back into it. `.api-index.json` gives you every path, relative to the project root, so there is nothing to assemble by hand: `figmaPages[].spec` and `.screens[]` for each page, `paths.userStories` and `paths.buildOrder` for the module.

| Input | Path | What it gives you |
|-------|------|-------------------|
| Page spec | `<module>/<NN>-<slug>/spec.md` (`figmaPages[].spec`) | The sections, element names, dialogs, interactions, and integration lines to bind |
| Screen images | `<module>/<NN>-<slug>/figma-resources/screens/*.png` (`figmaPages[].screens[]`) | Columns, field labels, card layouts, filters, and states the spec summarizes but does not enumerate |
| User stories | `<module>/user-stories.md` (`paths.userStories`) | The journeys — what the user does, in what order, and which actions must be possible |
| API index | `api-specs/.api-index.json` | The endpoints, parameters, and entities available |

The binding you decide here is written to `figmaPages[].bindings` — `api-specs/<NN>-<slug>/api-bindings.md`, the mirror of the page folder you just read.

**Look at the images.** A table's column headers, a card's layout, a form's field labels, and a filter's options are the strongest signal for which entity fields a screen actually uses — often stronger than the prose in `spec.md`.

## Walk the pages in build order

`figmaPages[]` is already sorted by `build-order.md`, which is the order the journeys run — login before dashboard, list before create. **Walk it in that order and do not re-sort it.** Folder numbering is a numbering; build order is the flow.

Binding in flow order is what makes each page's inputs obvious. A page rarely starts from nothing: the id its detail call needs was carried from the list page before it, the session its header shows was established at login. Read `user-stories.md` first, end to end, so you know which journey each page sits in, then bind each page knowing:

- **What arrives.** Which page precedes this one in the flow, and what it hands over — an id, a filter selection, a freshly created record.
- **What leaves.** Which pages this one leads to, and what they will need from it.
- **Which stories run through it.** Every story that touches this page has to be satisfiable with the endpoints available, including its actions.

When `scope` is `page`, this reading does **not** narrow. `pagesAvailable[]` is in build order and `user-stories.md` still describes the whole module, so place the page in the flow exactly as a full run would. Bind it as the page at that point in the journey, not as an island.

## 1 — Establish the page's entities

From the page's tables, forms, cards, and detail blocks, name the entities it displays or edits. Match screen labels to entity fields from `entities.md` — a column headed "Created on" is `Specification.createdOn`.

Expect some labels to match nothing. A screen shows more than the API stores, and a label with no field behind it is not a naming problem to solve — it is either a fixed design label or a computed value, and [step 4](#4--decide-what-is-carried-and-what-is-computed) sorts out which. Do not stretch a field to cover it.

List the entity the page is chiefly about first, then the supporting ones. Do not label them beyond that — a `primary`/`lookup` tag reads as precise while adding nothing, and on a page assembling a request shape, its server-side twin, and two nested relations there is no honest single answer.

The fact worth recording is **how each entity arrives**, because it decides whether a call is needed: nested inside another response, fetched by its own endpoint, carried in from the previous page in the flow, or held client-side from an earlier step. Say which in `Surfaces as`.

**List only the fields the page actually renders** in `Fields used` — not the entity's fields, and not the fields you expect the response to hold.

## 2 — Bind each section to an endpoint

First **list the page's UI sections** from its `spec.md` `Layout` block, in order — `Header`, `Cards Section`, `Filters`, `Table`, each `Dialog: <name>`, each wizard step. Each section becomes one section holding one table in the output, so get them right before binding anything.

Then work **one section at a time**. For each element in it that displays or moves data, find the endpoint that serves it, and record when the call fires, what it sends, and what comes back:

| Element | Trigger | Endpoint | Sends | Populates | Value source | Notes |
|---------|---------|----------|-------|-----------|--------------|-------|
| `<Page> / <element>` | `on load` | `<METHOD> <path>` | `<param>` ← `<UI input>` | `<status>` `<payload>` → `<what it fills>` | `direct` | — |

That single row is the whole binding — trigger, parameters *with their sources*, response *with its target*, and whether a field carries what the element shows. Collect all of it while you are in the section; nothing gets deferred to a page-level parameters or responses list, because there isn't one. `Value source` comes from [step 4](#4--decide-what-is-carried-and-what-is-computed) — bind the element first, then decide whether the response really contains the words on the screen.

Keep a section's load behaviour and its interaction behaviour **together** — the `Trigger` column separates them (`on load`, `on open`, `on type`, `on click`, `on blur`, `—` for a fixed label). The spec's `Interactions` block tells you the triggers; it is not a separate output section.

The `Element` column uses the same location form as the page `spec.md`, so the two files line up.

Signals to match on, strongest first:

1. **Entity match** — the element shows `Specification` data; the endpoint's `primaryEntity` is `Specification`. Where `entityInferred` is true the entity came from the resource name, not the document — still a strong signal, but lean harder on the other four before committing.
2. **Cardinality** — a table, list, or repeating card needs `collection: true`; a detail block or form needs a single-item endpoint.
3. **Method and intent** — Create → `POST`, Edit/Save → `PUT`/`PATCH`, Delete → `DELETE`, view/search → `GET`.
4. **Parameters** — a search field maps to a query parameter; a row action maps to a `{id}` path parameter.
5. **Naming** — `operationId`, `summary`, and `tags` as a tiebreaker, never as the only evidence.

Bind at **element level** — the search field, the filter dialog's Search button, each row action — not "this page uses the specifications API".

### One call, however many places it shows

The same response usually fills more than one part of a screen. An account fetched for the header also fills three summary cards; a collection fetched for the table also feeds a count in the toolbar. **Fetch it once.**

So before adding a call, check what the page has already loaded. Where two elements are served by the same response, bind them to the same endpoint and say in both rows that the call is shared — never write two rows that read as two round trips. Where an element could be served either by a call already being made or by one of its own, take the one already being made.

The same holds across a chain: if the page loaded the account on arrival, a sequence needing the account does not start by fetching it again.

### Lists, tables, and repeating cards

Wherever the screen repeats a structure — table rows, a grid of cards, a stacked panel list — that is almost always **one collection endpoint returning an array**, not one call per item. Find that endpoint and bind it once. A per-row call is the most common mistake here and the most expensive.

Record it in two parts:

1. **The call**, as one row in the section's table: the collection endpoint, its parameters, and that it populates the list.
2. **The field map**, as a table directly below, saying which field of one element of the array fills which part of one row or card. This is what a developer builds the card component from.

| Field | Card part | Value source |
|-------|-----------|--------------|
| `Player.name` | Card title | `direct` |
| `Player.position` | Subtitle chip | `direct` |
| `Player.matchesPlayed` | — | input to `Match quota` only |
| `—` | Quota bar | `derived → [Match quota](#derived-values)` |

Rules for the field map:

- **One element of the array, not the array.** The map describes a single card; the repetition is the list binding above it.
- **Every part of the card that shows data gets a row**, in the order it appears on the card. Read the screenshot for this — the spec rarely enumerates a card's internals.
- **A computed value inside a card is still `derived`** and still lands in `## Derived values`, with the same BFF treatment as anywhere else. A `Match quota` bar over `matchesPlayed / teamMatches` is derived, computed once per element, in the BFF — not in the card component.
- **A field that only feeds a derivation** gets a row with `—` as its card part, so a reader can see why it is being fetched.
- **A nested list inside a card** — a card holding its own repeating strip — gets its own field map **only if a separate endpoint or a nested array backs it**. Where it is the same response's nested array, say which field it comes from and map it. Where the design repeats a shape that is not API-backed, flatten it into the parent's rows rather than inventing a level.

### Read the document harder before adding a call

Most of what makes a binding efficient is already in `.api-index.json`, unread. Before you settle on an endpoint, mine it for these — each one either removes a call or replaces client-side work with something the server already does:

| Signal in the document | What it means for the binding |
|------------------------|-------------------------------|
| A **query parameter** on a collection endpoint (`status`, `productId`, `from`/`to`, `q`, `sort`, `page`) | The filter, sort, or search is server-side. Bind the control to the parameter instead of fetching everything and filtering in the client |
| An **enum** on a field | The dropdown's options are in the document. No call at all — only the selected value is sent |
| A **nested entity or array** on a response | The related data arrives with its parent. Do not add a second call for something already in hand |
| An **envelope counter** (`totalElements`, `totalPages`) | A count without traversing pages. Prefer it over fetching every page to count |
| A **batch parameter** — repeatable or comma-separated `ids`, `productIds`, an `in`-style filter | One call for the whole page of rows instead of one per row. This is the parameter that kills an N+1 outright |
| A declared **`expand`, `include`, or `embed`** parameter | The related entity arrives on the parent, so a hop disappears. Only usable where the document declares it |
| A **projection parameter** (`fields`, `select`, `view`, or a `summary` variant beside a `full` one) | The response can be narrowed to exactly what the screen renders |
| A **narrower endpoint beside a wider one** — a list returning 6 fields where the detail returns 40 | The table binds the list one |
| **Pagination parameters** (`page`/`size`, `limit`/`offset`, `cursor`) — or their **absence** on a `collection: true` endpoint | Present: bind the size the screen renders. Absent: note that the call returns the whole table |
| A **path parameter** (`{id}`, `{loanId}`) | The call cannot fire until something supplies that id — user input, the route, the previous page in the flow, or an earlier response. The last case is a call sequence, see [step 5](#5--chart-the-call-sequences) |
| A **`requestBody` field typed as another entity** or as its id | That reference has to be resolved before the write can be submitted, which usually means a lookup call earlier in the flow |
| A **`4xx` response** the document declares (`404`, `409`, `422`) | A real branch on the screen — a not-found state, a duplicate-name message, a validation error — not just an error toast. Bind it where the screen shows it |
| The **same endpoint** matching two elements | One call, shared. Say so in both rows rather than implying two separate calls |
| `entityInferred: true` | The entity came from the resource name, not the document. Usable, but say so where the binding leans on it |

The general rule: **the cheapest correct binding wins.** Where two endpoints would both serve an element, prefer the one that is already being called, then the one that needs fewer parameters, then the one that returns less. Note the alternative rather than silently discarding it.

## 3 — Bind the actions

A screen is not only what it displays. Every button that submits, saves, approves, deletes, or advances a wizard is a write, and the user stories are where those live — a story reading *the user submits the specification for review* is an assertion that a write endpoint exists and is reachable from that screen.

So go through `user-stories.md` and, for **every action a story describes**, confirm it lands somewhere:

- The element that triggers it is in a section table, with `on click` (or the real trigger) and the write endpoint it calls.
- The request body is recorded in `Sends`, with each field's source — the form field, the entity being edited, or an id carried from the previous page.
- The response is recorded in `Populates`, including what happens on success: a navigation, a toast, a reloaded table.
- The `4xx` branches the document declares are bound where the screen shows them.

An action a story requires with no endpoint behind it is **unbound UI**, recorded like any other — not quietly dropped because it is a button rather than a field. An action whose write needs a value the page cannot supply is a broken chain, and belongs in [step 5](#5--chart-the-call-sequences).

This is a check, not a section. Actions stay in their own section's table, where the rest of that region of the screen is.

## 4 — Decide what is carried and what is computed

An endpoint being bound does not mean the screen's words are in the response. Go back over every element that **shows a value** and ask one question: *does a field carry this, or does the screen state something the API never states?*

Classify each as exactly one of:

| Value source | When |
|--------------|------|
| `direct` | A field on a response holds this value; the screen renders it |
| `derived` | No field holds it — it exists only once you compute over one or more fields |
| `static` | The same for every record — a design label, a legend, a unit, a column header |
| `—` | The element shows no value at all: a button, a nav item, an icon that only opens something |

**Formatting is not derivation.** A date shown `12 Aug 2026`, an amount with a currency symbol, an enum mapped to a chip colour, two fields printed side by side as `120/120` — all `direct`. The field *is* the value; the screen is dressing it. What makes a value `derived` is that the screen asserts a **fact the document does not contain**.

That is the distinction worth getting right, and a card is the clearest case of both at once:

> `Payments completed 120/120` is `direct` — `paidInstalments` and `totalInstalments`, printed together.
> `Account Health: Excellent` on the same card is `derived` — nothing in the document holds `Excellent`, and nothing says where `Excellent` stops and `Good` begins. It is the ratio of those same two fields, plus a threshold that only the design knows.

### Every derivation is BFF work

A derived value is computed **in the backend-for-frontend layer**, not in the component that renders it. That is what makes it worth writing down: it is a piece of server-side work the API does not do and someone has to build. Write each one as a starter implementation the BFF team can take as-is.

**Do not propose a BFF route.** No `GET /bff/accounts/{id}/health`. The document is the only source of endpoints, and a proposed path sitting in a spec full of real ones is indistinguishable from a real one six weeks later. Say the computation belongs in the BFF and give the logic; how it is exposed is the BFF team's call.

For each `derived` value, work out and record:

1. **Inputs — the minimal set.** Only the attributes that actually enter the rule, each named with the endpoint that supplies it. Never "the response" or a whole entity. If two fields are enough, do not list five. Where the same value could be computed two ways, take the one needing fewer fields and fewer calls, and note the alternative rather than silently choosing.
2. **The calls behind it.** Prefer fields already on a response the page loads. Name an extra endpoint only when no loaded response carries the field. Where the inputs span endpoints, say whether they can be fetched in parallel or one feeds the next. Where getting them takes an ordered chain, that chain is a sequence — chart it in [step 5](#5--chart-the-call-sequences) and point the derived value at it rather than describing the order twice.
3. **The logic, as pseudocode.** A fenced block a developer can implement from: the arithmetic or comparison, every threshold, band and label written out, and the edge cases the inputs allow — a zero denominator, a null, an empty collection. Language-agnostic; real field names from the document. A rule with the bands left off is not a rule anyone can implement.
4. **What moves it.** Which change to *that record* makes the value change — a payment posted, an instalment gone overdue, a status transition. This is what tells the implementation when to recompute.
5. **Where it came from**, in a phrase — `document`, `card legend`, `screenshot`, `story`. Thresholds and verdict labels are almost never in an API document, and this is what tells a reviewer whether there is anything to check against.
6. **How sure you are** — exactly one of `certain`, `fairly certain`, `uncertain`. No sentence, no caveat trailing it; the `Source` phrase carries the reason.

| Confidence | When |
|------------|------|
| `certain` | Every input is a documented field and the rule is unambiguous — a subtraction of two fields the card names |
| `fairly certain` | The inputs are documented, the shape of the rule is clear, but a detail is read off the design — a rounding, a label, which of two fields the card means |
| `uncertain` | A threshold, a band, or the rule itself came from the design and nothing in the document can confirm it |

Guardrails, because this is where invention creeps in:

- **Only values a screen actually shows.** No intermediate quantities, no derivations nothing displays.
- **Only per-record dynamic values.** The test: would this differ between two records of the same entity, or change when that record changes? If not, it is `static`. A page title, a column header, a legend, a unit, and a fixed helper sentence are not derivations. Neither is a total the envelope already gives you — `totalElements` is `direct`.
- **Never invent a field to make a rule work.** Every input must be a field in `.api-index.json`. If the rule needs something that is not there, the value is **not derivable** — record it as such, with what it would need. That is a finding, exactly like unbound UI.
- **An aggregate over a paged collection is only right if every page is fetched.** Say so, and prefer a count the envelope already carries.
- **A derived value never becomes an entity field.** `entities.md` states what the document states; this is the page recording what the document leaves out.

## 5 — Chart the call sequences

A section table says *which* endpoint serves an element. It cannot say **in what order**, and on a generated API one call is often not enough: the id the call needs is itself the result of an earlier call. Those chains are where an implementation goes wrong — the row looks bound, and the developer discovers at build time that nothing supplies `{scheduleId}`.

So for every element whose data takes **more than one call to obtain**, work out the chain and record it as a named sequence. This is the one part of the output that is **not** a table: a chain has branches, loops, and parallel legs, so it is written as a flowchart plus a step table. See [FORMAT-call-sequences.md](../write-api-spec/FORMAT-call-sequences.md) for the exact shape.

### When a sequence exists

Write one when any of these is true. Each is a fact about the document, not a guess:

| Trigger | Example |
|---------|---------|
| **A parameter is supplied by another response** — the path or query parameter is not on the route and the user does not type it | The schedule table needs `{loanId}`, which only `GET /loans` returns |
| **A displayed label needs resolving** — the response carries an id, the screen shows a name | Rows carry `productId`; the column header reads `Product`, so `GET /products` has to be fetched and joined |
| **A write has prerequisites** — a form cannot be submitted until reference data or a validation call has run | `POST /specifications` needs a `productId` that `GET /products` supplies |
| **A write is itself ordered** — create, then attach, then submit | `POST /orders` → `POST /orders/{id}/items` → `POST /orders/{id}/submit` |
| **An aggregate needs every page** — a count or total the envelope does not carry | Summing `amount` across all pages of `GET /accounts/{id}/payments` |
| **A derivation's inputs span endpoints** — the rule in `## Derived values` reads fields from two responses | `Payment reliability` needs the account *and* its payments |
| **No single endpoint serves the section** — nothing returns what the region shows, but a filter or lookup endpoint reaches it in two hops | A panel of overdue accounts from `GET /accounts?status=OVERDUE` then a per-status lookup |

A single call with parameters the screen already has is **not** a sequence. Do not write one for `GET /specifications` on page load — the section table already says everything there is to say. Neither is a per-row fan-out you were about to write: find the collection endpoint first.

### What to record for each sequence

1. **A name and what it produces** — name it after the thing on screen it fills (`Populate the branch dropdown`, `Load the repayment schedule`), and name the element(s) it serves so the section rows can point at it.
2. **The flowchart** — a Mermaid `flowchart` showing each call as a node in order, the branch conditions the document declares (`404` → empty state, `409` → duplicate message), any loop or fan-out, and the UI target the chain ends at. The chart is the flow; do not make the reader reconstruct it from prose.
3. **The steps, one row each** — what the call *needs* and where that comes from, what it *yields* that the next step consumes, and whether it blocks the next step or can run alongside it. This is where the chain becomes checkable: every `needs` must be satisfied by the route, a user input, the previous page in the flow, or an earlier step's `yields`. If one is not, the sequence is broken and that is a finding, not something to paper over.

The payloads are **not** repeated here. Each endpoint's request and response are written once per page in `## Endpoint examples` — see [step 6](#6--write-one-example-per-endpoint). A sequence shows the *value that carries from one step to the next*, on the flowchart edges and in the step table, and points at the examples for the shapes.

### Make the chain as cheap as it can be

Chart the chain you would actually build, not the first one that works. In order:

- **Reuse a response already loaded.** If the page already fetched the account, the chain does not start with fetching it again. Two elements needing one call share it — say so.
- **Collapse a per-row fan-out.** N calls for N rows is the most common waste in a generated API. If a collection endpoint returns the same data in one call, fetch it once and join client-side, and say which you chose and why.
- **Push work to the server.** A filter parameter beats fetching a page and discarding rows; `sort` beats sorting in the client; the envelope's `totalElements` beats counting.
- **Parallelise anything without a data dependency.** Serialise a step **only** when it consumes an earlier step's output. Two independent lookups on page load are one wait, not two — say `parallel` rather than implying an order.
- **Cache what does not change per record.** Reference lists behind dropdowns — products, branches, currencies — are fetched once, not per row and not per dialog open. Say where the value is held.
- **Prefer the shorter chain.** Where the same screen value is reachable two ways, take the shorter one, and note the alternative so a reviewer can disagree.

Where you rejected a cheaper-looking option, say what made it wrong.

### Guardrails

- **Every step is a documented endpoint.** No invented call, no invented parameter, no `?expand=` that the document does not declare. If the chain needs a call that does not exist, the sequence is **incomplete** — record it with the step missing and say what the API would need. That is the same class of finding as unbound UI.
- **Every `needs` is satisfied.** Trace each one to the route, a user input, the previous page in the flow, or an earlier step. An unsatisfied `needs` means the screen cannot be built as designed; say so plainly.
- **Only sequences that serve something on the screen.** No speculative flows, no "you might also want to".
- **The chain lives in one place.** The section row names the sequence; the sequence holds the order and the branches. Do not restate the chain in the `Notes` column.

## 6 — Write one example per endpoint

A binding table says which call fills what. It does not show a developer what the call *looks like*. So every endpoint the page uses gets one worked example: the request as it would actually be issued, and a response as it would actually come back.

**One example per distinct endpoint, per page** — written once, at its first use, however many sections bind it. An endpoint serving the table, the search field, and a filter dialog is one example with a note that the parameters vary, not three.

Each example carries:

1. **The request line** — method and path with the path parameters filled in and the query string the screen would send.
2. **The headers that matter** — `Authorization` where the document declares a security scheme, `Content-Type` on a request with a body, and any header parameter the endpoint declares. Not a full browser header dump.
3. **The request body**, for writes — the shape from `requestBody`, with every required field present.
4. **The response** — the status the screen depends on, and a body trimmed to the fields this page actually uses, with `…` for the rest.
5. **The interesting failure**, where the document declares one — the `404`, `409`, or `422` that the screen has a state for, in a line or two.

Keep it honest, in exactly the way the sequence examples were:

- **Field names, types, and enum members come from the document.** A `status` in an example is one of the values the enum declares.
- **The values themselves are illustrative** — ids, names, dates, amounts. Mark them so once, and never present an example figure as documented.
- **Trim the response.** Show the fields this page consumes. A full paste of a 40-field entity buries the four the card uses.

## 7 — Bind the journeys

Cross-page moves from the page's `Integration` section often carry data. For each, note what the next page needs — usually an id passed to a `GET /{id}` on arrival:

| Source | Destination | Data passed | Destination loads |
|--------|-------------|-------------|-------------------|
| `Specification List / Dialog: Row options / Edit` | `Edit Specification` | `Specification.id` | `GET /specifications/{id}` |

Check these against `user-stories.md` and `build-order.md`: every journey there must be achievable with the endpoints available, and the hand-off must match what the destination page's own bindings expect to receive. Where it is not, that is a gap worth stating.

## 8 — Record what does not match

Both leftovers are findings the implementation team needs. Never hide them, and never invent a binding to make them go away.

- **Unbound UI** — an element that clearly moves data but has no endpoint, including an action a user story requires. Say what it would need. It stays in its own section's table, as a row with no endpoint — not collected into a list of its own.
- **Values that cannot be computed** — a `derived` value whose inputs are not in the document. Record the value with what it would need, not an invented field.
- **Broken chains** — a sequence with a step the document cannot supply, or a `needs` nothing satisfies. It stays in `## Call sequences`, charted as far as it goes, with the missing link named. A chain that stops halfway is a design the API cannot serve yet, and it is worth more to the team than a chain quietly completed with an invented call.
- **Unused endpoints** — endpoints for the page's entities that no element on this page calls. These belong to no section, so they are the one leftover recorded at page level. They may belong to another page; only flag one as genuinely unused after checking every page. That module-wide verdict is not written here — it is what `api-catalog.md` records once every page has been walked.

When `scope` is `page` you have not checked every page, so "genuinely unused" is not a claim you can make. List the endpoint as unused *by this page* and say the other pages in `pagesAvailable[]` were not examined. Cross-page `Integration` rows still get written — the destination page's spec is readable whether or not it is in scope.

If two endpoints are plausible for one element, bind the better fit and note the alternative — do not silently pick one.

## Confidence

Mark any binding you are not sure of. A wrong binding stated confidently is worse than an honest `uncertain` — the reviewer can resolve an open question, but will not re-check a claim that reads as settled.

The same holds, more sharply, for derived values, where confidence is one of `certain`, `fairly certain`, `uncertain` and sits beside the phrase saying where the rule came from. A binding can be checked against the document; a threshold cannot, because it is not in the document to check.

## Done when

- Every page in `figmaPages[]` has been walked with its spec **and** its screen images, **in build order**
- `user-stories.md` was read before binding, and each page was bound knowing what the page before it hands over and what the pages after it need
- Each page's UI sections are listed from its `spec.md`, in order, and every section was walked
- Every data-moving element on each page is either bound or marked unbound within its own section
- Each binding records its trigger, so load and interaction behaviour stay distinguishable within a section
- Each binding is complete on its own — trigger, parameter sources, and response targets all captured together
- No endpoint is called twice for one page load — responses shared by several elements are bound once, and both rows say so
- Every list, table, and repeating card is bound to **one** collection endpoint, with a field map saying which field fills which part of one row or card
- A nested list inside a card has its own field map where an endpoint or a nested array backs it, and is flattened where nothing does
- Every action a user story describes lands on a bound write endpoint, with its body sources, its success behaviour, and the `4xx` branches the document declares — or is recorded as unbound UI
- Every element that shows a value is classified `direct`, `derived`, or `static`, and formatting was not mistaken for derivation
- Every `derived` value has its minimal input set with the endpoint behind each attribute, pseudocode with every threshold and edge case, what moves it, a one-phrase source, and a confidence of `certain`, `fairly certain`, or `uncertain`
- Every `derived` value is stated as BFF work, and **no BFF endpoint path was invented**
- Derived values that the document cannot support are recorded as not derivable, with what they would need — no invented fields
- Every element needing more than one call has a named sequence with a flowchart and a step table — and the section row points at it
- Every step in every sequence is a documented endpoint, and every `needs` traces to the route, a user input, the previous page, or an earlier step's output
- Every endpoint the page uses has exactly one worked example with its request, its headers, its body where there is one, and a trimmed response
- Per-row fan-outs are collapsed into one collection call where the document allows it; parallel legs are marked parallel rather than implied to be ordered
- The document was mined before calls were added — server-side filters, enums, nested data, batch and projection parameters, and envelope counters used where they exist
- Cross-page journeys carrying data are bound, and checked against `user-stories.md`
- Unused endpoints are identified across the whole module, not just per page — or, in a page-scoped run, reported as unused *by this page* with the unexamined pages named
- Uncertain bindings are marked

**Then:** continue to [write-api-spec](../write-api-spec/SKILL.md) to write the files.
