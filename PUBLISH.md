# Publishing the SIMLab Website

The website at [simlab-vs.github.io](https://simlab-vs.github.io) is generated from
two plain-text Markdown files and a Python build script. No build tools, no
dependencies, no framework.

## How it works

```
data/projects.md        ─┐
data/collaborators.md   ─┤──► build.py ──► index.html ──► GitHub Pages
index.html (template)   ─┘
```

`build.py` parses the Markdown files and injects the generated HTML between
marker comments in `index.html`. GitHub Pages then serves `index.html` directly
from the `main` branch.

## Editing content

### Projects — `data/projects.md`

Each project is a `## Heading` block followed by optional `key: value` fields
and a free-form description paragraph:

```markdown
## Project Title
funding: Horizon          # Horizon | SNSF | Innosuisse | HES-SO (or any string)
period:  2024–2027
partners: EPFL, WSL
github:  https://github.com/simlab-vs/my-project
status:  ongoing          # ongoing | completed

One or more sentences describing the project. Wrap long lines freely —
the script joins them into a single paragraph.
```

All fields are optional. Only the `## Title` is required.

### Collaborators — `data/collaborators.md`

```markdown
## Full Name
title:       Associate Professor
affiliation: EPFL
website:     https://example.com
email:       name@example.com   # optional, not displayed publicly

One or two sentences of bio.
```

### Funding badge colours

| Value      | Badge colour |
|------------|-------------|
| Horizon    | Blue        |
| SNSF       | Green       |
| Innosuisse | Amber       |
| HES-SO     | Purple      |
| other      | Grey        |

## Rebuilding locally

Requires [uv](https://docs.astral.sh/uv/). No other dependencies.

```bash
# First time: create the virtual environment
uv sync

# Rebuild index.html in-place
uv run build.py

# Preview generated HTML without touching index.html
uv run build.py --check

# Use a different data directory or output file
uv run build.py --data path/to/data --output path/to/index.html
```

## Publishing

### Automatic (recommended)

Push any change to `data/projects.md` or `data/collaborators.md` on the `main`
branch. The CI pipeline (`.github/workflows/build.yml`) will:

1. Run `build.py` to regenerate `index.html`.
2. Commit the updated file back to `main` (commit message: `chore: rebuild site`).
3. GitHub Pages picks up the new `main` and redeploys automatically.

The whole process takes about 60–90 seconds from push to live.

### Manual

```bash
python build.py
git add index.html
git commit -m "chore: rebuild site"
git push
```

## Adding a new section to the site

1. Create `data/mysection.md` with the same `## heading` + fields + body format.
2. Add `<!-- BEGIN:mysection -->` / `<!-- END:mysection -->` markers in
   `index.html` where the section should appear.
3. Add CSS for the new section directly in `index.html`.
4. Add a `parse_mysection` / `render_mysection` / `build_mysection_html`
   function trio in `build.py` following the existing pattern, and call
   `inject(text, "mysection", ...)` in `main()`.
