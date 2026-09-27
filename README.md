# The What-If Blueprint

**Every business process, mapped today and redesigned with agents.**

A library of **162 business processes** across three sectors. Each process has its own page with the traditional baseline, and each one will get a *What-If* agent ecosystem redesign, published process by process.

Live site: https://nikhil-kasturi.github.io/business-process-agent-frameworks/

| Sector | Categories | Processes |
|---|---|---|
| Retail | 13 | 40 |
| Financial Services | 12 | 71 |
| Life Sciences | 17 | 51 |

## What each process page covers

**Stage 1, the baseline (live for all 162):** what it does, the traditional flow (Mermaid diagram with full-screen zoom), and where it breaks.

**Stage 2, the What-If redesign (coming soon):** tools in use today, pain points in depth, today's critical user journey, the agent ecosystem, the new critical user journey, before and after, how each pain point gets solved, and business outcomes.

## Publishing a redesign

1. Copy `content/redesigns/TEMPLATE.md` to `content/redesigns/<sector>/<process>.md`, using the same file name as the process page (for example `content/redesigns/retail/product-catalog-management.md`).
2. Fill in the sections. Any section you leave out keeps showing "Coming soon".
3. Run `python3 scripts/build_site.py`, then commit and push.

The process page, its sector page and the home page counter update automatically.

## Repository layout

- `index.html`, `retail.html`, `financial.html`, `life-sciences.html` — home and sector pages (generated)
- `retail/`, `financial/`, `life-sciences/` — one page per process (generated)
- `content/` — source Markdown for each sector, and `content/redesigns/` for redesigns
- `scripts/build_site.py` — builds every page from `content/` (Python 3, no dependencies)

Diagrams render with [Mermaid](https://mermaid.js.org/). The site is static HTML on GitHub Pages.

*Illustrative reference of common industry practice. Not based on any specific company.*

## License

Content is licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). You may share and adapt it with credit to Nikhil Kasturi.
