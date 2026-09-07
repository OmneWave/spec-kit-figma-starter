---
name: swagger-derive-entities
description: >-
  Step 2 of swagger-to-spec. Turn normalized schemas in .api-index.json into the
  entity model the UI must carry — fields, types, required flags, enums, and
  relationships. Use after pulling a Swagger document, before binding endpoints
  to screens.
disable-model-invocation: true
---

# Derive entities

Decide **which entities the application actually needs** and describe each one as a data contract the UI can be built against.

Read `figma-starter/api-specs/.api-index.json`. Write `figma-starter/api-specs/entities.md` using [FORMAT-entities.md](../write-api-spec/FORMAT-entities.md).

Read `paths.userStories` alongside it. The document says what schemas exist; the stories say which of them the application actually moves through, and in what order. That is what tells you the difference between a domain entity the screens revolve around and a schema the generator emitted. It does not change what a field says — every field, type, and enum still comes from the document, verbatim — it changes which entities lead and how each one is introduced.

## 1 — Separate real entities from noise

Not every schema in a document is an entity. Classify each `entities[]` member:

| Keep as | When |
|---------|------|
| **Entity** | It is a domain noun with its own identity — `Specification`, `Product`, `Customer` |
| **Request shape** | Only ever a `requestBody` — `SpecificationRequest`, `CreateOrderPayload` |
| **Envelope** | Only wraps another entity — `PageSpecification`, `ApiResponse`, `ListResult` |

Use `usedBy[]` to tell them apart: an entity that appears only as a `requestBody` entity is a request shape; one whose fields are just `content` + paging counters is an envelope.

List entities in full. Fold request shapes into the entity they create or update, as a note about which fields are writable. Mention envelopes once, under pagination — they are transport, not domain.

## 2 — Describe each entity

Each entity gets a `##` section: a plain sentence saying what it is, a **fields table**, and a **properties table** (identity, write path, client- vs server-supplied fields).

For every entity, record each field with:

- **Name** exactly as the API spells it — do not camelCase or rename it.
- **Type** from `type` (`Product[]` for a related collection, `string(uuid)` for a formatted scalar).
- **Required** from `required`.
- **Allowed values** from `enum`, listed in full — these drive dropdowns, status chips, and validation.
- **Notes** from `description`, only when it adds something the name does not.

Never add a field that is not in `.api-index.json`, and never drop one because it looks internal. If a field's purpose is unclear from the document, write `purpose unclear from the API document` rather than guessing.

## 3 — Record relationships

A field whose `entity` is set is a relationship. Capture direction and cardinality:

| From | To | Cardinality | Via field |
|------|----|-------------|-----------|
| `Specification` | `Product` | many | `Specification.products: Product[]` |
| `Order` | `Customer` | one | `Order.customer: Customer` |

These are what tell the implementation whether a screen needs a nested fetch, a join, or just an id.

## 4 — Note pagination and identity

- **Identity** — which field identifies each entity (`id`, `uuid`, `code`). Needed for row keys, detail routes, and delete calls.
- **Pagination** — which endpoints return `collection: true` and what the envelope carries (`totalElements`, `page`, `size`). This decides whether lists are paged or fully loaded.

## Writing rules

- Plain sentences; a non-technical reader should understand what each entity *is*
- API field names verbatim; no invented fields, types, or values
- Backtick every entity name, field name, type, and API path
- Enums listed exhaustively
- Every entity in the file traces to a schema in `.api-index.json`
- Do not describe UI here — that is bind-ui's job

## Done when

- `figma-starter/api-specs/entities.md` exists and matches [FORMAT-entities.md](../write-api-spec/FORMAT-entities.md)
- Every domain entity has its full field list, with required flags and enums
- Relationships are recorded with direction and cardinality
- Request shapes and envelopes are accounted for, not listed as entities
- Identity and pagination are stated

**Then:** continue to [bind-ui](../bind-ui/SKILL.md).
