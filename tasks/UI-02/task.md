# UI-02 — Race-safe autocomplete controller

Complete `createAutocomplete` in `starter/autocomplete.mjs`.

The function receives `{ fetchSuggestions, view, scheduler, delay = 200 }`. `scheduler` has `setTimeout(fn, ms)` and `clearTimeout(id)`. `view` has `render(items)`, `setLoading(boolean)`, and `setError(messageOrNull)`.

`input(rawValue)` must trim the query, debounce requests, and return immediately. A new input cancels the pending timer. Empty input clears results/error/loading and performs no fetch. When the timer fires, set loading and call `fetchSuggestions(query)`.

Only the newest input may update the view, even if an older promise settles later. On newest success, render at most 8 suggestions, deduplicated by string `id` (first occurrence wins), clear error, then clear loading. On newest failure, render `[]`, set error to `"Suggestions unavailable"`, then clear loading. Settlements after `destroy()` do nothing; destroy also cancels a pending timer and clears loading.

Return `{ input, destroy }`. Do not add dependencies.

## Public test

```bash
node --test tests/autocomplete.test.mjs
```
