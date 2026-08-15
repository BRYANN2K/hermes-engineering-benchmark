# LLM Engineering Benchmark — Severity-weighted score slides

Analysis date: `2026-08-15`

## Contents

- `00-overall-hook.svg`: horizontal six-route leaderboard using the same score-derived bars as the category slides.
- `01-devops` through `10-security`: severity-weighted category rankings from primary attempt 1.
- `index.html`: local viewer with previous/next controls, Arrow-key navigation, Home/End navigation, and persisted position.
- `verify-slides.py`: deterministic deck verification.
- `apply-quality-scores.py`: reproducible score-and-copy transformation used for this revision.

The deck displays all six route conditions on every slide. Every category slide contains a concise English “Covers” line for the full task family and one score note balancing the main strength against the most consequential gap. Scores are real percentages on a 0–100 scale: minor defects lose fewer points than missing core behavior or security-critical failures. The global score is the equal-weight mean of the ten categories. UI-05 is excluded for every route because its failing private return contract was absent from the public task contract. Repeat reliability remains a separate stability metric and is not blended into quality.

## Visual reference record

Both bundled files were inspected before generation:

- `references/arena-code-leaderboard.png`
- `references/arena-agent-comparison.png`

They were used only to study editorial hierarchy, spacing, chart rhythm, and footer placement. They are not embedded in any output. Arena branding, logos, the yellow accent, model logos, proprietary copy, and page chrome were not reproduced.

## Export method

Each SVG is authored at an explicit `1600 × 900` viewBox and rendered directly by the local HTML viewer. A matching `1600 × 900` PNG export is included for every slide. The deliverables have no remote fonts, images, scripts, CDNs, or network dependencies.

## Verification

Run from the project root:

```sh
python3 quality-score-slides/verify-slides.py
```

The verifier checks all 11 slides, 60 category score cells, 40 unique task IDs, score-derived bar widths, competition ranks, concise coverage and score notes, viewer navigation, optional PNG dimensions, and the absence of remote references or placeholders.
