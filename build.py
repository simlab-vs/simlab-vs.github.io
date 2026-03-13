#!/usr/bin/env python3
"""
build.py – Parse data/projects.md and data/collaborators.md, generate HTML
sections, and inject them into index.html between marker comments.

Markers expected in index.html:
    <!-- BEGIN:projects -->  ...  <!-- END:projects -->
    <!-- BEGIN:collaborators -->  ...  <!-- END:collaborators -->

Usage:
    python build.py                   # reads data/, writes index.html in-place
    python build.py --check           # dry-run: print generated HTML, no write
    python build.py --data other/dir  # override data directory
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ── Data models ──────────────────────────────────────────────────────────────

@dataclass
class Project:
    title: str
    funding: str = ""
    period: str = ""
    partners: str = ""
    github: str = ""
    status: str = ""
    description: str = ""


@dataclass
class Collaborator:
    name: str
    title: str = ""
    affiliation: str = ""
    website: str = ""
    email: str = ""
    bio: str = ""


# ── Parser ───────────────────────────────────────────────────────────────────

_KNOWN_FIELDS = {"funding", "period", "partners", "github", "status",
                 "title", "affiliation", "website", "email"}

def _parse_entries(text: str) -> list[dict]:
    """
    Split markdown into entries starting at each ## heading.
    Each entry is a dict with 'heading', recognised key:value fields,
    and 'body' (remaining lines joined).
    Comment lines (<!-- ... -->) are stripped.
    """
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    entries: list[dict] = []
    current: dict | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            if current is not None:
                entries.append(current)
            current = {"heading": line[3:].strip(), "_body_lines": []}
            continue
        if current is None:
            continue  # skip lines before first entry (e.g. # title, comments)

        # Try key: value field
        m = re.match(r'^([a-zA-Z_]+)\s*:\s*(.*)$', line)
        if m and m.group(1).lower() in _KNOWN_FIELDS:
            current[m.group(1).lower()] = m.group(2).strip()
        else:
            current["_body_lines"].append(raw_line)

    if current is not None:
        entries.append(current)

    for e in entries:
        e["body"] = " ".join(
            l.strip() for l in e.pop("_body_lines") if l.strip()
        )
    return entries


def parse_projects(path: Path) -> list[Project]:
    entries = _parse_entries(path.read_text())
    projects = []
    for e in entries:
        projects.append(Project(
            title=e["heading"],
            funding=e.get("funding", ""),
            period=e.get("period", ""),
            partners=e.get("partners", ""),
            github=e.get("github", ""),
            status=e.get("status", ""),
            description=e.get("body", ""),
        ))
    return projects


def parse_collaborators(path: Path) -> list[Collaborator]:
    entries = _parse_entries(path.read_text())
    collaborators = []
    for e in entries:
        collaborators.append(Collaborator(
            name=e["heading"],
            title=e.get("title", ""),
            affiliation=e.get("affiliation", ""),
            website=e.get("website", ""),
            email=e.get("email", ""),
            bio=e.get("body", ""),
        ))
    return collaborators


# ── HTML generators ───────────────────────────────────────────────────────────

_FUNDING_COLORS: dict[str, tuple[str, str]] = {
    "horizon":    ("#1d4ed8", "#dbeafe"),  # blue
    "snsf":       ("#065f46", "#d1fae5"),  # green
    "innosuisse": ("#92400e", "#fef3c7"),  # amber
    "hes-so":     ("#6b21a8", "#f3e8ff"),  # purple
}

def _funding_badge(funding: str) -> str:
    if not funding:
        return ""
    key = funding.lower().split()[0]
    color, bg = _FUNDING_COLORS.get(key, ("#374151", "#f3f4f6"))
    return (
        f'<span class="badge" style="background:{bg};color:{color}">'
        f'{html.escape(funding)}</span>'
    )


def _status_badge(status: str) -> str:
    if not status:
        return ""
    if status.lower() == "ongoing":
        return '<span class="badge badge-status ongoing">ongoing</span>'
    if status.lower() == "completed":
        return '<span class="badge badge-status completed">completed</span>'
    return f'<span class="badge badge-status">{html.escape(status)}</span>'


def render_projects(projects: list[Project]) -> str:
    if not projects:
        return "<p>No projects found.</p>"

    cards = []
    for p in projects:
        badges = _funding_badge(p.funding) + _status_badge(p.status)
        meta_parts = []
        if p.period:
            meta_parts.append(f'<span>{html.escape(p.period)}</span>')
        if p.partners:
            meta_parts.append(
                f'<span class="partners">{html.escape(p.partners)}</span>'
            )
        meta = f'<div class="proj-meta">{" · ".join(meta_parts)}</div>' if meta_parts else ""

        github_link = ""
        if p.github:
            github_link = (
                f'<a class="proj-link" href="{html.escape(p.github)}" '
                f'target="_blank" rel="noopener">View on GitHub →</a>'
            )

        desc = f'<p class="proj-desc">{html.escape(p.description)}</p>' if p.description else ""

        cards.append(f"""\
      <div class="proj-card">
        <div class="proj-header">
          <h3>{html.escape(p.title)}</h3>
          <div class="badges">{badges}</div>
        </div>
        {meta}
        {desc}
        {github_link}
      </div>""")

    return "\n".join(cards)


def render_collaborators(collaborators: list[Collaborator]) -> str:
    if not collaborators:
        return "<p>No collaborators found.</p>"

    cards = []
    for c in collaborators:
        initials = "".join(w[0].upper() for w in c.name.split()[:2])

        subtitle_parts = []
        if c.title:
            subtitle_parts.append(html.escape(c.title))
        if c.affiliation:
            subtitle_parts.append(html.escape(c.affiliation))
        subtitle = " · ".join(subtitle_parts)

        name_tag = c.name
        if c.website:
            name_tag = (
                f'<a href="{html.escape(c.website)}" '
                f'target="_blank" rel="noopener">{html.escape(c.name)}</a>'
            )
        else:
            name_tag = html.escape(c.name)

        bio = f'<p class="collab-bio">{html.escape(c.bio)}</p>' if c.bio else ""

        cards.append(f"""\
      <div class="collab-card">
        <div class="collab-avatar">{initials}</div>
        <div class="collab-body">
          <h3>{name_tag}</h3>
          {f'<div class="collab-subtitle">{subtitle}</div>' if subtitle else ""}
          {bio}
        </div>
      </div>""")

    return "\n".join(cards)


# ── Section HTML ─────────────────────────────────────────────────────────────

_PROJECTS_SECTION = """\
  <section class="db-section" id="projects">
    <div class="section-label">Projects</div>
    <h2>Research Projects</h2>
    <div class="proj-list">
{cards}
    </div>
  </section>"""

_COLLABORATORS_SECTION = """\
  <section class="db-section" id="collaborators">
    <div class="section-label">Network</div>
    <h2>Collaborators</h2>
    <div class="collab-grid">
{cards}
    </div>
  </section>"""


def build_projects_html(projects: list[Project]) -> str:
    return _PROJECTS_SECTION.format(cards=render_projects(projects))


def build_collaborators_html(collaborators: list[Collaborator]) -> str:
    return _COLLABORATORS_SECTION.format(cards=render_collaborators(collaborators))


# ── Injection ─────────────────────────────────────────────────────────────────

def inject(html_text: str, key: str, content: str) -> str:
    """Replace everything between <!-- BEGIN:key --> and <!-- END:key -->."""
    pattern = (
        r'(<!-- BEGIN:' + re.escape(key) + r' -->)'
        r'.*?'
        r'(<!-- END:' + re.escape(key) + r' -->)'
    )
    replacement = r'\1\n' + content + r'\n    \2'
    result, n = re.subn(pattern, replacement, html_text, flags=re.DOTALL)
    if n == 0:
        sys.exit(f"[build] Error: marker <!-- BEGIN:{key} --> not found in index.html")
    return result


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="Print generated HTML without modifying index.html")
    ap.add_argument("--data", default="data",
                    help="Directory containing projects.md and collaborators.md (default: data/)")
    ap.add_argument("--output", default="index.html",
                    help="HTML file to update in-place (default: index.html)")
    args = ap.parse_args()

    data_dir = Path(args.data)
    projects_path = data_dir / "projects.md"
    collaborators_path = data_dir / "collaborators.md"

    for p in (projects_path, collaborators_path):
        if not p.exists():
            sys.exit(f"[build] Error: {p} not found")

    projects = parse_projects(projects_path)
    collaborators = parse_collaborators(collaborators_path)

    proj_html = build_projects_html(projects)
    collab_html = build_collaborators_html(collaborators)

    if args.check:
        print("── Projects ─────────────────────────────────")
        print(proj_html)
        print("\n── Collaborators ────────────────────────────")
        print(collab_html)
        return

    index = Path(args.output)
    if not index.exists():
        sys.exit(f"[build] Error: {index} not found")

    text = index.read_text()
    text = inject(text, "projects", proj_html)
    text = inject(text, "collaborators", collab_html)
    index.write_text(text)

    print(f"[build] Wrote {len(projects)} project(s) and "
          f"{len(collaborators)} collaborator(s) into {index}")


if __name__ == "__main__":
    main()
