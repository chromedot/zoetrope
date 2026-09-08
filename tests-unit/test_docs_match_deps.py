"""Keep dependency declarations and docs honest about what the code actually does.

Three checks, each of which corresponds to a real problem found in this repo:

(a) Every third-party module the code imports is declared in pyproject.toml.
    Otherwise a fresh checkout hits an ImportError with nothing to point at.

(b) Every dependency declared in pyproject.toml is actually imported somewhere.
    This is the one that catches documentation drift in the other direction --
    docs/tech-stack.md claimed "SQLAlchemy/Alembic: Used for Object-
    Relational Mapping (ORM) and database migrations" for months, while the
    data layer was raw sqlite3 and neither package was imported anywhere.

(c) Every directory mentioned in backticks in the docs exists.
    Catches phantom directory structures -- documentation describing a layout
    the repo does not have, which is how a reader (human or agent) ends up
    looking for `src/` in a project that keeps its code in `scripts/`.
"""

import ast
import os
import re
import sys
import tomllib

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Vendored/generated trees that aren't ours to police.
EXCLUDED_DIRS = {
    "ComfyUI", "comfyui-env", ".git", "__pycache__", "models", "output",
    "user", "__manager", "node_modules", ".pytest_cache", "logs", "pids",
    "default", "data",
}

# import name -> distribution name, where they differ.
IMPORT_TO_DIST = {
    "edge_tts": "edge-tts",
    "google": "google-generativeai",
    "multipart": "python-multipart",
    "yaml": "pyyaml",
    "PIL": "pillow",
}

# Declared but legitimately never imported by our own code. Each entry needs a
# reason -- this allowlist is the pressure valve for check (b), so an unexplained
# addition here defeats the point of the check.
DECLARED_WITHOUT_DIRECT_IMPORT = {
    "uvicorn",           # ASGI server, invoked as a process (evergreen.sh), not imported
    "jinja2",            # used through fastapi's Jinja2Templates wrapper, never directly
    "python-multipart",  # required by FastAPI to parse Form(...), never imported directly
    "pytest-asyncio",    # pytest plugin, used via @pytest.mark.asyncio
    "pytest-httpx",      # pytest plugin, used via the httpx_mock fixture
    "pytest-cov",        # pytest plugin, used via --cov flags in pyproject.toml
}


def _our_python_files():
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for name in filenames:
            if name.endswith(".py"):
                yield os.path.join(dirpath, name)


def _first_party_names():
    """Top-level module/package names that live in this repo."""
    names = set()
    for entry in os.listdir(REPO_ROOT):
        if entry in EXCLUDED_DIRS:
            continue
        full = os.path.join(REPO_ROOT, entry)
        if os.path.isdir(full):
            names.add(entry)
            # Sibling-style imports (`import database`) resolve against
            # pyproject.toml's pythonpath entries, so their contents count
            # as first-party too.
            for sub in os.listdir(full):
                if sub.endswith(".py"):
                    names.add(sub[:-3])
        elif entry.endswith(".py"):
            names.add(entry[:-3])
    return names


def _imported_top_level_modules():
    """Every top-level module name imported by our own Python files."""
    found = set()
    for path in _our_python_files():
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    found.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0 and node.module:
                    found.add(node.module.split(".")[0])
    return found


def _declared_dependencies():
    """Every distribution named in pyproject.toml, required or optional."""
    with open(os.path.join(REPO_ROOT, "pyproject.toml"), "rb") as f:
        data = tomllib.load(f)
    project = data.get("project", {})
    declared = list(project.get("dependencies", []))
    for extra in project.get("optional-dependencies", {}).values():
        declared.extend(extra)
    # Strip any version specifiers -- "httpx>=0.28" -> "httpx".
    return {re.split(r"[<>=!~\[ ]", dep)[0].strip().lower() for dep in declared if dep.strip()}


def _third_party_imports():
    stdlib = set(sys.stdlib_module_names)
    first_party = _first_party_names()
    return {
        name for name in _imported_top_level_modules()
        if name not in stdlib and name not in first_party and not name.startswith("_")
    }


def test_imports_are_declared():
    """(a) Every third-party import is declared in pyproject.toml."""
    declared = _declared_dependencies()
    undeclared = set()
    for name in _third_party_imports():
        dist = IMPORT_TO_DIST.get(name, name).lower()
        if dist not in declared:
            undeclared.add(f"{name} (would be declared as '{dist}')")
    assert not undeclared, (
        "These modules are imported but not declared in pyproject.toml, so a "
        f"fresh checkout would fail on them: {sorted(undeclared)}"
    )


def test_declared_dependencies_are_used():
    """(b) Every declared dependency is actually imported somewhere.

    Guards against the failure mode where docs/config claim a technology the
    code never adopted -- see this module's docstring re: SQLAlchemy.
    """
    imported_dists = {
        IMPORT_TO_DIST.get(name, name).lower() for name in _third_party_imports()
    }
    unused = _declared_dependencies() - imported_dists - DECLARED_WITHOUT_DIRECT_IMPORT
    assert not unused, (
        "These are declared in pyproject.toml but never imported anywhere. "
        "Either start using them, drop them, or add them to "
        f"DECLARED_WITHOUT_DIRECT_IMPORT with a reason: {sorted(unused)}"
    )


def test_tech_stack_doc_does_not_claim_unused_libraries():
    """(b, prose edition) docs/tech-stack.md shouldn't claim unused tech.

    The specific regression: it described SQLAlchemy/Alembic as the ORM and
    migration layer while the code used raw sqlite3 and imported neither.
    """
    path = os.path.join(REPO_ROOT, "docs", "tech-stack.md")
    if not os.path.exists(path):
        return
    imported = {name.lower() for name in _third_party_imports()}

    # Only bolded bullet subjects count as a *claim* ("- **SQLAlchemy/Alembic:**
    # Used for ORM..."), which is the shape the actual regression took. Prose
    # mentioning a library elsewhere is not a claim -- notably, the corrected
    # entry has to name SQLAlchemy in order to explain that it is NOT used, and
    # that explanation must not trip this check.
    claims = re.findall(r"^\s*[-*]\s*\*\*([^*]+)\*\*", open(path, encoding="utf-8").read(), re.MULTILINE)
    claimed_text = " ".join(claims).lower()

    # Only libraries we can actually check for -- naming a language, a
    # protocol or an external binary in the tech stack is fine.
    checkable = {"sqlalchemy", "alembic", "django", "flask", "celery", "redis", "pandas", "numpy"}
    claimed_but_unused = {
        lib for lib in checkable
        if re.search(rf"\b{re.escape(lib)}\b", claimed_text) and lib not in imported
    }
    assert not claimed_but_unused, (
        "docs/tech-stack.md names libraries that nothing imports: "
        f"{sorted(claimed_but_unused)}. Either adopt them or stop claiming them."
    )


def _docs_files():
    for name in ("README.md", "gemini.md", "CLAUDE.md"):
        path = os.path.join(REPO_ROOT, name)
        if os.path.exists(path):
            yield path
    docs_dir = os.path.join(REPO_ROOT, "docs")
    if os.path.isdir(docs_dir):
        for name in sorted(os.listdir(docs_dir)):
            if name.endswith(".md"):
                yield os.path.join(docs_dir, name)


# Scoped deliberately narrowly: only *directory* references (a backticked
# token ending in "/"). That is the exact shape the real regression took --
# the old gemini.md documented a "Repository Structure" of `src/`, `web/`,
# `stories/` and `workflows/`, none of which ever existed at the repo root.
#
# Bare filenames (`app.py`) are excluded on purpose: docs refer to files by
# name in prose constantly, and resolving those against the repo root produces
# nothing but false positives. Same for forward-looking references -- see
# FORWARD_LOOKING_DOCS.
_DIR_TOKEN = re.compile(r"^[A-Za-z0-9._/-]+/$")

# Docs that describe intended/future state by design, where referencing a file
# that doesn't exist yet is the point, not a mistake. Empty since the planning
# docs moved out of this repo; kept because the exemption is still the right
# shape if a forward-looking doc is ever added back.
FORWARD_LOOKING_DOCS: set[str] = set()


def test_backticked_doc_directories_exist():
    """(c) Directories referenced in the docs actually exist.

    Catches phantom directory structures -- documentation describing a layout
    the repo does not have, which is how a reader (human or agent) ends up
    looking for `src/` in a project that keeps its code in `scripts/`.
    """
    missing = []
    for doc in _docs_files():
        rel_doc = os.path.relpath(doc, REPO_ROOT)
        if rel_doc in FORWARD_LOOKING_DOCS:
            continue
        for token in re.findall(r"`([^`\n]+)`", open(doc, encoding="utf-8").read()):
            token = token.strip()
            if not _DIR_TOKEN.match(token):
                continue
            # Absolute paths describe other machines, not this repo.
            if token.startswith(("/", "~")):
                continue
            if not os.path.isdir(os.path.join(REPO_ROOT, token.rstrip("/"))):
                missing.append(f"{rel_doc}: `{token}`")
    assert not missing, (
        "These directories are referenced in the docs but don't exist "
        f"(phantom structure, or a stale path): {missing}"
    )
