---
name: figma-read-screens
description: >-
  Step 3 of figma-images-to-spec. Open every section PNG and extract layout
  details matched to the flow map. Use when describing Figma UI from screenshots
  before writing a module specification.
disable-model-invocation: true
---

# Read screens

Open **each** page's PNG at `figma-starter/<module>/<NN>-<slug>/figma-resources/screens/` (`01`, `02`, …). Match to a page, dialog, or wizard step from the flow map.

## Label controls

`taps[].control` uses Figma layer names (`Buttons`, `Frame 1000003098`). **Use the image** for real labels: Create, Discard, Filter, View, …

## Capture from screenshots

- Chrome: left nav, header, title position (left/right)
- Actions: buttons, search fields, filter icons
- Tables: columns, row actions, filter chips, “navigation enabled” on rows
- Forms: field labels, types (text, date), columns/groups, hidden sections
- Wizards: tab bar steps, Next/Discard state (enabled/disabled)
- Dialogs: title, fields, Reset/Search/Close

## Output (working notes)

For each **Page**, record which `figma-resources/screens/*.png` files belong to it (for `Source images` in `spec.md`).

For each **Page**, **Dialog**, and **Step**, draft layout lines for `<NN>-<slug>/spec.md` under the `Layout` section — short plain sentences, one UI element per line.

For behavior (clicks, enable/disable, navigation), note as **Source → Destination — action** for `spec.md` (`Interactions` and `Integration` sections). Do not write tasks here — task generation is core Spec Kit's job after the pipeline hands off.

## Done when

- Every PNG is matched to a page (for `Source images`) and to a flow-map location (page, dialog, or step)
- Layout notes cover all visible UI for each page and dialog
- Navigation notes use source → destination form

Next: [write-spec](../write-spec/SKILL.md)
