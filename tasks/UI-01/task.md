# UI-01 — Accessible roving tab controller

Implement `createRovingTabs` in `starter/app.mjs`. The page supplies aligned, non-empty tab and panel arrays with at least one enabled tab; your job is the interaction controller.

## Required behavior

- On creation, activate `initialIndex` when it names an enabled tab; otherwise activate the first enabled tab.
- Exactly one enabled tab has `tabindex="0"` and `aria-selected="true"`. All others have `tabindex="-1"` and `aria-selected="false"`. Only the active tab's matching panel is visible.
- Click activates an enabled tab.
- `ArrowRight`/`ArrowLeft` move with wraparound, skipping tabs whose `disabled` property is true. `Home`/`End` move to the first/last enabled tab.
- Recognized navigation keys call `preventDefault`, focus the destination, and activate it. Other keys do nothing.
- `destroy()` removes listeners; later events must not alter state.
- Return `{ activeIndex, select, destroy }`, where `activeIndex` is a getter and `select(index)` activates an enabled in-range tab without focusing it and returns a boolean.

Do not add dependencies. Preserve the exported API.

## Public test

```bash
node --test tests/app.test.mjs
```
