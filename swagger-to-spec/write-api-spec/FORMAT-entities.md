# Entities format (`api-specs/entities.md`)

Markdown tables. **The entity model the UI must carry** — what each entity is, its fields, its relationships, and how it is identified and paged.

One `##` section per domain entity, primary entity first, each opening with a plain sentence saying what it is. Types come from `.api-index.json` verbatim: `string(uuid)`, `integer(int32)`, `Product[]` for a related collection.

```markdown
# Specification Service 1.2.0

- Source: `https://api.example.com/v3/api-docs` (openapi-3.0.1)
- Base URL: `https://api.example.com/api/v1`
- 3 entities, 2 of them domain entities

## Specification

The document a user creates, reviews and publishes. Primary entity of the module.

| Field | Type | Required | Allowed values | Notes |
|-------|------|----------|----------------|-------|
| `id` | `string(uuid)` | yes | — | Server-assigned |
| `name` | `string` | yes | — | Display name |
| `description` | `string` | no | — | — |
| `status` | `string` | no | `DRAFT`, `PUBLISHED` | Drives the status chip |
| `createdOn` | `string(date-time)` | yes | — | Server-assigned |
| `products` | `Product[]` | no | — | Products this specification covers |

| Property | Value |
|----------|-------|
| Identity | `id` — row keys, detail routes, `DELETE /specifications/{id}` |
| Written via | `SpecificationRequest` on `POST /specifications` and `PUT /specifications/{id}` |
| Client-supplied fields | `name`, `description`, `productId` |
| Server-assigned fields | `id`, `status`, `createdOn` — never sent by the client |

## Product

A product a specification can be filed against. Reference data — read-only in this API.

| Field | Type | Required | Allowed values | Notes |
|-------|------|----------|----------------|-------|
| `id` | `string` | yes | — | — |
| `name` | `string` | yes | — | — |

| Property | Value |
|----------|-------|
| Identity | `id` |
| Written via | — read-only |

## Relationships

| From | To | Cardinality | Via field |
|------|----|-------------|-----------|
| `Specification` | `Product` | many | `Specification.products: Product[]` |
| `Order` | `Customer` | one | `Order.customer: Customer` |

## Pagination

| Endpoint | Envelope | Payload | Paging parameters |
|----------|----------|---------|-------------------|
| `GET /specifications` | `PageSpecification` | `Specification[]` via `content` | `page`, `size` |

`PageSpecification.totalElements` gives the total across all pages. Lists must not assume every row arrives at once.

## Envelopes and request shapes

| Schema | Kind | Resolves to | Note |
|--------|------|-------------|------|
| `PageSpecification` | envelope | `Specification[]` | Transport only, not a domain entity |
| `SpecificationRequest` | request shape | `Specification` | Write side of `Specification` |
```

## Sections

| Section | Content |
|---------|---------|
| Title + bullets | `# <API title> <version>`, then source location and flavor, base URLs from `servers[]`, and entity counts |
| `## <Entity>` | One per domain entity, primary first. Open with a plain sentence saying what it is, then the fields table, then the properties table |
| Fields table | Every field: `Field`, `Type`, `Required` (`yes`/`no`), `Allowed values` (enums in full), `Notes` — a note only when it adds something the name does not |
| Properties table | `Identity`, `Written via`, `Client-supplied fields`, `Server-assigned fields`. Drop rows that do not apply; write `— read-only` for entities with no write path |
| `## Relationships` | Every relationship across all entities: From, To, Cardinality (`one`/`many`), and the field carrying it |
| `## Pagination` | Endpoints returning collections, their envelope, the payload, and the paging parameters |
| `## Envelopes and request shapes` | Wrapper and request-only schemas, named once and dismissed as transport |

Request shapes and envelopes are **not** given their own `##` section — they appear in the properties table of the entity they serve and in the final table. List enums in full: they drive dropdowns, chips, and validation.

Backtick every entity name, field name, type, and API path. Every entity and field must trace to a schema in `.api-index.json`; where a field's purpose is not derivable from the document, write `purpose unclear from the API document` in Notes rather than guessing.

This file states what the document states — nothing more. A value a screen shows but no field carries is **not** added here as a field: it belongs in that page's `## Derived values`, which exists precisely to record what the entity model leaves out. An entity referenced in `Relationships` or in a `Type` must have its own section.
