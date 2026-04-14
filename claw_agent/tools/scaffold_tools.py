"""Scaffold tools — generate project boilerplate and common files."""

from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Gitignore templates
# ---------------------------------------------------------------------------
_GITIGNORE = {
    "python": (
        "__pycache__/\n*.py[cod]\n*$py.class\n*.egg-info/\ndist/\nbuild/\n"
        ".eggs/\n*.egg\n.venv/\nenv/\n.env\n*.so\n.mypy_cache/\n.ruff_cache/\n"
        ".pytest_cache/\nhtmlcov/\n.coverage\n*.log\n"
    ),
    "node": (
        "node_modules/\ndist/\nbuild/\n.env\n.env.local\n*.log\nnpm-debug.log*\n"
        "yarn-debug.log*\nyarn-error.log*\n.cache/\ncoverage/\n.next/\n.nuxt/\n"
    ),
    "go": (
        "bin/\n*.exe\n*.exe~\n*.dll\n*.so\n*.dylib\n*.test\n*.out\nvendor/\n"
        ".env\n*.log\n"
    ),
    "rust": (
        "/target\nCargo.lock\n**/*.rs.bk\n*.pdb\n.env\n*.log\n"
    ),
    "generic": (
        ".env\n*.log\n.DS_Store\nThumbs.db\n*.swp\n*.swo\n*~\n.idea/\n"
        ".vscode/\n*.bak\n*.tmp\n"
    ),
}

# ---------------------------------------------------------------------------
# License templates (short versions)
# ---------------------------------------------------------------------------
_LICENSES = {
    "mit": (
        "MIT License\n\nCopyright (c) {year} {author}\n\n"
        "Permission is hereby granted, free of charge, to any person obtaining a copy\n"
        "of this software and associated documentation files (the \"Software\"), to deal\n"
        "in the Software without restriction, including without limitation the rights\n"
        "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\n"
        "copies of the Software, and to permit persons to whom the Software is\n"
        "furnished to do so, subject to the following conditions:\n\n"
        "The above copyright notice and this permission notice shall be included in all\n"
        "copies or substantial portions of the Software.\n\n"
        "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n"
        "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n"
        "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n"
        "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
        "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n"
        "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\n"
        "SOFTWARE.\n"
    ),
    "apache2": (
        "Apache License, Version 2.0\n\nCopyright {year} {author}\n\n"
        "Licensed under the Apache License, Version 2.0. You may obtain a copy at\n"
        "http://www.apache.org/licenses/LICENSE-2.0\n"
    ),
    "gpl3": (
        "GNU General Public License v3.0\n\nCopyright (c) {year} {author}\n\n"
        "This program is free software: you can redistribute it and/or modify\n"
        "it under the terms of the GNU General Public License as published by\n"
        "the Free Software Foundation, either version 3 of the License, or\n"
        "(at your option) any later version.\n"
    ),
}


def init_project(directory: str, language: str = "python", name: str = "") -> str:
    """Initialize a project with boilerplate files.

    Creates: README.md, .gitignore, src structure, and optionally
    pyproject.toml / package.json / go.mod / Cargo.toml
    """
    root = Path(directory).expanduser().resolve()
    lang = language.lower()
    project_name = name or root.name

    created: list[str] = []

    root.mkdir(parents=True, exist_ok=True)

    # .gitignore
    gi_content = _GITIGNORE.get(lang, _GITIGNORE["generic"])
    gi_path = root / ".gitignore"
    if not gi_path.exists():
        gi_path.write_text(gi_content, encoding="utf-8")
        created.append(".gitignore")

    # README.md
    readme = root / "README.md"
    if not readme.exists():
        readme.write_text(f"# {project_name}\n\nA {lang} project.\n", encoding="utf-8")
        created.append("README.md")

    # Language-specific setup
    if lang == "python":
        (root / project_name.replace("-", "_")).mkdir(exist_ok=True)
        init_f = root / project_name.replace("-", "_") / "__init__.py"
        if not init_f.exists():
            init_f.write_text(f'"""Top-level package for {project_name}."""\n', encoding="utf-8")
            created.append(f"{project_name.replace('-', '_')}/__init__.py")
        pyp = root / "pyproject.toml"
        if not pyp.exists():
            pyp.write_text(
                f'[project]\nname = "{project_name}"\nversion = "0.1.0"\n'
                f'description = ""\nrequires-python = ">=3.10"\n\n'
                f'[build-system]\nrequires = ["setuptools>=68"]\n'
                f'build-backend = "setuptools.build_meta"\n',
                encoding="utf-8",
            )
            created.append("pyproject.toml")
    elif lang in ("node", "javascript", "typescript"):
        pkg = root / "package.json"
        if not pkg.exists():
            pkg.write_text(
                '{\n'
                f'  "name": "{project_name}",\n'
                '  "version": "0.1.0",\n'
                '  "description": "",\n'
                '  "main": "index.js",\n'
                '  "scripts": {\n    "test": "echo \\"Error: no test\\" && exit 1"\n  }\n'
                '}\n',
                encoding="utf-8",
            )
            created.append("package.json")
        src = root / "src"
        src.mkdir(exist_ok=True)
        idx = src / ("index.ts" if lang == "typescript" else "index.js")
        if not idx.exists():
            idx.write_text("// entry point\n", encoding="utf-8")
            created.append(f"src/{idx.name}")
    elif lang == "go":
        mod = root / "go.mod"
        if not mod.exists():
            mod.write_text(f"module {project_name}\n\ngo 1.21\n", encoding="utf-8")
            created.append("go.mod")
        main = root / "main.go"
        if not main.exists():
            main.write_text(
                'package main\n\nimport "fmt"\n\nfunc main() {\n\tfmt.Println("hello")\n}\n',
                encoding="utf-8",
            )
            created.append("main.go")
    elif lang == "rust":
        src = root / "src"
        src.mkdir(exist_ok=True)
        mainrs = src / "main.rs"
        if not mainrs.exists():
            mainrs.write_text('fn main() {\n    println!("hello");\n}\n', encoding="utf-8")
            created.append("src/main.rs")
        cargo = root / "Cargo.toml"
        if not cargo.exists():
            cargo.write_text(
                f'[package]\nname = "{project_name}"\nversion = "0.1.0"\nedition = "2021"\n',
                encoding="utf-8",
            )
            created.append("Cargo.toml")

    if not created:
        return f"Project at {root} — all files already exist, nothing created."
    return f"Initialized {lang} project '{project_name}' at {root}\nCreated:\n  " + "\n  ".join(created)


def add_gitignore(directory: str, language: str = "generic") -> str:
    """Add or append to .gitignore with language-appropriate patterns."""
    root = Path(directory).expanduser().resolve()
    lang = language.lower()
    patterns = _GITIGNORE.get(lang, _GITIGNORE["generic"])

    gi = root / ".gitignore"
    existing = gi.read_text(encoding="utf-8") if gi.exists() else ""

    new_lines = []
    for line in patterns.strip().splitlines():
        if line and line not in existing:
            new_lines.append(line)

    if not new_lines:
        return f".gitignore at {root} already covers {lang} patterns."

    with open(gi, "a", encoding="utf-8") as f:
        if existing and not existing.endswith("\n"):
            f.write("\n")
        f.write(f"\n# {lang}\n")
        f.write("\n".join(new_lines) + "\n")

    return f"Added {len(new_lines)} {lang} patterns to {gi}"


def add_license(directory: str, license_type: str = "mit", author: str = "") -> str:
    """Add a LICENSE file to a project."""
    root = Path(directory).expanduser().resolve()
    lt = license_type.lower().replace("-", "").replace(" ", "")

    template = _LICENSES.get(lt)
    if not template:
        return f"Unknown license '{license_type}'. Supported: {', '.join(_LICENSES)}"

    lic = root / "LICENSE"
    if lic.exists():
        return f"LICENSE already exists at {lic}"

    year = datetime.now().year
    text = template.format(year=year, author=author or "Author")
    lic.write_text(text, encoding="utf-8")
    return f"Created {lic} ({license_type.upper()})"
