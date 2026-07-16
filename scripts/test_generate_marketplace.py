import json
from pathlib import Path

from generate_marketplace import generate


def _make_skill(root: Path, folder: str, body: str) -> None:
    d = root / "skills" / folder
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(body)


def test_generate_basic_with_frontmatter(tmp_path):
    _make_skill(
        tmp_path,
        "rdkit",
        "---\nname: rdkit\ndescription: Cheminformatics toolkit for molecules.\n---\n\n# RDKit\n\nBody.",
    )

    result = generate(tmp_path)

    assert result["name"] == "scientific-agent-skills"
    assert result["owner"] == {"name": "Kinandigital"}
    assert [p["name"] for p in result["plugins"]] == ["rdkit"]
    plugin = result["plugins"][0]
    assert plugin["source"] == "./"
    assert plugin["skills"] == ["./skills/rdkit"]
    assert plugin["description"] == "Cheminformatics toolkit for molecules."


def test_generate_description_fallback_to_heading(tmp_path):
    # No frontmatter description → fall back to first paragraph after the # heading.
    _make_skill(
        tmp_path,
        "plain-skill",
        "# Plain Skill\n\nA plain skill with no frontmatter at all.",
    )

    result = generate(tmp_path)
    plugin = result["plugins"][0]
    assert plugin["name"] == "plain-skill"
    assert plugin["description"] == "A plain skill with no frontmatter at all."


def test_generate_is_alphabetical(tmp_path):
    _make_skill(tmp_path, "zebra", "---\ndescription: Z.\n---\n\n# Z\n\nB.")
    _make_skill(tmp_path, "alpha", "---\ndescription: A.\n---\n\n# A\n\nB.")

    result = generate(tmp_path)
    assert [p["name"] for p in result["plugins"]] == ["alpha", "zebra"]


def test_generate_skips_dirs_without_skill_md(tmp_path):
    _make_skill(tmp_path, "real-skill", "---\ndescription: Real.\n---\n\n# Real\n\nB.")
    (tmp_path / "skills" / "not-a-skill").mkdir(parents=True)

    result = generate(tmp_path)
    assert [p["name"] for p in result["plugins"]] == ["real-skill"]


def test_generate_rejects_non_kebab_folder(tmp_path):
    import pytest

    _make_skill(tmp_path, "Bad_Name", "---\ndescription: X.\n---\n\n# X\n\nB.")
    with pytest.raises(ValueError, match="kebab-case"):
        generate(tmp_path)


def test_generate_requires_skills_dir(tmp_path):
    import pytest

    with pytest.raises(ValueError, match="skills"):
        generate(tmp_path)


def test_generate_block_scalar_description_is_joined(tmp_path):
    # `description: >` (YAML block scalar): value spans indented continuation
    # lines — must join them, NOT emit the literal ">" or fall back to heading.
    _make_skill(
        tmp_path,
        "bids",
        "---\nname: bids\ndescription: >\n  Use this for BIDS datasets:\n  organizing neuroscience data.\nlicense: CC-BY\n---\n\n# BIDS\n\nBrain imaging data spec.",
    )

    result = generate(tmp_path)
    plugin = result["plugins"][0]
    assert (
        plugin["description"]
        == "Use this for BIDS datasets: organizing neuroscience data."
    )


def test_generate_crlf_frontmatter(tmp_path):
    # CRLF line endings must not break the frontmatter scan.
    _make_skill(
        tmp_path,
        "crlf-skill",
        "---\r\nname: crlf-skill\r\ndescription: A CRLF skill.\r\n---\r\n\r\n# CRLF\r\n\r\nBody.\r\n",
    )

    result = generate(tmp_path)
    plugin = result["plugins"][0]
    assert plugin["description"] == "A CRLF skill."


def test_generate_truncates_long_frontmatter_description(tmp_path):
    long_desc = "x" * 500
    _make_skill(
        tmp_path,
        "wordy",
        f"---\ndescription: {long_desc}\n---\n\n# Wordy\n\nBody.",
    )

    result = generate(tmp_path)
    assert len(result["plugins"][0]["description"]) == 200

