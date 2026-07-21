"""gijinkai CLI — language-aware AI fingerprint stripping."""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from gijinkai.core import (
    Mode,
    mode_light,
    mode_medium,
    mode_aggressive,
    gijinkai_file,
    gijinkai_directory,
    rules_for,
    LANG_RULES,
)
from gijinkai import __version__

app = typer.Typer(
    name="gijinkai",
    help="Strip AI fingerprints from source code — per-language, per-extension.",
    no_args_is_help=True,
)
console = Console()


def _pick_mode(light: bool, aggressive: bool) -> Mode:
    if aggressive:
        return mode_aggressive()
    if light:
        return mode_light()
    return mode_medium()


@app.command()
def file(
    path: str = typer.Argument(..., help="Path to a source file"),
    light: bool = typer.Option(False, "--light", "-l", help="Whitespace only"),
    aggressive: bool = typer.Option(
        False, "--aggressive", "-a", help="Remove type hints too"
    ),
    write: bool = typer.Option(
        False, "--write", "-w", help="Overwrite file in place"
    ),
):
    """Gijinkai a single file. Prints to stdout unless --write."""
    mode = _pick_mode(light, aggressive)
    fpath = Path(path).resolve()

    if not fpath.exists():
        console.print(f"[red]File not found:[/red] {path}")
        raise typer.Exit(1)

    rules = rules_for(fpath)
    if rules is None:
        console.print(f"[yellow]Unsupported file type:[/yellow] {fpath.suffix}")
        console.print(
            f"Supported: {', '.join(sorted(set(r.name for r in LANG_RULES.values())))}"
        )
        raise typer.Exit(1)

    from gijinkai.core import gijinkai

    text = fpath.read_text(encoding="utf-8")
    result = gijinkai(text, rules, mode)

    if write:
        if result != text:
            fpath.write_text(result, encoding="utf-8")
            console.print(f"[green]✓[/green] Wrote {fpath} ({rules.name})")
        else:
            console.print("[dim]No changes needed.[/dim]")
    else:
        sys.stdout.write(result)


@app.command()
def dir(
    path: str = typer.Argument(".", help="Directory to scan"),
    light: bool = typer.Option(False, "--light", "-l"),
    aggressive: bool = typer.Option(False, "--aggressive", "-a"),
    write: bool = typer.Option(
        False, "--write", "-w", help="Overwrite files in place"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Preview changes without writing"
    ),
):
    """Gijinkai all supported files under a directory."""
    mode = _pick_mode(light, aggressive)
    root = Path(path).resolve()

    if not root.is_dir():
        console.print(f"[red]Not a directory:[/red] {path}")
        raise typer.Exit(1)

    results = gijinkai_directory(root, mode, in_place=write, dry_run=dry_run)

    if not results:
        console.print("[dim]All clean — nothing to change.[/dim]")
        return

    # Group by language
    table = Table(title=f"Gijinkai — {len(results)} file(s)")
    table.add_column("File", style="cyan")
    table.add_column("Lang", width=12)
    table.add_column("Before", justify="right", style="dim")
    table.add_column("After", justify="right", style="green")
    table.add_column("Δ", justify="right", style="yellow")

    total_before = 0
    total_after = 0
    for fpath, before, after, lang in results:
        rel = fpath.relative_to(root)
        delta = before - after
        total_before += before
        total_after += after
        table.add_row(
            str(rel),
            lang,
            f"{before:,}B",
            f"{after:,}B",
            f"-{delta:,}B",
        )

    console.print(table)

    if total_before:
        pct = (total_before - total_after) / total_before * 100
        console.print(
            f"\n[bold]{total_before:,}B → {total_after:,}B[/bold]  "
            f"[dim](-{total_before - total_after:,}B / {pct:.1f}%)[/dim]"
        )

    if dry_run:
        console.print("\n[yellow]Dry run — no files modified.[/yellow]")
        console.print("Run with [bold]--write[/bold] to apply changes.")


@app.command()
def langs():
    """List supported languages and their file extensions."""
    seen: dict[str, list[str]] = {}
    for ext, rules in LANG_RULES.items():
        seen.setdefault(rules.name, []).append(ext)

    for name, exts in sorted(seen.items()):
        console.print(f"[bold]{name}[/bold]  [dim]{' '.join(exts)}[/dim]")


@app.command()
def version():
    """Print version."""
    console.print(f"gijinkai v{__version__}")


@app.command()
def gui():
    """Launch the desktop GUI."""
    from gijinkai.gui import launch_gui
    launch_gui()


if __name__ == "__main__":
    app()
