#!/usr/bin/env python3
"""
build.py – Parse data/team/ and data/projects/ directories, generate HTML
sections, and inject them into index.html between marker comments.

Each person has their own file under data/team/<name>.md.
Each project has its own file under data/projects/<name>.md.
Files are processed in alphabetical order; prefix with numbers (01-, 02-, …)
to control display order.

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
import hashlib
import html
import re
import sys
from dataclasses import dataclass
from pathlib import Path


# ── Data models ──────────────────────────────────────────────────────────────

@dataclass
class Project:
    title: str
    funding: str = ""
    period: str = ""
    partners: str = ""
    website: str = ""
    github: str = ""
    status: str = ""
    description: str = ""


@dataclass
class Collaborator:
    name: str
    role: str = ""
    title: str = ""
    affiliation: str = ""
    website: str = ""
    portfolio: str = ""
    email: str = ""
    picture: str = ""
    interests: str = ""
    bio: str = ""


# ── Parser ───────────────────────────────────────────────────────────────────

_KNOWN_FIELDS = {
    "funding", "period", "partners", "website", "github", "status",
    "role", "title", "affiliation", "email", "picture", "interests", "portfolio",
}

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
            current[m.group(1).lower()] = m.group(2).strip().strip("<>")
        else:
            current["_body_lines"].append(raw_line)

    if current is not None:
        entries.append(current)

    for e in entries:
        e["body"] = "\n".join(e.pop("_body_lines")).strip()
    return entries


def _parse_md_files(dir_path: Path) -> list[dict]:
    """Read all *.md files from a directory (sorted by name) and parse entries."""
    entries = []
    for f in sorted(dir_path.glob("*.md")):
        entries.extend(_parse_entries(f.read_text()))
    return entries


def parse_projects(source: Path) -> list[Project]:
    entries = _parse_md_files(source) if source.is_dir() else _parse_entries(source.read_text())
    return [
        Project(
            title=e["heading"],
            funding=e.get("funding", ""),
            period=e.get("period", ""),
            partners=e.get("partners", ""),
            website=e.get("website", ""),
            github=e.get("github", ""),
            status=e.get("status", ""),
            description=e.get("body", ""),
        )
        for e in entries
    ]


def parse_collaborators(source: Path) -> list[Collaborator]:
    entries = _parse_md_files(source) if source.is_dir() else _parse_entries(source.read_text())
    return [
        Collaborator(
            name=e["heading"],
            role=e.get("role", ""),
            title=e.get("title", ""),
            affiliation=e.get("affiliation", ""),
            website=e.get("website", ""),
            portfolio=e.get("portfolio", ""),
            email=e.get("email", ""),
            picture=e.get("picture", ""),
            interests=e.get("interests", ""),
            bio=e.get("body", ""),
        )
        for e in entries
    ]


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

        links = []
        if p.website:
            links.append(
                f'<a class="proj-link" href="{html.escape(p.website)}" '
                f'target="_blank" rel="noopener">Project website →</a>'
            )
        if p.github:
            links.append(
                f'<a class="proj-link" href="{html.escape(p.github)}" '
                f'target="_blank" rel="noopener">GitHub →</a>'
            )
        links_html = ' <span class="proj-link-sep">·</span> '.join(links)

        desc = f'<p class="proj-desc">{html.escape(p.description)}</p>' if p.description else ""

        cards.append(f"""\
      <div class="proj-card">
        <div class="proj-header">
          <h3>{html.escape(p.title)}</h3>
          <div class="badges">{badges}</div>
        </div>
        {meta}
        {desc}
        {links_html}
      </div>""")

    return "\n".join(cards)


def _render_inline(text: str) -> str:
    """Render inline markdown (links, bold) within an already-plaintext string."""
    result = ""
    last_end = 0
    for m in re.finditer(r'\[([^\]]*)\]\(([^)]*)\)', text):
        result += re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>',
                         html.escape(text[last_end:m.start()]))
        result += (
            f'<a href="{html.escape(m.group(2))}" target="_blank" rel="noopener">'
            f'{html.escape(m.group(1))}</a>'
        )
        last_end = m.end()
    result += re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>',
                     html.escape(text[last_end:]))
    return result


def _render_bio(text: str) -> str:
    """Convert plain text / simple markdown (bullets, links, bold) to HTML."""
    if not text.strip():
        return ""
    lines = text.splitlines()
    parts: list[str] = []
    in_list = False
    para_lines: list[str] = []

    def flush_para() -> None:
        if para_lines:
            parts.append(f'<p class="collab-bio">{_render_inline(" ".join(para_lines))}</p>')
            para_lines.clear()

    for line in lines:
        stripped = line.strip()
        is_bullet = stripped.startswith("- ") or stripped.startswith("* ")
        if is_bullet:
            flush_para()
            if not in_list:
                parts.append('<ul class="collab-bio-list">')
                in_list = True
            parts.append(f'<li>{_render_inline(stripped[2:])}</li>')
        else:
            if in_list:
                parts.append("</ul>")
                in_list = False
            if stripped:
                para_lines.append(stripped)
            else:
                flush_para()

    if in_list:
        parts.append("</ul>")
    flush_para()
    return "\n".join(parts)


def render_collaborators(collaborators: list[Collaborator]) -> str:
    if not collaborators:
        return "<p>No collaborators found.</p>"

    cards = []
    for c in collaborators:
        # Avatar: explicit photo > Gravatar (if email) > coloured initials
        initials = "".join(w[0].upper() for w in c.name.split()[:2])
        if c.picture:
            avatar = (
                f'<img class="collab-photo" src="{html.escape(c.picture)}" '
                f'alt="{html.escape(initials)}" />'
            )
        elif c.email:
            digest = hashlib.md5(c.email.strip().lower().encode()).hexdigest()
            gravatar_url = f"https://www.gravatar.com/avatar/{digest}?s=200&d=mp"
            avatar = (
                f'<img class="collab-photo" src="{gravatar_url}" '
                f'alt="{html.escape(initials)}" />'
            )
        else:
            avatar = f'<div class="collab-avatar">{initials}</div>'

        display_name = f"{c.title} {c.name}".strip() if c.title else c.name
        if c.website:
            name_tag = (
                f'<a href="{html.escape(c.website)}" '
                f'target="_blank" rel="noopener">{html.escape(display_name)}</a>'
            )
        else:
            name_tag = html.escape(display_name)

        subtitle_parts = []
        if c.role:
            subtitle_parts.append(html.escape(c.role))
        if c.affiliation:
            subtitle_parts.append(html.escape(c.affiliation))
        subtitle = (
            f'<div class="collab-subtitle">{" · ".join(subtitle_parts)}</div>'
            if subtitle_parts else ""
        )

        if c.interests:
            tags = "".join(
                f'<span class="interest-tag">{html.escape(t.strip())}</span>'
                for t in c.interests.split(",") if t.strip()
            )
            interests_html = f'<div class="collab-interests">{tags}</div>'
        else:
            interests_html = ""

        bio = _render_bio(c.bio)

        links = []
        if c.website:
            links.append(
                f'<a class="collab-link" href="{html.escape(c.website)}" '
                f'target="_blank" rel="noopener">Website →</a>'
            )
        if c.portfolio:
            links.append(
                f'<a class="collab-link" href="{html.escape(c.portfolio)}" '
                f'target="_blank" rel="noopener">Portfolio →</a>'
            )
        links_html = (
            f'<div class="collab-links">{"&ensp;·&ensp;".join(links)}</div>'
            if links else ""
        )

        cards.append(f"""\
      <div class="collab-card">
        {avatar}
        <div class="collab-body">
          <h3>{name_tag}</h3>
          {interests_html}
          {subtitle}
          {bio}
          {links_html}
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
  <section class="db-section" id="team">
    <div class="section-label">People</div>
    <h2>Team</h2>
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
                    help="Directory containing team/ and projects/ subdirs (default: data/)")
    ap.add_argument("--output", default="index.html",
                    help="HTML file to update in-place (default: index.html)")
    args = ap.parse_args()

    data_dir = Path(args.data)

    # Resolve team source: prefer data/team/ dir, fall back to data/collaborators.md
    team_source = data_dir / "team"
    if not team_source.is_dir():
        team_source = data_dir / "collaborators.md"
        if not team_source.exists():
            sys.exit(f"[build] Error: neither {data_dir / 'team'} nor {data_dir / 'collaborators.md'} found")

    # Resolve projects source: prefer data/projects/ dir, fall back to data/projects.md
    projects_source = data_dir / "projects"
    if not projects_source.is_dir():
        projects_source = data_dir / "projects.md"
        if not projects_source.exists():
            sys.exit(f"[build] Error: neither {data_dir / 'projects'} nor {data_dir / 'projects.md'} found")

    collaborators = parse_collaborators(team_source)
    projects = parse_projects(projects_source)

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
