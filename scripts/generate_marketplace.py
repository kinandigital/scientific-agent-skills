#!/usr/bin/env python3
"""Generate .claude-plugin/marketplace.json from skills/*.

Each skills/<name>/ folder becomes one plugin entry scoped to its own subdir
via the marketplace's shared-root pattern (source: "./", skills: [<subdir>]).
Stdlib only.

Run: `uv run python scripts/generate_marketplace.py` (writes the file).
Import `generate(root)` for testing.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

MARKETPLACE_NAME = "scientific-agent-skills"
OWNER = {"name": "Kinandigital"}
KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def _extract_description(content: str, folder: str) -> str:
    """Frontmatter `description:` wins; else first paragraph after the first `# ` heading.

    Block-scalar indicators (`description: >` / `description: |`) and empty
    values are treated as "no usable description" → fall through to the
    heading path, rather than emitting the literal indicator.
    """
    # Normalize line endings so CRLF checkouts don't break the frontmatter scan.
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    if content.startswith("---\n"):
        end = content.find("\n---", 4)
        if end != -1:
            fm_lines = content[4:end].splitlines()
            for i, line in enumerate(fm_lines):
                if line.startswith("description:"):
                    inline = line.split(":", 1)[1].strip().strip('"').strip("'")
                    # Block scalar (`description: >` or `|`): value is on the
                    # following more-indented lines. Join them (folded/literal
                    # both collapse to the joined text for our one-line summary).
                    if inline in (">", "|", ""):
                        block: list[str] = []
                        for cont in fm_lines[i + 1 :]:
                            if cont.startswith(" ") or cont.startswith("\t"):
                                block.append(cont.strip())
                            elif cont.strip() == "":
                                continue
                            else:
                                break
                        desc = " ".join(block)
                    else:
                        desc = inline
                    if desc:
                        return desc[:200]
    # Fallback: first non-empty paragraph after the first "# " heading.
    lines = content.splitlines()
    started = False
    para: list[str] = []
    for line in lines:
        if not started:
            if line.startswith("# "):
                started = True
            continue
        stripped = line.strip()
        if stripped == "":
            if para:
                break
            continue
        if stripped.startswith("#"):
            break
        para.append(stripped)
    desc = " ".join(para) if para else folder
    return desc[:200]


def generate(root: Path) -> dict:
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        raise ValueError(f"No skills/ directory at {root}")

    plugins: list[dict] = []
    seen: set[str] = set()
    for entry in sorted(skills_dir.iterdir()):
        if not entry.is_dir():
            continue
        skill_md = entry / "SKILL.md"
        if not skill_md.exists():
            continue
        name = entry.name
        if not KEBAB_RE.match(name):
            raise ValueError(
                f"Skill folder '{name}' is not kebab-case (lowercase, digits, hyphens)."
            )
        if name in seen:
            raise ValueError(f"Duplicate plugin name '{name}'")
        seen.add(name)
        content = skill_md.read_text(encoding="utf-8")
        plugins.append(
            {
                "name": name,
                "source": "./",
                "skills": [f"./skills/{name}"],
                "description": _extract_description(content, name),
            }
        )

    return {
        "name": MARKETPLACE_NAME,
        "owner": OWNER,
        "description": (
            "Scientific AI skills for Claude Code — one installable plugin per "
            "skill across bioinformatics, cheminformatics, ML/AI, data analysis, "
            "scientific communication, and more."
        ),
        "plugins": plugins,
    }


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    marketplace = generate(root)
    out_dir = root / ".claude-plugin"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "marketplace.json").write_text(
        json.dumps(marketplace, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(marketplace['plugins'])} plugins to .claude-plugin/marketplace.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
