"""Build The What-If Blueprint static site.

Reads the sector Markdown in content/ (and any redesigns in content/redesigns/)
and writes the HTML pages to the repository root for GitHub Pages.

    python3 scripts/build_site.py
"""
import html
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_sectors import parse_file, count_leaves  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")
REDESIGNS = os.path.join(CONTENT, "redesigns")
VER = time.strftime("%Y%m%d%H%M")

SITE_NAME = "The What-If Blueprint"
AUTHOR = "Nikhil Kasturi"
TAGLINE = "Every business process, mapped today and redesigned with agents."

SECTORS = [
    {"key": "retail", "dir": "retail", "file": "retail.html", "name": "Retail", "short": "Retail",
     "source": "Retail-Sector-Deep-Dive.md",
     "kicker": "Commerce, stores & supply chain",
     "lede": "How products are catalogued, priced, stocked, sold and returned, from the e-commerce storefront to the distribution center and the store floor."},
    {"key": "financial", "dir": "financial", "file": "financial.html", "name": "Financial Services", "short": "Financial",
     "source": "Financial-Sector-Deep-Dive.md",
     "kicker": "Banking, markets & back office",
     "lede": "How money is lent, invested, insured, moved and reconciled, from retail banking and capital markets to the corporate finance back office."},
    {"key": "lifesciences", "dir": "life-sciences", "file": "life-sciences.html", "name": "Life Sciences", "short": "Life Sciences",
     "source": "Life-Sciences-Sector-Deep-Dive.md",
     "kicker": "Discovery, trials & commercialization",
     "lede": "How therapies, devices and diagnostics move from the lab bench through trials, regulators, manufacturing and into patients' hands."},
]

# Sections of a process page. Baseline sections come from the sector Markdown;
# redesign sections come from content/redesigns/<sector-dir>/<process-slug>.md.
BASELINE_SECTIONS = [
    ("overview", "What it does"),
    ("flow", "The traditional flow"),
    ("breaks", "Where it breaks"),
]
REDESIGN_SECTIONS = [
    ("tools", "Tools in use today",
     "The systems, spreadsheets and handoffs this process relies on in a typical organization."),
    ("pains", "Pain points in depth",
     "Each pain point broken down: where it happens, who feels it, and what it costs in time, errors or risk."),
    ("cuj-today", "Today's critical user journey",
     "Who touches the process, in what order, and where delays and errors creep in."),
    ("ecosystem", "The What-If agent ecosystem",
     "A named roster of agents, each with one responsibility, plus the orchestration diagram and the human checkpoints."),
    ("cuj-new", "The new critical user journey",
     "The same journey redesigned around the agents: what changes for each person and where they still step in."),
    ("compare", "Before and after",
     "A side-by-side comparison of the traditional flow and the agentic redesign."),
    ("solved", "How each pain point gets solved",
     "Every pain point mapped to the agent or checkpoint that removes it."),
    ("outcomes", "Business outcomes",
     "The generic business outcomes this redesign could drive. Any figures are illustrative estimates, never measured results."),
]

ICONS = {
    "retail": '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 16h28l-2.5 24h-23z"/><path d="M18 16v-3a6 6 0 0 1 12 0v3"/><path d="M18 23h12"/></svg>',
    "financial": '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 18 24 8l18 10"/><path d="M9 18h30"/><path d="M12 22v12M20 22v12M28 22v12M36 22v12"/><path d="M7 38h34"/></svg>',
    "lifesciences": '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M16 6c0 12 16 12 16 24s-16 12-16 12"/><path d="M32 6c0 12-16 12-16 24s16 12 16 12"/><path d="M18 13h12M18 35h12M20 24h8"/></svg>',
}

ZOOM_ICON = '<svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M7 1h4v4M5 11H1V7M11 1 7 5M1 11l4-4"/></svg>'


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def e(s):
    return html.escape(s or "", quote=True)


def step_count(mermaid):
    return len(set(re.findall(r"\b([A-Z][A-Za-z0-9]*)\s*[\[\{\(]", mermaid or "")))


def cap(s):
    s = s or ""
    return s[:1].upper() + s[1:]


def href(prefix, target, anchor=""):
    """Internal link with a build version so browsers never reuse a stale page."""
    if target == "index.html":
        return (prefix or "./") + "?v=" + VER + anchor
    return prefix + target + "?v=" + VER + anchor


# ---------------------------------------------------------------- styles
CSS = r"""
:root{
  --bg:#FAF9F5; --surface:#FFFFFF; --surface-2:#E4EEE8; --ink:#13241D; --ink-soft:#4A5C53; --line:#E6DFD8;
  --accent:#1E7A57; --accent-2:#2E7D5E; --mint:#A8C5B4; --gold:#C8A45D; --on-accent:#FAF9F5;
  --band-bg:#0F3B2E; --band-ink:#FAF9F5; --band-soft:#C8A45D;
  --pain-bg:#F5ECD6; --pain-label:#8A6A2B; --pill-bg:#E4EEE8; --pill-ink:#0F3B2E; --focus:#1E7A57;
  --soon-bg:#F4F1EA; --soon-ink:#6B6250;
  --shadow:0 1px 0 rgba(15,59,46,.05),0 14px 32px -20px rgba(15,59,46,.45);
  --display:"Trebuchet MS", "Lucida Grande", "Lucida Sans Unicode", "Segoe UI", sans-serif;
  --body:"Trebuchet MS", "Lucida Grande", "Lucida Sans Unicode", "Segoe UI", sans-serif;
  --mono:"Trebuchet MS", "Lucida Grande", "Segoe UI", sans-serif;
  color-scheme: light;
}
:root[data-theme="dark"]{
  --bg:#0C1712; --surface:#12211A; --surface-2:#1A2E25; --ink:#EEF1EA; --ink-soft:#A9BDB2; --line:#24392F;
  --accent:#5FBF94; --accent-2:#8FCDB0; --mint:#A8C5B4; --gold:#C8A45D; --on-accent:#0C1712;
  --band-bg:#0F3B2E; --band-ink:#FAF9F5; --band-soft:#C8A45D;
  --pain-bg:#2A2616; --pain-label:#D9B870; --pill-bg:#1A2E25; --pill-ink:#CFE3D8; --focus:#8FCDB0;
  --soon-bg:#15201A; --soon-ink:#A9BDB2;
  --shadow:0 1px 0 rgba(0,0,0,.25),0 14px 32px -18px rgba(0,0,0,.75);
  color-scheme: dark;
}
*{box-sizing:border-box}
[hidden]{display:none!important}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--body);font-size:16px;line-height:1.6}
a{color:inherit}
:focus-visible{outline:2px solid var(--focus);outline-offset:3px;border-radius:4px}
.wrap{max-width:1120px;margin:0 auto;padding-inline:clamp(16px,4vw,40px)}
h1,h2,h3{text-wrap:balance}
.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}

/* top bar */
.topbar{position:sticky;top:env(safe-area-inset-top,0px);z-index:20;background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.topbar .wrap{display:flex;align-items:center;justify-content:space-between;gap:16px;min-height:60px;flex-wrap:wrap;padding-block:8px}
.brand{display:flex;align-items:baseline;gap:10px;text-decoration:none}
.brand b{font-family:var(--display);font-weight:700;font-size:1.2rem;letter-spacing:-.01em;color:var(--ink)}
.brand b i{font-style:italic;color:var(--accent)}
.brand span{font-family:var(--mono);font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-soft)}
.topbar-right{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.nav{display:flex;gap:4px;flex-wrap:wrap}
.nav a{font-size:.86rem;font-weight:600;text-decoration:none;padding:6px 12px;border-radius:999px;color:var(--ink-soft)}
.nav a:hover{color:var(--ink);background:var(--surface-2)}
.nav a[aria-current="page"]{background:var(--accent);color:var(--on-accent)}
.theme-toggle{display:inline-flex;align-items:center;gap:6px;font:inherit;font-size:.84rem;font-weight:700;color:var(--ink);background:var(--surface);border:1px solid var(--line);border-radius:999px;padding:6px 12px;cursor:pointer}
.theme-toggle:hover{border-color:var(--accent);color:var(--accent)}
.theme-toggle svg{width:15px;height:15px}
.theme-toggle .i-sun{display:none}
:root[data-theme="dark"] .theme-toggle .i-sun{display:block}
:root[data-theme="dark"] .theme-toggle .i-moon{display:none}

/* home */
.home-hero{padding-block:clamp(48px,9vw,104px) clamp(28px,5vw,48px)}
.eyebrow{font-family:var(--mono);font-size:.74rem;letter-spacing:.16em;text-transform:uppercase;color:var(--accent-2);margin:0 0 18px}
.home-hero h1{font-family:var(--display);font-weight:700;font-size:clamp(2.3rem,5.6vw,4.2rem);line-height:1.08;margin:0;max-width:19ch;letter-spacing:-.025em}
.home-hero h1 em{font-style:italic;color:var(--accent);text-decoration:underline;text-decoration-color:var(--gold);text-decoration-thickness:.08em;text-underline-offset:.12em}
.home-hero p.lede{max-width:60ch;font-size:clamp(1.02rem,1.6vw,1.15rem);color:var(--ink-soft);margin:24px 0 0}
.totals{display:flex;flex-wrap:wrap;gap:clamp(20px,5vw,56px);margin-top:36px;padding-top:24px;border-top:1px solid var(--line)}
.totals div{display:flex;flex-direction:column}
.totals strong{font-family:var(--display);font-weight:700;letter-spacing:-.02em;font-size:2.4rem;line-height:1;font-variant-numeric:tabular-nums}
.totals strong small{font-size:1.1rem;color:var(--ink-soft);font-weight:400}
.totals span{font-family:var(--mono);font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-soft);margin-top:6px}

.sector-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px;padding-block:8px 64px}
@media (max-width:900px){.sector-grid{grid-template-columns:1fr}}
.sector-card{position:relative;display:flex;flex-direction:column;gap:18px;text-decoration:none;background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:26px 24px 22px;box-shadow:var(--shadow);transition:transform .25s ease,border-color .25s ease}
.sector-card:hover{transform:translateY(-4px);border-color:var(--accent-2)}
.sector-card .icon{width:52px;height:52px;border-radius:14px;display:grid;place-items:center;background:var(--band-bg);color:var(--gold)}
.sector-card .icon svg{width:30px;height:30px}
.sector-card .kick{font-family:var(--mono);font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-soft)}
.sector-card h2{font-family:var(--display);font-weight:700;letter-spacing:-.02em;font-size:2.1rem;line-height:1.05;margin:4px 0 0}
.sector-card p{margin:0;color:var(--ink-soft);font-size:.95rem}
.stats{display:flex;gap:18px;flex-wrap:wrap;font-family:var(--mono);font-size:.78rem;color:var(--ink);font-variant-numeric:tabular-nums}
.stats b{font-weight:700;font-size:1.05rem}
.cat-preview{list-style:none;margin:0;padding:14px 0 0;border-top:1px dashed var(--line);display:flex;flex-direction:column;gap:6px;font-size:.88rem;color:var(--ink-soft)}
.cat-preview li::before{content:"";display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--mint);margin-right:10px;vertical-align:middle}
.cat-preview li.more{font-style:italic}
.cat-preview li.more::before{display:none}
.card-cta{margin-top:auto;display:flex;justify-content:space-between;align-items:center;font-weight:700;font-size:.92rem;color:var(--accent);padding-top:6px}
.card-cta .arrow{transition:transform .25s ease}
.sector-card:hover .arrow{transform:translateX(5px)}

.stages{padding-block:0 72px}
.stages > h2{font-family:var(--display);font-weight:700;letter-spacing:-.02em;font-size:clamp(1.8rem,3.5vw,2.4rem);margin:0 0 8px}
.stages > p{margin:0 0 24px;color:var(--ink-soft);max-width:62ch}
.stage-grid{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:20px}
@media (max-width:860px){.stage-grid{grid-template-columns:1fr}}
.stage{border:1px solid var(--line);border-radius:16px;background:var(--surface);padding:22px 24px}
.stage.soon{background:var(--soon-bg);border-style:dashed}
.stage-head{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:14px}
.stage-head h3{margin:0;font-size:1.2rem}
.stage ol{margin:0;padding-left:1.3em;display:flex;flex-direction:column;gap:10px}
.stage li b{display:block;font-size:.97rem}
.stage li span{color:var(--ink-soft);font-size:.9rem}

/* status pills */
.state{display:inline-flex;align-items:center;gap:6px;font-size:.72rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:3px 10px;border-radius:999px;white-space:nowrap}
.state::before{content:"";width:7px;height:7px;border-radius:50%}
.state.live{background:var(--pill-bg);color:var(--pill-ink)}
.state.live::before{background:var(--accent)}
.state.soon{background:transparent;color:var(--soon-ink);border:1px dashed var(--line)}
.state.soon::before{border:1.5px solid var(--gold)}
.state.done{background:var(--pain-bg);color:var(--pain-label)}
.state.done::before{background:var(--gold)}

/* band (sector + process) */
.band{background:var(--band-bg);color:var(--band-ink);border-bottom:3px solid var(--gold)}
.band .wrap{padding-block:clamp(40px,7vw,80px) clamp(32px,5vw,56px)}
.crumbs{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;font-family:var(--mono);font-size:.74rem;letter-spacing:.14em;text-transform:uppercase;color:var(--band-soft)}
.crumbs a{color:var(--band-soft);text-decoration:none}
.crumbs a:hover{text-decoration:underline}
.crumbs .sep{opacity:.6}
.band h1{font-family:var(--display);font-weight:700;letter-spacing:-.02em;font-size:clamp(2.3rem,6vw,4rem);line-height:1.04;margin:14px 0 0}
.band.proc-band h1{font-size:clamp(2rem,5vw,3.3rem);max-width:22ch}
.band p{max-width:62ch;margin:18px 0 0;color:color-mix(in srgb,var(--band-ink) 82%,transparent);font-size:1.05rem}
.band .stats{margin-top:26px;color:var(--band-ink);gap:28px}
.band .stats span{color:var(--band-soft)}
.band .meta{margin-top:22px}
.band .pill{background:color-mix(in srgb,var(--band-ink) 14%,transparent);color:var(--band-ink)}
.band .steps{color:var(--band-soft)}
.band .state.live{background:color-mix(in srgb,var(--band-ink) 14%,transparent);color:var(--band-ink)}
.band .state.live::before{background:var(--mint)}
.band .state.soon{color:var(--band-soft);border-color:color-mix(in srgb,var(--band-soft) 60%,transparent)}

/* sector page */
.tools{position:sticky;top:calc(env(safe-area-inset-top,0px) + 61px);z-index:10;background:var(--bg);border-bottom:1px solid var(--line)}
.tools .wrap{display:flex;flex-direction:column;gap:10px;padding-block:14px}
.search{position:relative;max-width:420px}
.search input{width:100%;font:inherit;font-size:.95rem;color:var(--ink);background:var(--surface);border:1px solid var(--line);border-radius:999px;padding:9px 16px 9px 38px}
.search input::placeholder{color:var(--ink-soft)}
.search svg{position:absolute;left:13px;top:50%;transform:translateY(-50%);width:16px;height:16px;color:var(--ink-soft)}
.chips{display:flex;gap:8px;overflow-x:auto;padding-bottom:4px;scrollbar-width:thin}
.chips a{flex:0 0 auto;font-size:.8rem;font-weight:600;text-decoration:none;padding:5px 12px;border:1px solid var(--line);border-radius:999px;color:var(--ink-soft);background:var(--surface);white-space:nowrap}
.chips a:hover{border-color:var(--accent-2);color:var(--ink)}
.chips a .n{font-family:var(--mono);font-weight:400;margin-left:6px;color:var(--accent-2)}
.result-note{font-size:.85rem;color:var(--ink-soft);margin:0}
.cats{display:flex;flex-direction:column;gap:14px;padding-block:28px 40px}
details.cat{border:1px solid var(--line);border-radius:16px;background:var(--surface);scroll-margin-top:190px}
details.cat > summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:16px;padding:18px 22px}
details.cat > summary::-webkit-details-marker{display:none}
.cat-title{font-family:var(--display);font-weight:700;letter-spacing:-.02em;font-size:clamp(1.35rem,2.6vw,1.75rem);line-height:1.15;flex:1;min-width:0}
.count{font-family:var(--mono);font-size:.76rem;color:var(--ink-soft);white-space:nowrap}
.chev{width:30px;height:30px;flex:0 0 30px;border-radius:50%;display:grid;place-items:center;background:var(--surface-2);color:var(--ink);transition:transform .25s ease}
details[open] > summary .chev{transform:rotate(180deg)}
.cat-body{padding:4px 22px 22px;display:flex;flex-direction:column;gap:18px}
.group{display:flex;flex-direction:column;gap:18px}
.group-label{font-family:var(--mono);font-size:.74rem;letter-spacing:.14em;text-transform:uppercase;color:var(--accent-2);margin:10px 0 -4px;padding-top:12px;border-top:1px dashed var(--line)}
.group:first-child .group-label{border-top:0;padding-top:0}
.proc{display:grid;grid-template-columns:minmax(0,4fr) minmax(0,8fr);gap:22px;padding:20px;border-radius:12px;background:var(--bg);border:1px solid color-mix(in srgb,var(--line) 60%,transparent);scroll-margin-top:190px}
@media (max-width:820px){.proc{grid-template-columns:1fr}}
.proc-head{display:flex;flex-direction:column;gap:10px}
.proc h3{font-size:1.12rem;font-weight:700;margin:0;line-height:1.3}
.proc h3 a{text-decoration:none}
.proc h3 a:hover{color:var(--accent);text-decoration:underline;text-decoration-color:var(--gold)}
.meta{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.steps{font-family:var(--mono);font-size:.72rem;letter-spacing:.06em;color:var(--ink-soft)}
.pill{font-size:.72rem;font-weight:600;padding:2px 10px;border-radius:999px;background:var(--pill-bg);color:var(--pill-ink)}
.proc p.desc{margin:0;color:var(--ink-soft);font-size:.94rem;max-width:60ch}
.pain{margin:0;padding:12px 14px;border-radius:10px;background:var(--pain-bg);font-size:.9rem;line-height:1.5}
.pain b{display:block;font-family:var(--mono);font-weight:700;font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;color:var(--pain-label);margin-bottom:4px}
.open-proc{margin-top:auto;display:inline-flex;align-items:center;gap:8px;align-self:flex-start;font-weight:700;font-size:.88rem;color:var(--accent);text-decoration:none;padding:7px 14px;border:1px solid var(--accent);border-radius:999px}
.open-proc:hover{background:var(--accent);color:var(--on-accent)}

/* diagrams + zoom */
.diagram{position:relative;overflow-x:auto;border-radius:10px;background:var(--surface);border:1px solid color-mix(in srgb,var(--line) 70%,transparent);padding:14px;min-height:120px;display:flex;align-items:center;justify-content:center}
.diagram pre.mermaid{margin:0;background:transparent;font-family:var(--body);font-size:.8rem;color:var(--ink-soft);white-space:pre-wrap}
.diagram pre.mermaid:not([data-processed]){opacity:.5}
.diagram svg{max-width:100%;height:auto}
.diagram:has(svg){cursor:zoom-in}
.zoom-btn{position:absolute;top:8px;right:8px;display:inline-flex;align-items:center;gap:6px;font:inherit;font-size:.76rem;font-weight:700;color:var(--accent);background:var(--surface);border:1px solid var(--line);border-radius:999px;padding:4px 10px;cursor:pointer;opacity:.9;transition:border-color .2s ease,opacity .2s ease}
.zoom-btn svg{width:12px;height:12px}
.diagram:hover .zoom-btn,.zoom-btn:focus-visible{opacity:1;border-color:var(--accent)}
.lightbox{position:fixed;inset:0;z-index:100;display:flex;padding:calc(env(safe-area-inset-top,0px) + 16px) 16px calc(env(safe-area-inset-bottom,0px) + 16px);background:color-mix(in srgb,#06140F 62%,transparent);backdrop-filter:blur(4px);-webkit-backdrop-filter:blur(4px)}
.lb-panel{margin:auto;width:min(1280px,100%);height:100%;max-height:900px;display:flex;flex-direction:column;background:var(--surface);border:1px solid var(--line);border-radius:16px;overflow:hidden;box-shadow:0 30px 80px -30px rgba(0,0,0,.6)}
.lb-bar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:10px 14px;border-bottom:1px solid var(--line)}
.lb-title{flex:1 1 200px;min-width:0;font-weight:700;font-size:1rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.lb-tools{display:flex;align-items:center;gap:6px}
.lb-bar button{font:inherit;font-size:.86rem;font-weight:700;min-width:36px;height:36px;padding:0 12px;border-radius:999px;border:1px solid var(--line);background:var(--bg);color:var(--ink);cursor:pointer}
.lb-bar button:hover{border-color:var(--accent);color:var(--accent)}
.lb-bar button.lb-close{background:var(--accent);border-color:var(--accent);color:var(--on-accent)}
.lb-pct{min-width:52px;text-align:center;font-size:.82rem;color:var(--ink-soft);font-variant-numeric:tabular-nums}
.lb-view{position:relative;flex:1;overflow:hidden;background:var(--bg);cursor:grab;touch-action:none}
.lb-view.dragging{cursor:grabbing}
.lb-stage{position:absolute;left:0;top:0;transform-origin:0 0}
.lb-stage svg{display:block;max-width:none!important}
.lb-hint{padding:8px 14px;border-top:1px solid var(--line);font-size:.78rem;color:var(--ink-soft)}
@media (max-width:600px){.lb-hint{display:none}.lightbox{padding-inline:8px}}

/* process page */
.proc-layout{display:grid;grid-template-columns:230px minmax(0,1fr);gap:40px;padding-block:36px 24px}
@media (max-width:900px){.proc-layout{grid-template-columns:1fr;gap:20px}}
.toc{position:sticky;top:calc(env(safe-area-inset-top,0px) + 80px);align-self:start}
.toc h2{font-family:var(--mono);font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-soft);margin:0 0 10px}
.toc ol{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:2px;border-left:1px solid var(--line)}
.toc a{display:flex;align-items:center;gap:10px;padding:5px 0 5px 14px;margin-left:-1px;border-left:2px solid transparent;font-size:.86rem;text-decoration:none;color:var(--ink-soft)}
.toc a:hover{color:var(--ink);border-left-color:var(--mint)}
.toc a::before{content:"";flex:0 0 8px;height:8px;border-radius:50%;background:var(--accent)}
.toc a.soon::before{background:transparent;border:1.5px solid var(--gold)}
.toc .divider{font-family:var(--mono);font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-soft);padding:12px 0 4px 14px}
@media (max-width:900px){.toc{position:static}.toc ol{flex-direction:row;flex-wrap:wrap;border-left:0;gap:6px}.toc a{border:1px solid var(--line);border-radius:999px;padding:4px 12px;margin:0}.toc .divider{width:100%;padding:8px 0 0}}
.secs{display:flex;flex-direction:column;gap:18px;min-width:0}
.sec{scroll-margin-top:90px;border:1px solid var(--line);border-radius:16px;background:var(--surface);padding:22px 24px}
.sec.soon{background:var(--soon-bg);border-style:dashed}
.sec-head{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:12px}
.sec-num{font-family:var(--mono);font-size:.78rem;font-weight:700;color:var(--gold);font-variant-numeric:tabular-nums}
.sec-head h2{flex:1;margin:0;font-size:1.3rem;letter-spacing:-.01em}
.sec p{margin:0 0 12px;max-width:68ch}
.sec p:last-child{margin-bottom:0}
.sec .lead{font-size:1.05rem}
.sec.soon .soon-note{color:var(--soon-ink);font-size:.95rem}
.phase{font-family:var(--mono);font-size:.74rem;letter-spacing:.14em;text-transform:uppercase;color:var(--accent-2);margin:14px 0 -4px;display:flex;align-items:center;gap:12px}
.phase::after{content:"";flex:1;height:1px;background:var(--line)}
.md ul,.md ol{margin:0 0 12px;padding-left:1.3em}
.md li{margin:4px 0}
.md h3{font-size:1.02rem;margin:16px 0 6px}
.md code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.88em;background:var(--pill-bg);padding:1px 5px;border-radius:5px}
.md .table-wrap{overflow-x:auto;margin:0 0 12px}
.md table{border-collapse:collapse;width:100%;font-size:.92rem}
.md th,.md td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
.md th{font-size:.78rem;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-soft)}
.md .diagram{margin:0 0 12px}

.pager{display:grid;grid-template-columns:1fr 1fr;gap:16px;padding-block:8px 64px}
@media (max-width:640px){.pager{grid-template-columns:1fr}}
.pager a{display:flex;flex-direction:column;gap:4px;text-decoration:none;padding:20px 22px;border:1px solid var(--line);border-radius:14px;background:var(--surface);transition:border-color .2s ease}
.pager a:hover{border-color:var(--accent-2)}
.pager a.next{text-align:right;background:var(--accent);color:var(--on-accent);border-color:var(--accent)}
.pager small{font-family:var(--mono);font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;opacity:.8}
.pager span{font-family:var(--display);font-size:1.4rem;line-height:1.15;font-weight:700;letter-spacing:-.01em}
.pager .spacer{visibility:hidden}

footer.site{border-top:1px solid var(--line)}
footer.site .wrap{display:flex;flex-wrap:wrap;justify-content:space-between;gap:12px;padding-block:24px;font-size:.84rem;color:var(--ink-soft)}
@media (max-width:700px){.tools{position:static}.nav{flex-wrap:nowrap;overflow-x:auto;max-width:100%}.nav a{white-space:nowrap}details.cat,.proc{scroll-margin-top:130px}}
@media (prefers-reduced-motion: reduce){*{transition:none!important;scroll-behavior:auto!important}}
"""

# ---------------------------------------------------------------- scripts
HEAD_JS = "<script>try{if(localStorage.getItem('pf-theme')==='dark')document.documentElement.setAttribute('data-theme','dark');}catch(e){}</script>"

THEME_JS = r"""
(function(){
  var root=document.documentElement, btn=document.getElementById('theme-toggle'); if(!btn) return;
  var label=btn.querySelector('.theme-label');
  function sync(){ var dark=root.getAttribute('data-theme')==='dark';
    btn.setAttribute('aria-pressed', dark?'true':'false'); label.textContent = dark?'Light':'Dark';
    btn.setAttribute('aria-label', dark?'Switch to light mode':'Switch to dark mode'); }
  btn.addEventListener('click', function(){
    var dark = root.getAttribute('data-theme')!=='dark';
    root.setAttribute('data-theme', dark?'dark':'light');
    try{ localStorage.setItem('pf-theme', dark?'dark':'light'); }catch(e){}
    sync(); document.dispatchEvent(new CustomEvent('pf-themechange'));
  });
  sync();
})();
"""

MERMAID_SRC = '<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>'

MERMAID_JS = r"""
(function(){
  function tok(n){return getComputedStyle(document.documentElement).getPropertyValue(n).trim();}
  var ready = false;
  function init(){
    if(!window.mermaid) return false;
    window.mermaid.initialize({
      startOnLoad:false, securityLevel:'strict', theme:'base',
      flowchart:{curve:'basis', useMaxWidth:true, htmlLabels:true, nodeSpacing:22, rankSpacing:28, padding:10},
      themeVariables:{
        fontFamily:'Trebuchet MS, Lucida Grande, Segoe UI, sans-serif', fontSize:'15px',
        primaryColor:tok('--pill-bg'), primaryTextColor:tok('--ink'), primaryBorderColor:tok('--accent'),
        lineColor:tok('--mint'), secondaryColor:tok('--pain-bg'), tertiaryColor:tok('--surface'),
        edgeLabelBackground:tok('--surface'), clusterBkg:tok('--surface')
      }
    });
    ready = true; return true;
  }
  function render(scope){
    if(!scope) return;
    if(!ready && !init()) return;
    var nodes = Array.prototype.slice.call(scope.querySelectorAll('pre.mermaid:not([data-processed])'));
    if(nodes.length) window.mermaid.run({nodes:nodes}).catch(function(){});
  }
  function renderVisible(){
    document.querySelectorAll('details.cat[open], .proc-page').forEach(render);
  }
  document.querySelectorAll('pre.mermaid').forEach(function(p){ p.setAttribute('data-src', p.textContent); });
  document.addEventListener('pf-themechange', function(){
    ready=false; init();
    document.querySelectorAll('pre.mermaid[data-processed]').forEach(function(p){
      p.removeAttribute('data-processed'); p.textContent = p.getAttribute('data-src'); });
    renderVisible();
  });
  init();
  document.addEventListener('toggle', function(ev){
    var d = ev.target; if(d && d.tagName==='DETAILS' && d.open) render(d);
  }, true);
  window.addEventListener('load', renderVisible);
})();
"""

SECTOR_JS = r"""
(function(){
  var cats = Array.prototype.slice.call(document.querySelectorAll('details.cat'));
  document.querySelectorAll('.chips a').forEach(function(a){
    a.addEventListener('click', function(){
      var t = document.getElementById(a.getAttribute('href').slice(1));
      if(t){ t.open = true; }
    });
  });
  function openFromHash(){
    var id = location.hash.slice(1); if(!id) return;
    var t = document.getElementById(id); if(!t) return;
    var d = t.tagName==='DETAILS' ? t : t.closest('details.cat');
    if(d){ d.open = true; t.scrollIntoView({block:'start'}); }
  }
  window.addEventListener('hashchange', openFromHash);
  openFromHash();
  var input = document.getElementById('proc-search');
  var note = document.getElementById('result-note');
  var initialOpen = cats.map(function(c){return c.open;});
  if(input){
    input.addEventListener('input', function(){
      var q = input.value.trim().toLowerCase(), total = 0;
      cats.forEach(function(cat, i){
        var hits = 0;
        cat.querySelectorAll('.proc').forEach(function(p){
          var m = !q || p.getAttribute('data-search').indexOf(q) !== -1;
          p.hidden = !m; if(m) hits++;
        });
        cat.querySelectorAll('.group').forEach(function(g){ g.hidden = !g.querySelector('.proc:not([hidden])'); });
        cat.hidden = q && hits === 0;
        if(q){ if(hits) cat.open = true; } else { cat.open = initialOpen[i]; }
        total += hits;
      });
      note.textContent = q ? (total + (total===1?' process matches':' processes match') + ' “' + input.value.trim() + '”') : '';
    });
  }
})();
"""

ZOOM_JS = r"""
(function(){
  var lb, view, stage, pct, titleEl, closeBtn, lastFocus;
  var s=1, x=0, y=0, w=0, h=0;
  var pointers = new Map(), pinchDist=0, dragStart=null;
  function build(){
    lb = document.createElement('div');
    lb.className='lightbox'; lb.hidden=true;
    lb.setAttribute('role','dialog'); lb.setAttribute('aria-modal','true'); lb.setAttribute('aria-label','Process diagram');
    lb.innerHTML='<div class="lb-panel"><div class="lb-bar"><span class="lb-title"></span><div class="lb-tools">'+
      '<button type="button" data-z="out" aria-label="Zoom out">&minus;</button><span class="lb-pct">100%</span>'+
      '<button type="button" data-z="in" aria-label="Zoom in">+</button>'+
      '<button type="button" data-z="fit">Fit</button>'+
      '<button type="button" class="lb-close" data-z="close">Close</button></div></div>'+
      '<div class="lb-view"><div class="lb-stage"></div></div>'+
      '<div class="lb-hint">Scroll or pinch to zoom. Drag to move. Keys: + and &minus; zoom, 0 fits, Esc closes.</div></div>';
    document.body.appendChild(lb);
    view=lb.querySelector('.lb-view'); stage=lb.querySelector('.lb-stage'); pct=lb.querySelector('.lb-pct');
    titleEl=lb.querySelector('.lb-title'); closeBtn=lb.querySelector('.lb-close');
    lb.addEventListener('click', function(ev){
      var b=ev.target.closest('[data-z]');
      if(b){ var z=b.getAttribute('data-z'); var c=center();
        if(z==='in') zoomAt(1.25,c[0],c[1]); else if(z==='out') zoomAt(0.8,c[0],c[1]); else if(z==='fit') fit(); else close();
        return; }
      if(ev.target===lb) close();
    });
    view.addEventListener('wheel', function(ev){
      ev.preventDefault(); var r=view.getBoundingClientRect();
      zoomAt(Math.exp(-ev.deltaY*0.0015), ev.clientX-r.left, ev.clientY-r.top);
    }, {passive:false});
    view.addEventListener('pointerdown', function(ev){
      view.setPointerCapture(ev.pointerId); pointers.set(ev.pointerId,{x:ev.clientX,y:ev.clientY});
      if(pointers.size===1){ dragStart={px:ev.clientX,py:ev.clientY,x:x,y:y}; view.classList.add('dragging'); }
      if(pointers.size===2){ pinchDist=dist(); dragStart=null; }
    });
    view.addEventListener('pointermove', function(ev){
      if(!pointers.has(ev.pointerId)) return;
      pointers.set(ev.pointerId,{x:ev.clientX,y:ev.clientY});
      if(pointers.size===2){
        var d=dist(), m=mid(), r=view.getBoundingClientRect();
        if(pinchDist) zoomAt(d/pinchDist, m[0]-r.left, m[1]-r.top); pinchDist=d;
      } else if(dragStart){
        x=dragStart.x+(ev.clientX-dragStart.px); y=dragStart.y+(ev.clientY-dragStart.py); apply();
      }
    });
    function end(ev){ pointers.delete(ev.pointerId); if(pointers.size<2) pinchDist=0;
      if(pointers.size===0){ dragStart=null; view.classList.remove('dragging'); }
      else if(pointers.size===1){ var p=pointers.values().next().value; dragStart={px:p.x,py:p.y,x:x,y:y}; } }
    view.addEventListener('pointerup', end); view.addEventListener('pointercancel', end);
    document.addEventListener('keydown', function(ev){
      if(lb.hidden) return; var c=center();
      if(ev.key==='Escape'){ ev.preventDefault(); close(); }
      else if(ev.key==='+'||ev.key==='='){ zoomAt(1.25,c[0],c[1]); }
      else if(ev.key==='-'||ev.key==='_'){ zoomAt(0.8,c[0],c[1]); }
      else if(ev.key==='0'){ fit(); }
      else if(ev.key==='Tab'){
        var f=lb.querySelectorAll('button'); var first=f[0], last=f[f.length-1];
        if(ev.shiftKey && document.activeElement===first){ ev.preventDefault(); last.focus(); }
        else if(!ev.shiftKey && document.activeElement===last){ ev.preventDefault(); first.focus(); }
      }
    });
    window.addEventListener('resize', function(){ if(!lb.hidden) fit(); });
  }
  function dist(){ var p=Array.from(pointers.values()); return Math.hypot(p[0].x-p[1].x,p[0].y-p[1].y); }
  function mid(){ var p=Array.from(pointers.values()); return [(p[0].x+p[1].x)/2,(p[0].y+p[1].y)/2]; }
  function center(){ return [view.clientWidth/2, view.clientHeight/2]; }
  function apply(){ stage.style.transform='translate('+x+'px,'+y+'px) scale('+s+')'; pct.textContent=Math.round(s*100)+'%'; }
  function zoomAt(f,cx,cy){ var ns=Math.min(8,Math.max(0.2,s*f)); x=cx-(cx-x)*(ns/s); y=cy-(cy-y)*(ns/s); s=ns; apply(); }
  function fit(){ var vw=view.clientWidth, vh=view.clientHeight; s=Math.min((vw-48)/w,(vh-48)/h,3); if(!(s>0)) s=1;
    x=(vw-w*s)/2; y=(vh-h*s)/2; apply(); }
  function open(diagram){
    var svg=diagram.querySelector('pre.mermaid svg'); if(!svg) return;
    if(!lb) build();
    var vb=svg.viewBox && svg.viewBox.baseVal;
    w=(vb && vb.width) || svg.getBoundingClientRect().width; h=(vb && vb.height) || svg.getBoundingClientRect().height;
    var clone=svg.cloneNode(true);
    clone.removeAttribute('style'); clone.setAttribute('width',w); clone.setAttribute('height',h);
    stage.innerHTML=''; stage.appendChild(clone);
    titleEl.textContent = diagram.getAttribute('data-title') || 'Process diagram';
    lastFocus=document.activeElement; lb.hidden=false; document.documentElement.style.overflow='hidden';
    requestAnimationFrame(fit); closeBtn.focus();
  }
  function close(){ lb.hidden=true; stage.innerHTML=''; document.documentElement.style.overflow='';
    if(lastFocus && lastFocus.focus) lastFocus.focus(); }
  document.addEventListener('click', function(ev){
    if(lb && !lb.hidden) return;
    var d=ev.target.closest('.diagram'); if(!d) return;
    if(ev.target.closest('a')) return;
    if(d.querySelector('pre.mermaid svg')) open(d);
  });
})();
"""


# ---------------------------------------------------------------- shared chrome
def topbar(active, prefix=""):
    links = ['<a href="%s"%s>Overview</a>' % (href(prefix, "index.html"), ' aria-current="page"' if active == "home" else "")]
    for s in SECTORS:
        cur = ' aria-current="page"' if active == s["key"] else ""
        links.append('<a href="%s"%s>%s</a>' % (href(prefix, s["file"]), cur, s["short"]))
    return ('<header class="topbar"><div class="wrap">'
            '<a class="brand" href="%s"><b>The <i>What-If</i> Blueprint</b><span>by %s</span></a>'
            '<div class="topbar-right"><nav class="nav" aria-label="Sectors">%s</nav>'
            '<button class="theme-toggle" id="theme-toggle" type="button" aria-pressed="false">'
            '<svg class="i-moon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"><path d="M13.5 9.5A5.5 5.5 0 0 1 6.5 2.5a5.5 5.5 0 1 0 7 7z"/></svg>'
            '<svg class="i-sun" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><circle cx="8" cy="8" r="3"/><path d="M8 1v1.5M8 13.5V15M1 8h1.5M13.5 8H15M3 3l1 1M12 12l1 1M13 3l-1 1M4 12l-1 1"/></svg>'
            '<span class="theme-label">Dark</span></button></div></div></header>'
            ) % (href(prefix, "index.html"), e(AUTHOR), "".join(links))


def footer():
    return ('<footer class="site"><div class="wrap">'
            '<span>%s &middot; %s &middot; 2026 &middot; CC BY 4.0</span>'
            '<span>Illustrative reference of common industry practice. Not based on any specific company.</span>'
            '</div></footer>') % (e(SITE_NAME), e(AUTHOR))


def page(title, desc, body, scripts=""):
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<title>%s</title>\n<meta name="description" content="%s">\n%s\n<style>%s</style>\n</head>\n'
            '<body>\n%s\n%s<script>%s</script>\n</body>\n</html>\n'
            ) % (e(title), e(desc), HEAD_JS, CSS, body, scripts, THEME_JS)


def diagram_html(code, title):
    return ('<div class="diagram" data-title="%s"><button class="zoom-btn" type="button" '
            'aria-label="Open diagram full screen to zoom">%sExpand</button>'
            '<pre class="mermaid">%s</pre></div>') % (e(title), ZOOM_ICON, e(code))


def state(kind):
    label = {"live": "Live", "soon": "Coming soon", "done": "Redesign published"}[kind]
    return '<span class="state %s">%s</span>' % (kind, label)


# ---------------------------------------------------------------- redesign files
def inline_md(s):
    s = e(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    return s


def render_md(text, title):
    """Small Markdown renderer for redesign sections: paragraphs, ### headings,
    bullet/numbered lists, pipe tables, **bold**, *italic*, `code`, links and
    ```mermaid diagrams (rendered with zoom)."""
    out, lines, i = [], text.strip("\n").split("\n"), 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.strip().startswith("```"):
            lang = line.strip()[3:].strip()
            buf = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            code = "\n".join(buf)
            out.append(diagram_html(code, title) if lang == "mermaid" else "<pre><code>%s</code></pre>" % e(code))
            continue
        if line.startswith("### "):
            out.append("<h3>%s</h3>" % inline_md(line[4:].strip()))
            i += 1
            continue
        if line.lstrip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            if rows:
                head = "".join("<th>%s</th>" % inline_md(c) for c in rows[0])
                body = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % inline_md(c) for c in r) for r in rows[1:])
                out.append('<div class="table-wrap"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (head, body))
            continue
        m = re.match(r"\s*([-*]|\d+\.)\s+", line)
        if m:
            ordered = m.group(1)[0].isdigit()
            items = []
            while i < len(lines) and re.match(r"\s*([-*]|\d+\.)\s+", lines[i]):
                items.append(re.sub(r"\s*([-*]|\d+\.)\s+", "", lines[i], count=1))
                i += 1
            tag = "ol" if ordered else "ul"
            out.append("<%s>%s</%s>" % (tag, "".join("<li>%s</li>" % inline_md(t) for t in items), tag))
            continue
        para = []
        while (i < len(lines) and lines[i].strip() and not lines[i].strip().startswith("```")
               and not lines[i].startswith("### ") and not lines[i].lstrip().startswith("|")
               and not re.match(r"\s*([-*]|\d+\.)\s+", lines[i])):
            para.append(lines[i].strip())
            i += 1
        out.append("<p>%s</p>" % inline_md(" ".join(para)))
    return "".join(out)


SECTION_ALIASES = {
    "tools": ["tools in use today", "tools"],
    "pains": ["pain points in depth", "pain points"],
    "cuj-today": ["today's critical user journey", "todays critical user journey", "current cuj", "today's cuj", "current critical user journey"],
    "ecosystem": ["the what-if agent ecosystem", "what-if agent ecosystem", "agent ecosystem"],
    "cuj-new": ["the new critical user journey", "new critical user journey", "new cuj"],
    "compare": ["before and after", "comparison", "before vs after"],
    "solved": ["how each pain point gets solved", "how pain points get solved", "pain points solved"],
    "outcomes": ["business outcomes", "outcomes"],
}


def load_redesign(sector_dir, proc_slug):
    path = os.path.join(REDESIGNS, sector_dir, proc_slug + ".md")
    if not os.path.exists(path):
        return {}
    text = open(path, encoding="utf-8").read()
    sections, current, buf = {}, None, []
    for line in text.split("\n"):
        if line.startswith("## "):
            if current:
                sections[current] = "\n".join(buf)
            heading = line[3:].strip().lower().replace("’", "'")
            current = next((k for k, names in SECTION_ALIASES.items() if heading in names), None)
            if current is None:
                print("  ! %s: unknown section heading '%s' (see content/redesigns/TEMPLATE.md)" % (os.path.relpath(path, ROOT), line[3:].strip()))
            buf = []
        elif current:
            buf.append(line)
    if current:
        sections[current] = "\n".join(buf)
    return {k: v for k, v in sections.items() if v.strip()}


# ---------------------------------------------------------------- data
def build_index():
    """Flatten each sector into an ordered list of processes with page paths."""
    sectors = []
    for s in SECTORS:
        title, cats = parse_file(os.path.join(CONTENT, s["source"]))
        procs, seen = [], set()
        for c in cats:
            cid = "cat-" + slug(c["name"])
            c["id"] = cid
            groups = [(None, [ch]) if ch["kind"] == "leaf" else (ch["name"], ch["children"]) for ch in c["children"]]
            for group, leaves in groups:
                for leaf in leaves:
                    ps = slug(leaf["name"])
                    if ps in seen:
                        ps = slug(c["name"]) + "-" + ps
                    seen.add(ps)
                    leaf.update({"slug": ps, "category": c["name"], "cat_id": cid, "group": group,
                                 "path": "%s/%s.html" % (s["dir"], ps),
                                 "redesign": load_redesign(s["dir"], ps)})
                    procs.append(leaf)
        sectors.append(dict(s, categories=cats, procs=procs,
                            total=len(procs), cat_count=len(cats),
                            published=sum(1 for p in procs if p["redesign"])))
    return sectors


# ---------------------------------------------------------------- home
def home_page(sectors):
    total = sum(s["total"] for s in sectors)
    cats = sum(s["cat_count"] for s in sectors)
    published = sum(s["published"] for s in sectors)
    cards = []
    for s in sectors:
        names = [c["name"] for c in s["categories"]]
        items = "".join("<li>%s</li>" % e(n) for n in names[:5])
        if len(names) > 5:
            items += '<li class="more">+ %d more categories</li>' % (len(names) - 5)
        cards.append(
            '<a class="sector-card" href="%s"><div class="icon">%s</div>'
            '<div><div class="kick">%s</div><h2>%s</h2></div><p>%s</p>'
            '<div class="stats"><div><b>%d</b> categories</div><div><b>%d</b> processes</div><div><b>%d</b> redesigned</div></div>'
            '<ul class="cat-preview">%s</ul>'
            '<div class="card-cta"><span>Open %s</span><span class="arrow" aria-hidden="true">&rarr;</span></div></a>'
            % (href("", s["file"]), ICONS[s["key"]], e(s["kicker"]), e(s["name"]), e(s["lede"]),
               s["cat_count"], s["total"], s["published"], items, e(s["name"])))
    baseline = "".join('<li><b>%s</b><span>%s</span></li>' % (t, d) for t, d in [
        ("What it does", "A two-line summary of the function and why the business depends on it."),
        ("The traditional flow", "A diagram of the steps as they run today. Click it to open full screen and zoom."),
        ("Where it breaks", "The main pain point an agent ecosystem would target."),
    ])
    redesign = "".join('<li><b>%s</b><span>%s</span></li>' % (e(t), e(d)) for _, t, d in REDESIGN_SECTIONS)
    body = (topbar("home") + '<main>'
            '<section class="wrap home-hero">'
            '<p class="eyebrow">For leaders planning their next move with AI</p>'
            '<h1>See where your processes <em>break</em>, and how agents could fix them.</h1>'
            '<p class="lede">A reference of %d business processes across three sectors. Each one maps the traditional flow and its main pain point, '
            'followed by a What-If agent ecosystem: the agents, the human checkpoints, and the business outcomes it could drive.</p>'
            '<div class="totals">'
            '<div><strong>3</strong><span>Sectors</span></div>'
            '<div><strong>%d</strong><span>Categories</span></div>'
            '<div><strong>%d</strong><span>Processes mapped</span></div>'
            '<div><strong>%d<small> / %d</small></strong><span>Redesigns published</span></div>'
            '</div></section>'
            '<section class="wrap sector-grid" aria-label="Sectors">%s</section>'
            '<section class="wrap stages"><h2>What each process page covers</h2>'
            '<p>Every page is built in two stages. The baseline is live for all %d processes. The redesign sections fill in as each What-If redesign is published.</p>'
            '<div class="stage-grid">'
            '<div class="stage"><div class="stage-head"><h3>Stage 1: The baseline</h3>%s</div><ol>%s</ol></div>'
            '<div class="stage soon"><div class="stage-head"><h3>Stage 2: The What-If redesign</h3>%s</div><ol start="4">%s</ol></div>'
            '</div></section>'
            '</main>' + footer()) % (total, cats, total, published, total, "".join(cards), total,
                                     state("live"), baseline, state("soon"), redesign)
    return page(SITE_NAME, "%s %d business processes across Retail, Financial Services and Life Sciences." % (TAGLINE, total), body)


# ---------------------------------------------------------------- sector
def proc_card(s, p):
    tag = '<span class="pill">Also %s</span>' % e(p["tag"]) if p.get("tag") else ""
    search = " ".join([p["name"], p.get("tag") or "", p["desc"] or "", p["pain"] or ""]).lower()
    link = href("", p["path"])
    return ('<article class="proc" id="p-%s" data-search="%s"><div class="proc-head">'
            '<h3><a href="%s">%s</a></h3>'
            '<div class="meta"><span class="steps">%d-step flow</span>%s%s</div>'
            '<p class="desc">%s</p>'
            '<p class="pain"><b>Where it breaks</b>%s</p>'
            '<a class="open-proc" href="%s">Open process page <span aria-hidden="true">&rarr;</span></a>'
            '</div>%s</article>') % (
        p["slug"], e(search), link, e(p["name"]), step_count(p["mermaid"]), tag,
        state("done") if p["redesign"] else "",
        e(p["desc"]), e(cap(p["pain"])), link, diagram_html(p["mermaid"], p["name"]))


def sector_page(sectors, idx):
    s = sectors[idx]
    by_slug = {p["slug"]: p for p in s["procs"]}
    chips, blocks = [], []
    for i, c in enumerate(s["categories"]):
        n = count_leaves(c["children"])
        chips.append('<a href="#%s">%s<span class="n">%d</span></a>' % (c["id"], e(c["name"]), n))
        inner = []
        for ch in c["children"]:
            if ch["kind"] == "leaf":
                inner.append(proc_card(s, by_slug[ch["slug"]]))
            else:
                inner.append('<div class="group"><p class="group-label">%s</p>%s</div>'
                             % (e(ch["name"]), "".join(proc_card(s, by_slug[l["slug"]]) for l in ch["children"])))
        blocks.append('<details class="cat" id="%s"%s><summary><span class="cat-title">%s</span>'
                      '<span class="count">%d %s</span><span class="chev" aria-hidden="true">'
                      '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M3 5l4 4 4-4"/></svg>'
                      '</span></summary><div class="cat-body">%s</div></details>'
                      % (c["id"], " open" if i == 0 else "", e(c["name"]), n, "process" if n == 1 else "processes", "".join(inner)))
    prev = sectors[idx - 1] if idx > 0 else None
    nxt = sectors[idx + 1] if idx < len(sectors) - 1 else None
    prev_link = ('<a href="%s"><small>&larr; Previous sector</small><span>%s</span></a>' % (href("", prev["file"]), e(prev["name"]))
                 if prev else '<a href="%s"><small>&larr; Back</small><span>Overview</span></a>' % href("", "index.html"))
    next_link = ('<a class="next" href="%s"><small>Next sector &rarr;</small><span>%s</span></a>' % (href("", nxt["file"]), e(nxt["name"]))
                 if nxt else '<a class="next" href="%s"><small>Finished &rarr;</small><span>Back to overview</span></a>' % href("", "index.html"))
    body = (topbar(s["key"]) + '<main>'
            '<section class="band"><div class="wrap">'
            '<div class="crumbs"><a href="%s">All sectors</a></div>'
            '<h1>%s</h1><p>%s</p>'
            '<div class="stats"><div><b>%d</b> <span>categories</span></div><div><b>%d</b> <span>processes</span></div>'
            '<div><b>%d</b> <span>redesigns published</span></div></div>'
            '</div></section>'
            '<div class="tools"><div class="wrap">'
            '<label class="search" for="proc-search"><span class="sr-only">Search processes</span>'
            '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="7" cy="7" r="5"/><path d="M11 11l3.5 3.5" stroke-linecap="round"/></svg>'
            '<input id="proc-search" type="search" placeholder="Search %d processes" autocomplete="off"></label>'
            '<nav class="chips" aria-label="Categories">%s</nav>'
            '<p class="result-note" id="result-note" aria-live="polite"></p>'
            '</div></div>'
            '<div class="wrap cats">%s</div>'
            '<nav class="wrap pager" aria-label="Sector navigation">%s%s</nav>'
            '</main>' + footer()) % (
        href("", "index.html"), e(s["name"]), e(s["lede"]), s["cat_count"], s["total"], s["published"], s["total"],
        "".join(chips), "".join(blocks), prev_link, next_link)
    scripts = MERMAID_SRC + "<script>%s</script><script>%s</script><script>%s</script>" % (MERMAID_JS, SECTOR_JS, ZOOM_JS)
    return page("%s | %s" % (s["name"], SITE_NAME), s["lede"], body, scripts)


# ---------------------------------------------------------------- process
def process_page(s, i):
    p = s["procs"][i]
    pre = "../"
    red = p["redesign"]
    toc, secs = [], []
    num = 0
    for key, title in BASELINE_SECTIONS:
        num += 1
        if key == "overview":
            content = '<p class="lead">%s</p>' % e(p["desc"])
        elif key == "flow":
            content = diagram_html(p["mermaid"], p["name"])
        else:
            content = '<p class="pain"><b>Main pain point</b>%s</p>' % e(cap(p["pain"]))
        toc.append('<li><a href="#%s">%s</a></li>' % (key, e(title)))
        secs.append('<section class="sec" id="%s"><div class="sec-head"><span class="sec-num">%02d</span><h2>%s</h2>%s</div>%s</section>'
                    % (key, num, e(title), state("live"), content))
    toc.append('<li class="divider">What-If redesign</li>')
    secs.append('<p class="phase">Stage 2: The What-If redesign</p>')
    for key, title, blurb in REDESIGN_SECTIONS:
        num += 1
        if key in red:
            toc.append('<li><a href="#%s">%s</a></li>' % (key, e(title)))
            secs.append('<section class="sec md" id="%s"><div class="sec-head"><span class="sec-num">%02d</span><h2>%s</h2>%s</div>%s</section>'
                        % (key, num, e(title), state("live"), render_md(red[key], "%s: %s" % (p["name"], title))))
        else:
            toc.append('<li><a class="soon" href="#%s">%s</a></li>' % (key, e(title)))
            secs.append('<section class="sec soon" id="%s"><div class="sec-head"><span class="sec-num">%02d</span><h2>%s</h2>%s</div>'
                        '<p class="soon-note">%s</p></section>' % (key, num, e(title), state("soon"), e(blurb)))
    prev = s["procs"][i - 1] if i > 0 else None
    nxt = s["procs"][i + 1] if i < len(s["procs"]) - 1 else None
    prev_link = ('<a href="%s"><small>&larr; Previous process</small><span>%s</span></a>' % (href(pre, prev["path"]), e(prev["name"]))
                 if prev else '<a href="%s"><small>&larr; Back to</small><span>All %s processes</span></a>' % (href(pre, s["file"]), e(s["name"])))
    next_link = ('<a class="next" href="%s"><small>Next process &rarr;</small><span>%s</span></a>' % (href(pre, nxt["path"]), e(nxt["name"]))
                 if nxt else '<a class="next" href="%s"><small>Finished &rarr;</small><span>All %s processes</span></a>' % (href(pre, s["file"]), e(s["name"])))
    crumbs = ['<a href="%s">All sectors</a>' % href(pre, "index.html"),
              '<a href="%s">%s</a>' % (href(pre, s["file"]), e(s["name"])),
              '<a href="%s">%s</a>' % (href(pre, s["file"], "#" + p["cat_id"]), e(p["category"]))]
    if p["group"]:
        crumbs.append("<span>%s</span>" % e(p["group"]))
    tag = '<span class="pill">Also %s</span>' % e(p["tag"]) if p.get("tag") else ""
    body = (topbar(s["key"], pre) + '<main class="proc-page">'
            '<section class="band proc-band"><div class="wrap">'
            '<nav class="crumbs" aria-label="Breadcrumb">%s</nav>'
            '<h1>%s</h1><p>%s</p>'
            '<div class="meta">%s<span class="steps">%d-step traditional flow</span>%s</div>'
            '</div></section>'
            '<div class="wrap proc-layout">'
            '<aside class="toc"><h2>On this page</h2><ol>%s</ol></aside>'
            '<div class="secs">%s</div>'
            '</div>'
            '<nav class="wrap pager" aria-label="Process navigation">%s%s</nav>'
            '</main>' + footer()) % (
        '<span class="sep">/</span>'.join(crumbs), e(p["name"]), e(p["desc"]),
        state("done") if red else state("soon").replace("Coming soon", "Redesign coming soon"),
        step_count(p["mermaid"]), tag, "".join(toc), "".join(secs), prev_link, next_link)
    scripts = MERMAID_SRC + "<script>%s</script><script>%s</script>" % (MERMAID_JS, ZOOM_JS)
    return page("%s | %s" % (p["name"], SITE_NAME), "%s %s" % (p["desc"], TAGLINE), body, scripts)


# ---------------------------------------------------------------- write
def write(rel, text):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    sectors = build_index()
    write("index.html", home_page(sectors))
    count = 0
    for idx, s in enumerate(sectors):
        write(s["file"], sector_page(sectors, idx))
        # remove pages for processes that no longer exist
        d = os.path.join(ROOT, s["dir"])
        keep = {p["slug"] + ".html" for p in s["procs"]}
        if os.path.isdir(d):
            for fn in os.listdir(d):
                if fn.endswith(".html") and fn not in keep:
                    os.remove(os.path.join(d, fn))
        for i in range(len(s["procs"])):
            write(s["procs"][i]["path"], process_page(s, i))
            count += 1
    open(os.path.join(ROOT, ".nojekyll"), "w").close()
    total = sum(s["total"] for s in sectors)
    published = sum(s["published"] for s in sectors)
    print("Built %s: home, %d sector pages, %d process pages (%d/%d redesigns published). Version %s"
          % (SITE_NAME, len(sectors), count, published, total, VER))


if __name__ == "__main__":
    main()
