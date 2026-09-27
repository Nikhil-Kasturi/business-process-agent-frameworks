# Business Process Agent Frameworks

A reference library of **162 traditional business process flows** across three sectors, the baseline for my *What-If Agent Ecosystem Design* series.

| Sector | Categories | Process flows |
|---|---|---|
| Retail | 13 | 40 |
| Financial Services | 12 | 71 |
| Life Sciences | 17 | 51 |

Each process includes a two-line description, a Mermaid diagram of how it traditionally runs, and the main pain point in that flow.

## Structure

- `index.html` — overview with a card for each sector
- `retail.html`, `financial.html`, `life-sciences.html` — sector pages (search, category index, collapsible categories, diagrams)
- `content/` — the source Markdown for each sector (diagrams render directly on GitHub)

Static HTML with no build step, hosted on GitHub Pages. Diagrams render with [Mermaid](https://mermaid.js.org/).

*Illustrative reference of common industry practice. Not based on any specific company.*

## License

Content is licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). You may share and adapt it with credit to Nikhil Kasturi.

— Nikhil Kasturi
