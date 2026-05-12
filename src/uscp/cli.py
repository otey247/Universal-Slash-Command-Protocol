"""USCP command-line interface.

Entry point: ``uscp``
"""

from __future__ import annotations

import pathlib
import sys
from typing import Optional

import click
import yaml
from rich.console import Console
from rich.table import Table

from uscp import compiler as comp
from uscp import validator as val
from uscp.compiler import list_targets
from uscp.registry import CommandRegistry

console = Console()
err_console = Console(stderr=True)


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------


@click.group()
@click.version_option(package_name="uscp")
def main() -> None:
    """Universal Slash Command Protocol CLI.

    Discover, validate, and compile portable agent workflow commands.
    """


# ---------------------------------------------------------------------------
# uscp validate
# ---------------------------------------------------------------------------


@main.command("validate")
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--dir",
    "search_dir",
    type=click.Path(exists=True, file_okay=False),
    default=None,
    help="Validate all *.yaml manifests in this directory.",
)
def validate_cmd(paths: tuple[str, ...], search_dir: Optional[str]) -> None:
    """Validate one or more USCP command manifests.

    Provide either explicit PATHS to manifest files, or use --dir to validate
    all *.yaml files in a directory.
    """
    files: list[pathlib.Path] = []

    if search_dir:
        files.extend(sorted(pathlib.Path(search_dir).glob("*.yaml")))

    for p in paths:
        files.append(pathlib.Path(p))

    if not files:
        err_console.print("[yellow]No manifest files specified.[/yellow]")
        sys.exit(1)

    all_ok = True
    for path in files:
        errors = val.validate_file(path)
        if errors:
            all_ok = False
            err_console.print(f"[red]✗[/red] {path}")
            for e in errors:
                err_console.print(f"  [red]•[/red] {e}")
        else:
            console.print(f"[green]✓[/green] {path}")

    if not all_ok:
        sys.exit(1)


# ---------------------------------------------------------------------------
# uscp list
# ---------------------------------------------------------------------------


@main.command("list")
@click.option(
    "--root",
    default=".",
    show_default=True,
    help="Project root to search for commands.",
)
def list_cmd(root: str) -> None:
    """List all discovered USCP commands in the current project."""
    registry = CommandRegistry(root)
    count = registry.discover()

    if count == 0:
        console.print("[yellow]No commands found.[/yellow]")
        return

    table = Table(title=f"USCP Commands ({count} found)", show_lines=True)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Version", style="dim")
    table.add_column("Title")
    table.add_column("Mode", style="yellow")
    table.add_column("Description")

    for manifest in registry.list_commands():
        mode = manifest.get("execution", {}).get("mode", "—")
        table.add_row(
            f"/{manifest['name']}",
            manifest.get("version", "?"),
            manifest.get("title", ""),
            mode,
            manifest.get("description", ""),
        )

    console.print(table)


# ---------------------------------------------------------------------------
# uscp compile
# ---------------------------------------------------------------------------


@main.command("compile")
@click.option(
    "--target",
    "-t",
    required=True,
    type=click.Choice(list_targets(), case_sensitive=False),
    help="Target tool to compile for.",
)
@click.option(
    "--output",
    "-o",
    default="dist",
    show_default=True,
    help="Output directory for compiled files.",
)
@click.option(
    "--root",
    default=".",
    show_default=True,
    help="Project root to discover commands from.",
)
@click.argument("names", nargs=-1)
def compile_cmd(target: str, output: str, root: str, names: tuple[str, ...]) -> None:
    """Compile USCP commands to a tool-specific format.

    Optionally provide command NAMES to compile only specific commands.
    If no names are given, all discovered commands are compiled.
    """
    registry = CommandRegistry(root)
    registry.discover()

    manifests: list[dict] = []
    if names:
        for name in names:
            manifest = registry.resolve(name)
            if manifest is None:
                err_console.print(f"[red]Command not found:[/red] {name}")
                sys.exit(1)
            manifests.append(manifest)
    else:
        manifests = registry.list_commands()

    if not manifests:
        console.print("[yellow]No commands to compile.[/yellow]")
        return

    results = comp.compile_manifests(manifests, target, output)

    all_ok = True
    for result in results:
        if result.success:
            console.print(
                f"[green]✓[/green] Compiled [cyan]/{result.command_name}[/cyan] "
                f"→ {result.output_path}"
            )
        else:
            all_ok = False
            err_console.print(
                f"[red]✗[/red] Failed [cyan]/{result.command_name}[/cyan]: {result.error}"
            )

    if not all_ok:
        sys.exit(1)


# ---------------------------------------------------------------------------
# uscp install
# ---------------------------------------------------------------------------


@main.command("install")
@click.argument("source", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--dest",
    default=".agent/commands",
    show_default=True,
    help="Destination directory for installed command manifests.",
)
def install_cmd(source: str, dest: str) -> None:
    """Install USCP command manifests from SOURCE directory into the project.

    SOURCE should be a directory of *.yaml manifest files.
    Manifests are validated before installation.
    """
    src = pathlib.Path(source)
    dst = pathlib.Path(dest)
    dst.mkdir(parents=True, exist_ok=True)

    yaml_files = sorted(src.glob("*.yaml"))
    if not yaml_files:
        console.print(f"[yellow]No *.yaml files found in {src}[/yellow]")
        return

    installed = 0
    skipped = 0
    for yaml_file in yaml_files:
        errors = val.validate_file(yaml_file)
        if errors:
            err_console.print(f"[red]✗[/red] Skipping {yaml_file.name} (validation failed):")
            for e in errors:
                err_console.print(f"  [red]•[/red] {e}")
            skipped += 1
            continue

        target_path = dst / yaml_file.name
        target_path.write_bytes(yaml_file.read_bytes())
        console.print(f"[green]✓[/green] Installed {yaml_file.name} → {target_path}")
        installed += 1

    console.print(f"\nInstalled [green]{installed}[/green] commands, skipped [yellow]{skipped}[/yellow].")


# ---------------------------------------------------------------------------
# uscp show
# ---------------------------------------------------------------------------


@main.command("show")
@click.argument("name")
@click.option(
    "--root",
    default=".",
    show_default=True,
    help="Project root to search.",
)
def show_cmd(name: str, root: str) -> None:
    """Show details of a specific USCP command."""
    registry = CommandRegistry(root)
    registry.discover()

    # Strip leading slash if the user typed /command-name
    name = name.lstrip("/")
    manifest = registry.resolve(name)
    if manifest is None:
        err_console.print(f"[red]Command not found:[/red] {name}")
        sys.exit(1)

    console.print(f"\n[bold cyan]/{manifest['name']}[/bold cyan]  v{manifest.get('version', '?')}")
    console.print(f"[italic]{manifest.get('description', '')}[/italic]")
    console.print()

    # Arguments
    props = manifest.get("arguments", {}).get("properties", {})
    required = manifest.get("arguments", {}).get("required", [])
    if props:
        table = Table(title="Arguments", show_lines=True)
        table.add_column("Argument", style="cyan")
        table.add_column("Type")
        table.add_column("Required")
        table.add_column("Description")
        for arg_name, arg_def in props.items():
            req = "[green]yes[/green]" if arg_name in required else "no"
            desc = arg_def.get("description", "")
            enum_vals = arg_def.get("enum")
            if enum_vals:
                desc += f"\nAllowed: {', '.join(str(v) for v in enum_vals)}"
            table.add_row(f"--{arg_name}", arg_def.get("type", "string"), req, desc)
        console.print(table)

    # Workflow
    steps = manifest.get("workflow", {}).get("steps", [])
    if steps:
        console.print("\n[bold]Workflow Steps[/bold]")
        for i, step in enumerate(steps, 1):
            console.print(f"  [dim]{i}.[/dim] [yellow]{step['id']}[/yellow]")

    # Examples
    examples = manifest.get("examples", [])
    if examples:
        console.print("\n[bold]Examples[/bold]")
        for ex in examples:
            console.print(f"  [dim]$[/dim] {ex}")

    console.print()


if __name__ == "__main__":
    main()
