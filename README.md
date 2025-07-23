
---

# One-Click Context Toolkit 🗂️✨

[![CI](https://github.com/lucasfuturist/oneclick-context/actions/workflows/ci.yml/badge.svg)](https://github.com/lucasfuturist/oneclick-context/actions/workflows/ci.yml)

*Visual file trees & inline code commentary for any project — in one command.*

---

## Features

| Flag / Sub-feature | What it does |
| :--- | :--- |
| `--fmt text` (default) | Classic Unicode tree in the terminal |
| `--fmt md` | Collapsible Markdown ready for GitHub / PRs |
| `--fmt json` | Machine-readable nested dict |
| `--fmt html` | Expandable `<ul><li>` list for web/docs |
| `--list-scripts .py .ts` | **Prints full source** of matching files |
| `--depth N` | Limit recursion (default = 3) |
| `--suppress node_modules` | Skip noisy folders (case-insensitive) |

---

## Installation

```bash
# recommended
pipx install oneclick-context

# or plain pip
python -m pip install --upgrade oneclick-context
```Requires Python 3.10+.
`pipx` keeps the tool isolated in its own virtual-env & puts `oneclick` on your PATH.

## Quick start

#### 1. Plain-text tree
```bash
oneclick . --depth 2
``````css
├── src
│   └── oneclick_context
├── tests
│   └── test_cli.py
└── pyproject.toml
```

#### 2. Paste-ready Markdown
```bash
oneclick . --depth 2 --fmt md
``````html
<details><summary>📁 my-project</summary>

├── src
│   └── ...
└── pyproject.toml

</details>
```

#### 3. JSON (pipe to `jq`)
```bash
oneclick . --fmt json | jq .
``````jsonc
{
  "type": "dir",
  "name": "my-project",
  "children": [
    { "type": "file", "name": "pyproject.toml", "children": [] }
  ]
}
```

#### 4. HTML
```bash
oneclick . --fmt html > tree.html && start tree.html
```

#### 5. Print out all scripts
```bash
oneclick . --list-scripts .py .ts .yaml > SCRIPTS.md
```
Combine with `depth` / `suppress` flags:
```bash
oneclick . --depth 3 --suppress node_modules dist .git \
          --list-scripts .py .sh
```

## Why?
*   **LLM context compression** — shrink 50 KLOC into a 1-page digest for ChatGPT, Claude, etc.
*   **Lightning-fast code reviews** — drop the Markdown tree in a PR comment.
*   **Docs & onboarding** — generate an instant project map for new teammates.

## Roadmap
- [ ] GPT-powered file summaries (`--summarise`)
- [ ] VS Code extension panel
- [ ] SVG / Graphviz exporter

## Contributing
PRs and issues welcome!
```bash
poetry install
poetry run pytest -q
```
