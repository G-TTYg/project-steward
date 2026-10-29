#!/usr/bin/env python3
"""Check published package structure, Markdown routes, and an exported CLI smoke.

Uses only the standard library and copies package sources into a disposable export.
The Codex quick validator remains an additional local check when available.
"""

import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import unquote


def markdown_body(path):
    text = path.read_text(encoding="utf-8")
    return re.sub(r"^(`{3,}|~{3,}).*?^\1[^\n]*$", "", text, flags=re.M | re.S)


def anchors(path):
    result = set()
    counts = {}
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", markdown_body(path), re.M):
        slug = re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        result.add(slug if count == 0 else f"{slug}-{count}")
    return result


def check_links(root):
    count = 0
    for source in root.rglob("*.md"):
        if any(part in {".git", "__pycache__"} for part in source.parts):
            continue
        for raw in re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", markdown_body(source)):
            target = raw.strip("<>")
            if re.match(r"[A-Za-z][\w+.-]*:", target) or target.startswith("//"):
                continue
            path, _, fragment = unquote(target).partition("#")
            destination = (source.parent / path).resolve() if path else source.resolve()
            if not destination.is_relative_to(root.resolve()):
                raise ValueError(f"link escapes checked root: {source}: {raw}")
            if not destination.exists():
                raise ValueError(f"missing link target: {source}: {raw}")
            if fragment and destination.suffix == ".md" and fragment not in anchors(destination):
                raise ValueError(f"missing anchor: {source}: {raw}")
            count += 1
    return count


def check_package(package):
    skill = (package / "SKILL.md").read_text(encoding="utf-8")
    if not skill.startswith("---\n") or "\n---\n" not in skill[4:]:
        raise ValueError("SKILL requires YAML frontmatter")
    front = skill.split("---", 2)[1]
    if not re.search(r"^name: project-steward$", front, re.M) or not re.search(r"^description: \S.+", front, re.M):
        raise ValueError("missing name/description frontmatter")
    if any((package / name).exists() for name in (".git", "AGENTS.md", "README.md", "tests", "logs")):
        raise ValueError("runtime package contains maintenance content")
    references = sorted((package / "references").glob("*.md"))
    for reference in references:
        if f"references/{reference.name}" not in skill:
            raise ValueError(f"reference missing from SKILL routes: {reference.name}")
    for source in (package / "scripts").rglob("*.py"):
        compile(source.read_text(encoding="utf-8"), str(source), "exec")
    metadata = (package / "agents" / "openai.yaml").read_text(encoding="utf-8")
    if 'display_name: "Project Steward"' not in metadata or "$project-steward" not in metadata:
        raise ValueError("Codex metadata does not identify the skill")
    with tempfile.TemporaryDirectory(prefix="steward-package-") as temporary:
        export = Path(temporary) / "export" / "project-steward"
        shutil.copytree(package, export, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        project = Path(temporary) / "project"
        project.mkdir()
        script = export / "scripts" / "long_work.py"
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        commands = [["--help"], ["init", "--project", str(project), "--task", "export smoke"]]
        for args in commands:
            subprocess.run([sys.executable, "-B", "-X", "utf8", str(script), *args], check=True,
                           capture_output=True, text=True, encoding="utf-8", env=env)
        run = next((project / "docs" / "agent-runs").iterdir())
        subprocess.run([sys.executable, "-B", str(script), "doctor", "--run", str(run)], check=True,
                       capture_output=True, env=env)
    return len(references)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, default=Path(__file__).resolve().parents[1] / "project-steward")
    parser.add_argument("--repository", type=Path, default=None, help="also check maintenance Markdown routes")
    args = parser.parse_args()
    if args.repository and (args.package / "LICENSE").read_bytes() != (args.repository / "LICENSE").read_bytes():
        raise ValueError("runtime and repository license notices must match")
    references = check_package(args.package.resolve())
    count = check_links((args.repository or args.package).resolve())
    print(f"Package/export smoke passed; {references} routed references; {count} local links/anchors checked.")


if __name__ == "__main__":
    main()
