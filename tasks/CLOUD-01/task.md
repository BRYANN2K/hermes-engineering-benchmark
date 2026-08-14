# Build a dependency-safe infrastructure change plan

Repair `plan_changes(current, desired)` in `solution.py`. Each input is `{"resources": [...]}`. A resource has exactly `id` (unique non-empty string), `kind` (`network`, `database`, or `service`), `depends_on` (unique resource IDs), and `properties` (a JSON object). References must exist within the same input; self-references and cycles are invalid.

Return action objects `{"action": ACTION, "id": ID}` only:

- Missing from current: `create`.
- Missing from desired: `delete`.
- Same in both and identical kind/properties: no action (dependency-only changes need no action).
- Changed kind, or an immutable property changed: replacement represented by `delete` then `create`. Immutable properties are `cidr` for network, `engine` for database, and `runtime` for service.
- Other property changes: `update`.

Order all deletes so current dependents are deleted before prerequisites. Then order creates and updates so desired prerequisites precede dependents. At every valid choice use lexicographically smallest ID. A replacement's delete must occur in delete phase and its create in create/update phase. Validate both complete inputs before planning and do not mutate them. CLI takes two JSON files and prints compact JSON. Standard library only.

Run the visible tests with `python3 -B -m unittest discover -s tests -p 'test_*.py' -v`.
