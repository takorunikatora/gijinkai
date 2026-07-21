"""Core humanization engine — language-aware AI fingerprint stripping.

Each language gets its own rules. No one-size-fits-all regex.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

# ═══════════════════════════════════════════════════════════════════════════
# Language rule sets
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class LangRules:
    """What to strip for a specific language."""

    name: str
    exts: tuple[str, ...]

    # Docstring / block-comment patterns
    block_doc_re: re.Pattern | None = None  # match the whole block
    ai_doc_starts: tuple[str, ...] = ()

    # Line comments
    line_comment_prefix: str = ""

    # AI boilerplate lines (exact match → drop line)
    drop_lines: tuple[re.Pattern, ...] = ()

    # Obvious comment patterns (strip comment, keep code)
    obvious_comment_re: re.Pattern | None = None

    # Divider / section separator patterns
    divider_re: re.Pattern | None = None

    # Inline pragmas to strip
    pragma_re: re.Pattern | None = None

    # Shebang to optionally strip
    shebang_re: re.Pattern | None = None

    # Type annotations (aggressive only)
    strip_type_hints: Callable[[str], str] | None = None


# ── Python ─────────────────────────────────────────────────────────────────

PYTHON_DOCSTRING_RE = re.compile(r'"""(.+?)"""', re.DOTALL)
PYTHON_SINGLE_DS_RE = re.compile(r"'''(.+?)'''", re.DOTALL)

PYTHON_AI_DOC_STARTS = (
    "This module provides",
    "This module implements",
    "This module contains",
    "Module for",
    "A module that",
    "The .+ module",
    "Core .+ engine",
    "Command-line interface for",
    "Entry point for",
    "Package metadata",
)

PYTHON_DROP_LINES = (
    re.compile(r"^\s*__all__\s*=\s*\[.*\]\s*$"),
    re.compile(r"^\s*from\s+__future__\s+import\s+annotations\s*$"),
)

PYTHON_OBVIOUS_COMMENTS = re.compile(
    r"#\s*("
    r"increment\s|initialize\s|return\s(the\s)?result|"
    r"call\s(the\s)?|set\s(the\s)?|get\s(the\s)?|"
    r"create\s(a\s|the\s|new\s)|check\s(if\s|whether\s)?|"
    r"loop\sthrough|iterate\s(through|over)|"
    r"this\s(function|method|class|module)\s(is|does|takes|returns|handles|provides|will|should)|"
    r"end\s(if|for|while|function|method|class)"
    r")",
    re.IGNORECASE,
)

PYTHON_DIVIDER_RE = re.compile(r"^\s*#\s*[─━═⬚▔▁▂▃▄▅▆▇█✂\-]{4,}\s*$")

PYTHON_PRAGMA_RE = re.compile(
    r"^\s*#\s*(type:\s*ignore|noqa|noinspection|nosec|pylint:.*)\s*$"
)

PYTHON_SHEBANG_RE = re.compile(r"^#!.*python")


def _strip_python_types(text: str) -> str:
    """Remove Python type annotations from function signatures."""
    # Return type: ) -> Type:
    text = re.sub(r"\)\s*->\s*[\w\[\], |.\"']+\s*:", "):", text)

    # Parameter types inside def signatures
    def _clean_params(match: re.Match) -> str:
        sig = match.group(0)
        return re.sub(r"(\w+)\s*:\s*[\w\[\], |.\"']+(?=\s*[,\)=])", r"\1", sig)

    text = re.sub(r"\b(?:async\s+)?def\s+\w+\([^)]*\)", _clean_params, text)
    return text


PYTHON = LangRules(
    name="Python",
    exts=(".py", ".pyw"),
    block_doc_re=PYTHON_DOCSTRING_RE,
    ai_doc_starts=PYTHON_AI_DOC_STARTS,
    line_comment_prefix="#",
    drop_lines=PYTHON_DROP_LINES,
    obvious_comment_re=PYTHON_OBVIOUS_COMMENTS,
    divider_re=PYTHON_DIVIDER_RE,
    pragma_re=PYTHON_PRAGMA_RE,
    shebang_re=PYTHON_SHEBANG_RE,
    strip_type_hints=_strip_python_types,
)

# ── JavaScript / TypeScript ────────────────────────────────────────────────

JS_BLOCK_DOC_RE = re.compile(r"/\*\*(.+?)\*/", re.DOTALL)

JS_AI_DOC_STARTS = (
    "This module provides",
    "This module implements",
    "A module that",
    "Module for",
    "@module",
    "@description",
    "@file",
)

JS_DROP_LINES = (
    re.compile(r"^\s*'use strict'\s*;?\s*$"),
    re.compile(r'^\s*"use strict"\s*;?\s*$'),
)

JS_OBVIOUS_COMMENTS = re.compile(
    r"//\s*("
    r"increment\s|initialize\s|return\s|call\s|set\s|get\s|create\s|"
    r"check\s|loop\s|iterate\s|this\sfunction\s|the\sfunction\s|"
    r"TODO|FIXME|HACK|"
    r"eslint-disable-line"
    r")",
    re.IGNORECASE,
)

JS_PRAGMA_RE = re.compile(
    r"^\s*//\s*(@ts-ignore|@ts-expect-error|eslint-disable[\w-]*|prettier-ignore)\s*$"
)

JS_DIVIDER_RE = re.compile(r"^\s*//\s*[─━═\-=]{4,}\s*$")

JS_SHEBANG_RE = re.compile(r"^#!.*node")


def _strip_ts_types(text: str) -> str:
    """Remove TS type annotations from function signatures."""
    # Return types
    text = re.sub(r"\)\s*:\s*[\w\[\]<>| &.,\"']+(?=\s*\{)", ") {", text)
    text = re.sub(r"\)\s*:\s*[\w\[\]<>| &.,\"']+\s*=>", ") =>", text)
    # Parameter types
    text = re.sub(
        r"(\w+)\s*:\s*(?:string|number|boolean|void|any|never|null|undefined|[\w\[\]<>| &.]+)(?=\s*[,\)=])",
        r"\1", text,
    )
    return text


JAVASCRIPT = LangRules(
    name="JavaScript",
    exts=(".js", ".mjs", ".cjs"),
    block_doc_re=JS_BLOCK_DOC_RE,
    ai_doc_starts=JS_AI_DOC_STARTS,
    line_comment_prefix="//",
    drop_lines=JS_DROP_LINES,
    obvious_comment_re=JS_OBVIOUS_COMMENTS,
    divider_re=JS_DIVIDER_RE,
    pragma_re=JS_PRAGMA_RE,
    shebang_re=JS_SHEBANG_RE,
)

TYPESCRIPT = LangRules(
    name="TypeScript",
    exts=(".ts", ".tsx", ".mts", ".cts"),
    block_doc_re=JS_BLOCK_DOC_RE,
    ai_doc_starts=JS_AI_DOC_STARTS,
    line_comment_prefix="//",
    drop_lines=JS_DROP_LINES,
    obvious_comment_re=JS_OBVIOUS_COMMENTS,
    divider_re=JS_DIVIDER_RE,
    pragma_re=JS_PRAGMA_RE,
    shebang_re=JS_SHEBANG_RE,
    strip_type_hints=_strip_ts_types,
)

# ── HTML ───────────────────────────────────────────────────────────────────

HTML_COMMENT_RE = re.compile(r"<!--(.+?)-->", re.DOTALL)

HTML_AI_COMMENT_STARTS = (
    "Section:",
    "BEGIN ",
    "END ",
    "Component:",
    "Template for",
    "This section",
    "Status Card",
    "Status",
    "Setup Form",
    "Setup",
    "Connected ",
    "Client List",
    "Clients",
    "QR Code",
    "QR",
    "Bandwidth",
    "Profile ",
    "Profiles",
    "Ban ",
    "Bans",
    "Toast ",
    "Error ",
    "Main ",
)

HTML_PRAGMA_RE = None
HTML_DIVIDER_RE = None
HTML_DROP_LINES: tuple = ()
HTML_OBVIOUS_COMMENTS = None

HTML = LangRules(
    name="HTML",
    exts=(".html", ".htm", ".xhtml"),
    block_doc_re=HTML_COMMENT_RE,
    ai_doc_starts=HTML_AI_COMMENT_STARTS,
    line_comment_prefix="<!--",
    drop_lines=HTML_DROP_LINES,
)

# ── CSS ────────────────────────────────────────────────────────────────────

CSS_COMMENT_RE = re.compile(r"/\*(.+?)\*/", re.DOTALL)

CSS_AI_COMMENT_STARTS = (
    "Section:",
    "Component:",
    "==========",
    "----------",
    "Typography",
    "Layout -",
    "Colors -",
    "Spacing -",
    "Variables",
    "Reset /",
    "Base styles",
    "Utility classes",
)

CSS_DROP_LINES = ()

CSS = LangRules(
    name="CSS",
    exts=(".css", ".scss", ".sass", ".less"),
    block_doc_re=CSS_COMMENT_RE,
    ai_doc_starts=CSS_AI_COMMENT_STARTS,
    line_comment_prefix="/*",
    drop_lines=CSS_DROP_LINES,
)

# ── Shell ──────────────────────────────────────────────────────────────────

SHELL_DOCSTRING_RE = None  # Shell has no docstrings

SHELL_AI_DOC_STARTS: tuple[str, ...] = ()

SHELL_DROP_LINES = (
    re.compile(r"^\s*set\s+[-+]euo\s+pipefail\s*$"),  # keep? remove comment above it
)

SHELL_OBVIOUS_COMMENTS = re.compile(
    r"#\s*("
    r"check\s|ensure\s|verify\s|make\ssure\s|"
    r"if\s.*exists|if\s.*installed|"
    r"set\s.*options|configure\s|"
    r"TODO|FIXME|HACK"
    r")",
    re.IGNORECASE,
)

SHELL_DIVIDER_RE = re.compile(r"^\s*#\s*[─━═\-=]{4,}\s*$")

SHELL_SHEBANG_RE = re.compile(r"^#!.*(bash|sh|zsh|dash)")

SHELL = LangRules(
    name="Shell",
    exts=(".sh", ".bash", ".zsh", ".ksh"),
    block_doc_re=SHELL_DOCSTRING_RE,
    ai_doc_starts=SHELL_AI_DOC_STARTS,
    line_comment_prefix="#",
    drop_lines=SHELL_DROP_LINES,
    obvious_comment_re=SHELL_OBVIOUS_COMMENTS,
    divider_re=SHELL_DIVIDER_RE,
    shebang_re=SHELL_SHEBANG_RE,
)

# ── Rule lookup ────────────────────────────────────────────────────────────

LANG_RULES: dict[str, LangRules] = {}
for rules in (PYTHON, JAVASCRIPT, TYPESCRIPT, HTML, CSS, SHELL):
    for ext in rules.exts:
        LANG_RULES[ext] = rules


def rules_for(path: Path) -> LangRules | None:
    """Get the language rules for a file path."""
    return LANG_RULES.get(path.suffix)


# ═══════════════════════════════════════════════════════════════════════════
# Common patterns (cross-language)
# ═══════════════════════════════════════════════════════════════════════════

TRAILING_WS_RE = re.compile(r"[ \t]+$", re.MULTILINE)
MULTI_BLANK_RE = re.compile(r"\n{3,}")  # 3+ blank lines → 2

# Module/class variable annotations:  __version__ = "0.1.0"
# Not always AI, but extremely common in AI boilerplate templates
VERSION_ASSIGN_RE = re.compile(r'^\s*__version__\s*=\s*"[^"]*"\s*$')
AUTHOR_ASSIGN_RE = re.compile(r'^\s*__author__\s*=\s*"[^"]*"\s*$')


# ═══════════════════════════════════════════════════════════════════════════
# Mode
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class Mode:
    remove_docstrings: bool = True
    remove_obvious_comments: bool = True
    remove_pragmas: bool = True
    remove_dividers: bool = True
    remove_type_hints: bool = False
    remove_shebangs: bool = False
    remove_version_author: bool = False
    normalize_whitespace: bool = True


def mode_light() -> Mode:
    return Mode(
        remove_docstrings=False,
        remove_obvious_comments=False,
        remove_pragmas=False,
        remove_dividers=False,
        normalize_whitespace=True,
    )


def mode_medium() -> Mode:
    return Mode()


def mode_aggressive() -> Mode:
    return Mode(
        remove_type_hints=True,
        remove_shebangs=True,
        remove_version_author=True,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Pipeline
# ═══════════════════════════════════════════════════════════════════════════


def _strip_block_docs(text: str, rules: LangRules) -> str:
    """Remove AI-style docstrings / block comments."""
    if rules.block_doc_re is None or not rules.ai_doc_starts:
        return text

    start_re = re.compile(
        "|".join(f"(?:{s})" for s in rules.ai_doc_starts),
        re.IGNORECASE,
    )

    def _should_strip(match: re.Match) -> bool:
        body = match.group(1).strip()
        first_line = body.split("\n")[0].strip()
        if start_re.match(first_line):
            return True
        # Multi-paragraph verbose block = likely AI
        if body.count("\n") >= 3 and len(body) > 200:
            return True
        return False

    def _replacer(match: re.Match) -> str:
        return "" if _should_strip(match) else match.group(0)

    return rules.block_doc_re.sub(_replacer, text)


def _strip_line(line: str, rules: LangRules, mode: Mode) -> str | None:
    """Process one line. Return processed line or None to drop."""
    stripped = line.rstrip()

    # Drop-lines (__all__, __future__, 'use strict')
    for pat in rules.drop_lines:
        if pat.match(stripped):
            return None

    # Pragmas — whole-line (drop line) or inline (strip suffix)
    if mode.remove_pragmas and rules.pragma_re:
        if rules.pragma_re.match(stripped):
            # Whole line is a pragma → drop
            return None
        # Inline pragma (code followed by pragma comment)
        # e.g. "foo(); // eslint-disable-line" → "foo();"
        if rules.line_comment_prefix:
            prefix = rules.line_comment_prefix
            # Find the last comment on the line
            idx = stripped.rfind(prefix)
            if idx >= 0:
                comment_part = stripped[idx:]
                if rules.pragma_re.match(comment_part.strip()):
                    before = stripped[:idx].rstrip()
                    return before if before else None

    # Dividers
    if mode.remove_dividers and rules.divider_re:
        if rules.divider_re.match(stripped):
            return None

    # Shebang
    if mode.remove_shebangs and rules.shebang_re:
        if rules.shebang_re.match(stripped):
            return None

    # Version / author boilerplate
    if mode.remove_version_author:
        if VERSION_ASSIGN_RE.match(stripped):
            return None
        if AUTHOR_ASSIGN_RE.match(stripped):
            return None

    # Obvious comment — strip comment, keep code before it
    if mode.remove_obvious_comments and rules.obvious_comment_re:
        if rules.obvious_comment_re.search(stripped):
            prefix = rules.line_comment_prefix
            if prefix and prefix in stripped:
                idx = stripped.index(prefix)
                before = stripped[:idx].rstrip()
                return before if before else None

    return stripped


def gijinkai(text: str, rules: LangRules, mode: Mode) -> str:
    """Run language-aware humanization pipeline."""

    # Phase 1: strip AI block docs
    if mode.remove_docstrings:
        text = _strip_block_docs(text, rules)

    # Phase 2: line-by-line processing
    lines = text.split("\n")
    kept: list[str] = []
    for line in lines:
        result = _strip_line(line, rules, mode)
        if result is not None:
            kept.append(result)

    text = "\n".join(kept)

    # Phase 3: type hints (aggressive)
    if mode.remove_type_hints and rules.strip_type_hints:
        text = rules.strip_type_hints(text)

    # Phase 4: whitespace
    if mode.normalize_whitespace:
        text = TRAILING_WS_RE.sub("", text)
        text = MULTI_BLANK_RE.sub("\n\n", text)

    # Phase 5: strip trailing blank lines, ensure one trailing newline
    text = text.rstrip("\n") + "\n"

    return text


def gijinkai_file(path: Path, mode: Mode | None = None) -> str:
    """Gijinkai a single file. Auto-detects language."""
    if mode is None:
        mode = mode_medium()

    rules = rules_for(path)
    if rules is None:
        return path.read_text(encoding="utf-8")  # unsupported lang → pass through

    text = path.read_text(encoding="utf-8")
    return gijinkai(text, rules, mode)


def gijinkai_directory(
    root: Path,
    mode: Mode | None = None,
    in_place: bool = False,
    dry_run: bool = False,
) -> list[tuple[Path, int, int, str]]:
    """Gijinkai all matching files. Returns [(path, orig_bytes, new_bytes, lang), ...]."""
    if mode is None:
        mode = mode_medium()

    results: list[tuple[Path, int, int, str]] = []

    for ext, rules in LANG_RULES.items():
        for fpath in root.rglob(f"**/*{ext}"):
            rel = fpath.relative_to(root)
            if any(part.startswith(".") for part in rel.parts[:-1]):
                continue

            orig = fpath.read_text(encoding="utf-8")
            new = gijinkai(orig, rules, mode)

            if new != orig:
                results.append((fpath, len(orig), len(new), rules.name))
                if in_place and not dry_run:
                    fpath.write_text(new, encoding="utf-8")

    return results
