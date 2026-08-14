# UI-05 — Persistent cart state for a checkout drawer

Implement `createCart({ storage, view, key = "checkout-cart" })` in `starter/cart.mjs`. Monetary values are integer cents.

Products passed to `add` have `{ id, name, priceCents, stock }`. Validate a non-empty string id/name and non-negative integer price/stock. `add(product)` adds one or increments quantity up to stock. `setQuantity(id, quantity)` accepts integer quantities: `0` removes, positive values clamp to stock; unknown ids return false. `remove(id)` returns whether it removed anything.

Persist `{ version: 1, items }` after every successful mutation. On startup, safely load that shape, discard malformed products/items, merge duplicate ids, and clamp quantities to stock. Corrupt JSON behaves as empty. Never expose mutable internal item objects.

`applyCoupon(code)` recognizes case-insensitive, trimmed `SAVE10`; it is active only while subtotal is at least 5000 cents. Unknown/blank codes clear the coupon. Shipping is 0 at subtotal >= 7500 or for an empty cart, otherwise 799. Discount is floor(subtotal * 0.10). Render on startup and every state/coupon change.

The view receives `{ items, itemCount, subtotalCents, discountCents, shippingCents, totalCents, coupon }`. Return `{ add, setQuantity, remove, applyCoupon, snapshot }`.

## Public test

```bash
node --test tests/cart.test.mjs
```
