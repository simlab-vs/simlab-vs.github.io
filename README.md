# SIMLab Website

The website at [simlab-vs.github.io](https://simlab-vs.github.io) showcases SIMLab's
research projects and team. It is built from plain Markdown files — no web skills needed
to keep it up to date.

## What you can do

- **Add or update a project** — edit a file in `data/projects/`
- **Add or update a team member** — edit a file in `data/team/`
- **Change the site layout or style** — edit `index.html` and `build.py`

All content lives in the `data/` directory as simple text files. If you can write an
email, you can edit this website.

## How it works

```
data/projects/*.md  ─┐
data/team/*.md      ─┤──► build.py ──► index.html ──► GitHub Pages
index.html          ─┘
```

`build.py` parses the Markdown files and injects the generated HTML into `index.html`.
GitHub Pages then serves `index.html` directly from the `main` branch.

---

## Editing content

### Projects — `data/projects/`

Each file in `data/projects/` describes one project. Create a new `.md` file or edit an
existing one. The format is a `## Title` heading, optional `key: value` fields, and a
free-form description:

```markdown
## Project Title
funding: Horizon          # Horizon | SNSF | Innosuisse | HES-SO (or any string)
period:  2024–2027
partners: EPFL, WSL
website: https://example.com
github:  https://github.com/simlab-vs/my-project
status:  ongoing          # ongoing | completed

One or more sentences describing the project. Wrap long lines freely —
the script joins them into a single paragraph.
```

All fields are optional. Only the `## Title` is required.

**Funding badge colours**

| Value      | Badge colour |
|------------|-------------|
| Horizon    | Blue        |
| SNSF       | Green       |
| Innosuisse | Amber       |
| HES-SO     | Purple      |
| other      | Grey        |

---

### Team members — `data/team/`

Each file in `data/team/` describes one person. Name files with a numeric prefix to
control the display order (e.g. `01-jane-doe.md`):

```markdown
## Full Name
role:        Director
title:       Prof. Dr.
affiliation: HES-SO
website:     https://example.com
email:       name@example.com   # used for Gravatar avatar, not shown publicly
interests:   Machine Learning, Control Systems

One or two sentences of bio.
```

The `email` field drives the profile photo via [Gravatar](https://gravatar.com). If no
email is set, a placeholder avatar is shown.

---

## Publishing your changes

You don't need to build anything locally. Just edit the files, open a pull request, and
CI will rebuild `index.html` automatically.

**Step-by-step:**

1. Edit or create files under `data/`.
2. Commit and push your branch.
3. Open a pull request — CI rebuilds `index.html` and commits it to your branch.
4. Merge once the preview looks good.

```bash
# Example: add yourself to the team
git checkout -b add-jane-doe
# … edit data/team/08-jane-doe.md …
git add data/team/08-jane-doe.md
git commit -m "feat(team): add Jane Doe"
git push origin add-jane-doe
# then open a pull request on GitHub
```

---

## Rebuilding locally (optional)

Requires [uv](https://docs.astral.sh/uv/). No other dependencies.

```bash
# First time: create the virtual environment
uv sync

# Rebuild index.html in-place
uv run build.py

# Preview without touching index.html
uv run build.py --check
```

---

## Adding a new section to the site

1. Create a `data/mysection/` directory with `.md` files using the same format.
2. Add `<!-- BEGIN:mysection -->` / `<!-- END:mysection -->` markers in `index.html`.
3. Add CSS for the new section directly in `index.html`.
4. Add a `parse_mysection` / `render_mysection` / `build_mysection_html` function trio
   in `build.py` following the existing pattern, and call `inject(text, "mysection", …)`
   in `main()`.
