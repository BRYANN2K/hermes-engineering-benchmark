# FEAT-01: Add environment placeholder expansion

Implement `expand_env(value, env)` in `env_expand.py`.

`value` must be a string and `env` a mapping with string keys and string values. Expand placeholders left-to-right:

- `${NAME}` substitutes the value, or raises `KeyError(NAME)` when absent.
- `${NAME:-fallback}` uses `fallback` only when NAME is absent or its value is empty.
- `${NAME:?message}` raises `ValueError(message)` when NAME is absent or empty; an empty message uses `NAME is required`.
- `$$` emits one literal `$`. Thus `$${NAME}` emits literal `${NAME}` and is not expanded.

Names match `[A-Za-z_][A-Za-z0-9_]*`. Fallback/message text is literal (no recursive expansion) and may be empty, but may not contain `}`. Any other `$` sequence, malformed placeholder, or unterminated placeholder raises `ValueError` containing the zero-based character offset of that `$`. Expansion is one pass: substituted environment values are not re-expanded. Do not mutate `env`.

## Environment

- Python 3.13 standard library only
- No network access or third-party packages

## Public tests

Run exactly:

```bash
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
```

Make the smallest maintainable change that satisfies the contract.
