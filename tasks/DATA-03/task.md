# DATA-03 — Net revenue SQL report

Write a single read-only SQLite query in `report.sql`. The schema is:

- `orders(id, customer_id, created_at, status)`
- `order_items(id, order_id, quantity, unit_price_cents)`
- `refunds(id, order_id, amount_cents, status)`

Return one row per UTC order month and customer for paid orders, with exact columns:

`month, customer_id, gross_cents, refund_cents, net_cents, order_count`

Rules:

- `month` is `YYYY-MM` from `orders.created_at`.
- Gross is the sum of `quantity * unit_price_cents` across paid-order items.
- Refund is the sum of only `successful` refunds for paid orders, including multiple refunds. Orders without items/refunds contribute zero to that component.
- Net is gross minus refund and may be negative.
- `order_count` counts paid orders, not joined rows.
- Include every paid-order month/customer group. Ignore non-paid orders and refunds attached to them.
- Sort by month ascending, then net descending, then customer_id ascending.

Avoid correlated assumptions that duplicate gross or order counts when an order has multiple items and refunds. Do not create/modify schema or data.

## Public test

```bash
python3 -m unittest discover -s tests -v
```

Run the visible tests with `python3 -B -m unittest discover -s tests -p 'test_*.py' -v`.
