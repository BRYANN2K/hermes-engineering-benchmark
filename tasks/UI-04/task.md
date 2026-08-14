# UI-04 — Modal focus and dismissal manager

Complete `createModalManager` in `starter/modal.mjs`.

Inputs are `{ dialog, opener, focusables, documentLike }`. Elements expose normal event/focus methods; `focusables` is the ordered list used by the focus trap.

- Initially leave the dialog as supplied. `open()` stores `documentLike.activeElement`, unhides the dialog, sets `aria-modal="true"`, and focuses the first focusable (or the dialog when the list is empty). Calling open while already open is a no-op.
- While open, `Tab` wraps last→first and `Shift+Tab` wraps first→last, calling `preventDefault` only when wrapping. `Escape` prevents default and closes.
- A click on the backdrop closes only when `event.target === dialog`; clicks on dialog children do not.
- `close()` hides the dialog, removes `aria-modal`, and restores focus to the element active before open when it still has `isConnected !== false`; otherwise restore to `opener`. Calling close while closed is a no-op.
- Clicking `opener` opens. `destroy()` removes listeners and, if open, closes/restores focus.
- Return `{ open, close, destroy, isOpen }`, with `isOpen` a getter.

## Public test

```bash
node --test tests/modal.test.mjs
```
