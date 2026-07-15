# Page spec format (`<NN>-<slug>/spec.md`)

Tab-indented. **Complete page specification** — source images, layout, dialogs, interactions (with source → destination), and cross-page navigation.

## Source → destination notation

Every interaction and integration line uses:

```text
<Source> → <Destination> — <action or effect>
```

| Location form | Example |
|---------------|---------|
| Page | `Specification List` |
| Page / step | `Create Specification / General details` |
| Page / dialog | `Specification List / Dialog: Row options` |
| Page / state | `Specification List / filtered table` |

Same-page state changes use the page on both sides with a different state label. Cross-page moves use **Integration**. Popups and in-page UI use **Interactions**.

```text
Page: Specification List
WaveMaker page: SpecificationList

	Source images
		figma-resources/screens/10-specification-list.png — default table, Contract tab selected
		figma-resources/screens/11-specification-list.png — success toast after create
		figma-resources/screens/12-specification-list.png — table with row options context
		figma-resources/screens/13-option.png — Dialog: Row options (menu open)

	Layout
		Leftnav, Header
		Title "Specifications" on the left
		Button: Create on the right
		Search text field covering full width of the page. Filter icon on the right
		List/table of specifications with columns (name, status, description, ...) + button (more options)
		4 filter options in table view Product, Release, ...

	Dialog: Advanced Filters
		Form with fields identifier (text), Name, Created on (date)
		Button: Reset
		Button: Search

	Dialog: Row options
		Menu items: View, Edit, Clone, Delete

	Interactions
		Specification List / filter icon → Specification List / Dialog: Advanced Filters — tap filter icon
		Specification List / Dialog: Advanced Filters / Button: Reset → Specification List / Dialog: Advanced Filters — clear filter field values
		Specification List / Dialog: Advanced Filters / Button: Search → Specification List / filtered table — apply filters and close dialog
		Specification List / table row kebab → Specification List / Dialog: Row options — open row menu anchored to row
		Specification List / column header → Specification List / sorted table — sort by that column
		Specification List / search field → Specification List / filtered table — filter rows as user types

	Integration
		Specification List / Button: Create → Create Specification / General details — start create flow
		Specification List / Dialog: Row options / View → View Specification — open read-only view
		Specification List / Dialog: Row options / Edit → Edit Specification / General details — open edit wizard
		Specification List / Dialog: Row options / Clone → Create Specification / General details — open create with prefilled data
```

Wizard example:

```text
Page: Create Specification
WaveMaker page: CreateSpecification

	Source images
		figma-resources/screens/01-create-specification.png — General details, Next disabled
		figma-resources/screens/02-create-specification.png — General details, Next enabled
		figma-resources/screens/03-create-specification.png — Additional details
		figma-resources/screens/04-create-specification.png — Review
		figma-resources/screens/05-create-specification.png — Dialog: Discard message

	Layout
		Title on left: Create Spec
		Button: Discard		Wizard/Tab (General -> Additional -> Review)		Button: Next, disabled

		Step1: General Details
			...

		Dialog: Discard message
			Title: "Are you sure you want to discard?"
			Button: Yes, discard
			Button: Stay on page

	Interactions
		Create Specification / General details / required fields filled → Create Specification / General details / Button: Next enabled — validation passes
		Create Specification / General details / Toggle: Additional attributes off → Create Specification / General details / 2nd form group hidden — toggle off
		Create Specification / General details / Toggle: Additional attributes on → Create Specification / General details / 2nd form group visible — toggle on
		Create Specification / General details / Button: Discard → Create Specification / Dialog: Discard message — tap Discard
		Create Specification / Dialog: Discard message / Stay on page → Create Specification / General details — close dialog, keep editing
		Create Specification / General details / Button: Next → Create Specification / Additional details — advance when step valid
		Create Specification / Additional details / Button: Back → Create Specification / General details — return with data preserved
		Create Specification / Review / Button: Back → Create Specification / Additional details — return with data preserved

	Integration
		Create Specification / Dialog: Discard message / Yes, discard → Specification List — abandon unsaved changes
		Create Specification / Review / Button: Submit → Specification List / success toast — save and return to list
```

## Sections

| Section | Content |
|---------|---------|
| `Page:` / `WaveMaker page:` | Human page name and PascalCase WaveMaker page name (must match `build-order.md`) |
| `Source images` | Every downloaded `figma-resources/screens/*.png` for this page from `screens.json`, with a short state label (step, dialog open, disabled Next, toast, …) |
| `Layout` | Static UI — chrome, tables, forms, wizard steps (`Step1:`, `Step2:`, …), disabled/enabled states |
| `Dialog: <name>` | Popup layout (under `Layout` or as sibling blocks before `Interactions`) |
| `Interactions` | In-page behavior — each line is **Source → Destination — action** |
| `Integration` | Cross-page navigation — each line is **Source → Destination — action**; every `type: "screen"` tap from `screens.json` |

Note disabled/enabled **states** in layout lines (e.g. `Button: Next, disabled`). **Rules** for when they change go in `Interactions` as source → destination lines.

Every API tap on this page must appear in `Interactions` or `Integration` with explicit source and destination. Every PNG assigned to this page must be listed under `Source images`.
