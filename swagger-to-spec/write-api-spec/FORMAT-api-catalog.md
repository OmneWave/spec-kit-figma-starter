# API catalog format (`api-specs/api-catalog.md`)

Markdown tables. **The module-wide summary, written last** — every endpoint with the pages that call it, and what is left over on both sides once all the pages have been bound.

This is the one file that can only be written after every page's `api-bindings.md` exists. A page file answers *what does this screen call*; this one answers the questions no single page can: *which screens call this endpoint, what does nothing call, what did we fail to serve, and which values the design shows are not in the API at all*.

It is a **coverage view, not a second copy of the document**. It never restates parameters, request bodies, response shapes, or field lists — `.api-index.json` holds those and the page files interpret them. Each endpoint gets one row: what it is, what it returns, and who binds it. The same restraint applies to derived values and call sequences: this file names the value or the chain, the pages it belongs to, and the calls it needs — the pseudocode, the flowchart, and the worked examples stay in the page file that worked them out.

```markdown
# Specification Service 1.2.0 — API catalog

- Source: `https://api.example.com/v3/api-docs` (openapi-3.0.1)
- Base URL: `https://api.example.com/api/v1`
- Bound against module `specifications`, 4 pages
- 12 endpoints across 3 resources — 9 bound, 3 unused

## Coverage

| | Count | Note |
|--|-------|------|
| Endpoints bound | 9 of 12 | Called by at least one page |
| Endpoints unused | 3 | No page calls them — see below |
| Pages bound | 4 of 4 | Every page with a `spec.md` has bindings |
| Unbound UI elements | 2 | Elements that move data with no endpoint to serve them |
| Derived values | 3 | Shown on a screen but carried by no field — 1 of them not derivable at all |
| Call sequences | 4 | Elements needing more than one call — 1 chain the document cannot complete |

## Endpoints

One row per endpoint, grouped by resource. `Bound by` names every page that calls it.

### Specifications

| Endpoint | Returns | Bound by | Notes |
|----------|---------|----------|-------|
| `GET /specifications` | `Specification[]` | Specification List | Paged; also serves the search field |
| `GET /specifications/{id}` | `Specification` | Edit Specification, View Specification | On arrival from the list; on View it also feeds the `Completeness` and `Product count` derivations |
| `POST /specifications` | `Specification` | Create Specification | Submit on the final wizard step |
| `PUT /specifications/{id}` | `Specification` | Edit Specification | — |
| `DELETE /specifications/{id}` | — | Specification List | Row action, via the confirm dialog |
| `POST /specifications/{id}/publish` | `Specification` | — | Unused — no screen publishes |

### Products

| Endpoint | Returns | Bound by | Notes |
|----------|---------|----------|-------|
| `GET /products` | `Product[]` | Create Specification, Advanced Filters | Fills the product dropdown on both |

## Unused endpoints

Endpoints no page in the module calls. Each is either a screen nobody designed or an endpoint nobody needs — worth deciding which.

| Endpoint | Entity | Note |
|----------|--------|------|
| `POST /specifications/{id}/publish` | `Specification` | No screen moves a specification out of `DRAFT`, though `status` has a `PUBLISHED` value |
| `GET /audit-events` | `AuditEvent` | Entity appears on no screen |
| `DELETE /products/{id}` | `Product` | Products are read-only in the UI |

## Unbound UI

Elements that move data with no endpoint behind them, gathered from every page.

| Page | Element | What it would need |
|------|---------|--------------------|
| Specification List | `Created on range` | Date-range parameters on `GET /specifications`; only client-side filtering is possible today |
| Specification List | `Button: Export` | No export endpoint in the document |

## Call sequences

Screen elements that take more than one call to fill. Each page's `api-bindings.md` holds the flowchart, the
step-by-step and the endpoint examples; this table is the module-wide list of what has to be orchestrated.

| Sequence | Page | Chain | Note |
|----------|------|-------|------|
| Load the repayment schedule | Account Detail | `GET /accounts/{accountNo}` → `GET /accounts/{accountId}/loans` → `GET /loans/{loanId}/schedule` | Each id comes from the response before it; nothing can be parallelised |
| Resolve product names for the loan rows | Account Detail | `GET /products` | Joined on `productId` client-side; per-row `GET /products/{id}` avoided. Cacheable — Advanced Filters needs the same list |
| Grade payment reliability | Account Detail | `GET /accounts/{id}/payments` ×(1 + n) | Aggregate over a paged collection with no status counts; page 0 is shared with the payment table |
| Submit the new specification | Create Specification | `GET /products` → `POST /specifications` | `productId` must be resolved before the write; `409` returns the user to step 1 |
| Reconcile against the ledger | Account Detail | `GET /loans/{loanId}/schedule` → **MISSING** | Incomplete — needs a ledger endpoint keyed by loan and instalment, or `ledgerBalance` on `Instalment` |

## Derived values

Values a screen states that no field carries — all of it BFF work. Each page's `api-bindings.md` holds the pseudocode and the thresholds; this table is the module-wide list of what has to be computed and the calls it needs.

| Value | Pages | Needs | Note |
|-------|-------|-------|------|
| `Completeness` | View Specification | `GET /specifications/{id}` | Share of optional fields filled; the bands are not in the document |
| `Product count` | View Specification, Edit Specification | `GET /specifications/{id}` | Length of the nested `products` array — no extra call |
| `Last updated by` | View Specification | — | not derivable — `Specification` has no audit fields, and `GET /audit-events` cannot be filtered by specification |

## Entity coverage

| Entity | Pages | Note |
|--------|-------|------|
| `Specification` | Specification List, Create Specification, Edit Specification | Primary entity of the module |
| `Product` | Create Specification, Specification List | Reference data — dropdowns only |
| `AuditEvent` | — | On no screen |
```

## Sections

| Section | Columns | Notes |
|---------|---------|-------|
| Title + bullets | — | `# <API title> <version> — API catalog`, then source and flavor, base URL, the module and page count it was bound against, and the endpoint tally |
| `## Coverage` | (blank), Count, Note | The run in six numbers. `X of Y` wherever there is a total to be a fraction of |
| `## Endpoints` | Endpoint, Returns, Bound by, Notes | One `###` per resource, in `resources[]` order; every endpoint in `.api-index.json` appears exactly once. `Bound by` names each page that calls it, or `—` when nothing does |
| `## Unused endpoints` | Endpoint, Entity, Note | The `Bound by: —` rows again, with a sentence each on why nothing calls them |
| `## Unbound UI` | Page, Element, What it would need | Every unbound row from every page's tables, gathered in one place |
| `## Call sequences` | Sequence, Page, Chain, Note | Every `###` from every page's `## Call sequences` — the chain as `A → B → C`, never the flowchart or the payloads |
| `## Derived values` | Value, Pages, Needs, Note | Every row from every page's `## Derived values`, one row per value even when several pages show it |
| `## Entity coverage` | Entity, Pages, Note | Which screens touch each entity; `—` for entities on no screen |

`Returns` is the endpoint's `primaryEntity`, `[]` when `collection` is true, `—` when it returns nothing. Where `entityInferred` is true, mark it `Specification[] (inferred)` — the entity came from the resource name, not the document.

In `## Derived values`, `Needs` is the set of endpoints the computation reads, or `—` when the value is not derivable from this API at all. Keep it to endpoints: no thresholds, no pseudocode, no field lists. A value that several pages show is one row with both pages named, so a reviewer can see at a glance that the same rule has to hold in two places. Where an endpoint appears in `Needs` only because a derivation reads it, say so in that endpoint's `Notes` under `## Endpoints` — otherwise it reads as if a table or form were bound to it.

In `## Call sequences`, `Chain` is the ordered endpoint list joined by `→`, with `×(1 + n)` or `×N` where a step repeats and `**MISSING**` where the document cannot complete the chain. Keep flowcharts, step tables, and worked examples out: they are the page file's job, and a copy here would be a second version to keep in step. Where an endpoint appears in a chain only as an intermediate hop, say so in its `Notes` under `## Endpoints` — otherwise it reads as if an element were bound directly to it.

Do not add parameter, request-body, or response-shape columns. A reader who needs that detail wants the page's `api-bindings.md` or `.api-index.json`, and a copy here would be a second version to keep in step.

Backtick every API path, method, parameter name, entity name, and field name. Every endpoint must exist in `.api-index.json`, and every page named must have an `api-bindings.md` that actually contains that binding — this file is a roll-up of what was written, never a claim about what should have been. That applies to the links too: every page link here must resolve to a file on disk, and every entity anchor to a `##` heading in `entities.md`.
