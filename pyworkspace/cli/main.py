"""PyWorkspace CLI — Typer-based command-line interface."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="pyworkspace",
    help="PyWorkspace — Enterprise Environment-as-a-Service CLI",
    no_args_is_help=True,
)
console = Console()


# ── Workspace commands ───────────────────────────────────────────────


@app.command()
def up(
    name: str = typer.Option(..., "--name", "-n", help="Workspace name"),
    template: Optional[str] = typer.Option(None, "--template", "-t", help="Template name"),
    spec: Optional[str] = typer.Option(None, "--spec", "-s", help="Path to spec YAML"),
    owner: str = typer.Option("cli-user", "--owner", help="Owner ID"),
    org: str = typer.Option("default", "--org", help="Organization ID"),
    tier: str = typer.Option("standard", "--tier", help="Tier: dev/standard/enterprise"),
) -> None:
    """Create and start a workspace."""
    import httpx

    console.print(f"[bold green]Creating workspace '{name}'...[/]")

    payload = {
        "name": name,
        "template": template,
        "owner_id": owner,
        "org_id": org,
        "tier": tier,
    }

    if spec:
        import yaml
        from pathlib import Path

        spec_data = yaml.safe_load(Path(spec).read_text())
        payload.update(spec_data)

    try:
        resp = httpx.post("http://localhost:8080/v1/workspaces", json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        console.print(f"[green]Workspace created:[/] {data.get('id', 'unknown')}")
        console.print(f"  Status: {data.get('status', 'unknown')}")
        console.print(f"  Namespace: {data.get('k8s_namespace', 'N/A')}")
        console.print(f"  DNS Zone: {data.get('dns_zone', 'N/A')}")
    except httpx.ConnectError:
        console.print("[red]Error: Cannot connect to PyWorkspace API at localhost:8080[/]")
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]Error: {e.response.text}[/]")
        raise typer.Exit(1)


@app.command()
def down(name: str = typer.Argument(..., help="Workspace name or ID")) -> None:
    """Destroy a workspace."""
    import httpx

    console.print(f"[bold red]Destroying workspace '{name}'...[/]")
    try:
        resp = httpx.delete(f"http://localhost:8080/v1/workspaces/{name}", timeout=30)
        resp.raise_for_status()
        console.print("[green]Workspace destruction initiated.[/]")
    except httpx.ConnectError:
        console.print("[red]Error: Cannot connect to PyWorkspace API[/]")
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]Error: {e.response.text}[/]")
        raise typer.Exit(1)


@app.command()
def status(name: str = typer.Argument(..., help="Workspace name or ID")) -> None:
    """Show workspace status."""
    import httpx

    try:
        resp = httpx.get(f"http://localhost:8080/v1/workspaces/{name}", timeout=10)
        resp.raise_for_status()
        data = resp.json()

        table = Table(title=f"Workspace: {data.get('name', name)}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("ID", data.get("id", ""))
        table.add_row("Status", data.get("status", ""))
        table.add_row("Tier", data.get("tier", ""))
        table.add_row("Namespace", data.get("k8s_namespace", ""))
        table.add_row("DNS Zone", data.get("dns_zone", ""))

        console.print(table)
    except httpx.ConnectError:
        console.print("[red]Error: Cannot connect to PyWorkspace API[/]")
        raise typer.Exit(1)
    except httpx.HTTPStatusError as e:
        console.print(f"[red]Error: {e.response.text}[/]")
        raise typer.Exit(1)


@app.command()
def services(name: str = typer.Argument(..., help="Workspace name or ID")) -> None:
    """List workspace services and their health."""
    import httpx

    try:
        resp = httpx.get(
            f"http://localhost:8080/v1/workspaces/{name}/services", timeout=10
        )
        resp.raise_for_status()
        data = resp.json()

        table = Table(title="Services")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="blue")
        table.add_column("Status", style="green")
        table.add_column("DNS", style="dim")

        for svc in data:
            table.add_row(
                svc.get("service_name", ""),
                svc.get("service_type", ""),
                svc.get("status", ""),
                svc.get("internal_dns", ""),
            )

        console.print(table)
    except httpx.ConnectError:
        console.print("[red]Error: Cannot connect to PyWorkspace API[/]")
        raise typer.Exit(1)


@app.command()
def pause(name: str = typer.Argument(..., help="Workspace name or ID")) -> None:
    """Pause a workspace."""
    import httpx

    try:
        resp = httpx.post(f"http://localhost:8080/v1/workspaces/{name}/pause", timeout=30)
        resp.raise_for_status()
        console.print(f"[green]Workspace '{name}' paused.[/]")
    except httpx.ConnectError:
        console.print("[red]Error: Cannot connect to PyWorkspace API[/]")
        raise typer.Exit(1)


@app.command()
def resume(name: str = typer.Argument(..., help="Workspace name or ID")) -> None:
    """Resume a paused workspace."""
    import httpx

    try:
        resp = httpx.post(f"http://localhost:8080/v1/workspaces/{name}/resume", timeout=30)
        resp.raise_for_status()
        console.print(f"[green]Workspace '{name}' resumed.[/]")
    except httpx.ConnectError:
        console.print("[red]Error: Cannot connect to PyWorkspace API[/]")
        raise typer.Exit(1)


@app.command()
def snapshot(
    name: str = typer.Argument(..., help="Workspace name or ID"),
    snapshot_name: str = typer.Option("manual", "--name", "-n", help="Snapshot name"),
) -> None:
    """Take a workspace snapshot."""
    import httpx

    try:
        resp = httpx.post(
            f"http://localhost:8080/v1/workspaces/{name}/snapshots",
            json={"name": snapshot_name},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        console.print(f"[green]Snapshot created: {data.get('id', '')}[/]")
    except httpx.ConnectError:
        console.print("[red]Error: Cannot connect to PyWorkspace API[/]")
        raise typer.Exit(1)


@app.command()
def restore(
    name: str = typer.Argument(..., help="Workspace name or ID"),
    snapshot_id: str = typer.Option(..., "--snapshot", help="Snapshot ID"),
) -> None:
    """Restore workspace from snapshot."""
    import httpx

    try:
        resp = httpx.post(
            f"http://localhost:8080/v1/workspaces/{name}/snapshots/{snapshot_id}/restore",
            timeout=60,
        )
        resp.raise_for_status()
        console.print(f"[green]Restore initiated from snapshot {snapshot_id}[/]")
    except httpx.ConnectError:
        console.print("[red]Error: Cannot connect to PyWorkspace API[/]")
        raise typer.Exit(1)


@app.command()
def clone(
    name: str = typer.Argument(..., help="Source workspace name or ID"),
    new_name: str = typer.Argument(..., help="New workspace name"),
) -> None:
    """Clone a workspace."""
    import httpx

    try:
        resp = httpx.post(
            f"http://localhost:8080/v1/workspaces/{name}/clone",
            params={"new_name": new_name},
            timeout=60,
        )
        resp.raise_for_status()
        console.print(f"[green]Cloning '{name}' to '{new_name}'...[/]")
    except httpx.ConnectError:
        console.print("[red]Error: Cannot connect to PyWorkspace API[/]")
        raise typer.Exit(1)


# ── Agent commands ───────────────────────────────────────────────────


agent_app = typer.Typer(name="agent", help="Agent management commands")
app.add_typer(agent_app)


@agent_app.command("run")
def agent_run(
    name: str = typer.Argument(..., help="Workspace name or ID"),
    prompt: str = typer.Argument(..., help="Prompt to send to agent"),
) -> None:
    """Send a task to the PyOz agent."""
    import httpx

    try:
        resp = httpx.post(
            f"http://localhost:8080/v1/workspaces/{name}/agent/execute",
            json={"prompt": prompt},
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        console.print(f"[green]Agent task submitted:[/] {data.get('status', '')}")
    except httpx.ConnectError:
        console.print("[red]Error: Cannot connect to PyWorkspace API[/]")
        raise typer.Exit(1)


@agent_app.command("status")
def agent_status(name: str = typer.Argument(..., help="Workspace name or ID")) -> None:
    """Get agent status."""
    import httpx

    try:
        resp = httpx.get(
            f"http://localhost:8080/v1/workspaces/{name}/agent/status", timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        console.print(f"Agent status: {data.get('agent_status', 'unknown')}")
    except httpx.ConnectError:
        console.print("[red]Error: Cannot connect to PyWorkspace API[/]")
        raise typer.Exit(1)


@agent_app.command("logs")
def agent_logs(
    name: str = typer.Argument(..., help="Workspace name or ID"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
) -> None:
    """Stream agent logs."""
    console.print(f"[dim]Agent logs for workspace '{name}'...[/]")
    console.print("[dim]Log streaming not yet implemented in CLI.[/]")


# ── Catalog commands ─────────────────────────────────────────────────


@app.command("catalog")
def catalog_list() -> None:
    """List available services in the catalog."""
    import httpx

    try:
        resp = httpx.get("http://localhost:8080/v1/catalog", timeout=10)
        resp.raise_for_status()
        data = resp.json()

        table = Table(title="Service Catalog")
        table.add_column("Type", style="cyan")
        table.add_column("Display Name", style="green")
        table.add_column("Categories", style="dim")
        table.add_column("Versions", style="blue")

        for svc in data:
            table.add_row(
                svc.get("type", ""),
                svc.get("display_name", ""),
                ", ".join(svc.get("categories", [])),
                ", ".join(svc.get("versions", [])[:3]),
            )

        console.print(table)
    except httpx.ConnectError:
        console.print("[red]Error: Cannot connect to PyWorkspace API[/]")
        raise typer.Exit(1)


@app.command("templates")
def templates_list() -> None:
    """List available workspace templates."""
    import httpx

    try:
        resp = httpx.get("http://localhost:8080/v1/templates", timeout=10)
        resp.raise_for_status()
        data = resp.json()

        table = Table(title="Workspace Templates")
        table.add_column("Name", style="cyan")
        table.add_column("Display Name", style="green")
        table.add_column("Category", style="blue")
        table.add_column("Description", style="dim")

        for tmpl in data:
            table.add_row(
                tmpl.get("name", ""),
                tmpl.get("display_name", ""),
                tmpl.get("category", ""),
                tmpl.get("description", "")[:60],
            )

        console.print(table)
    except httpx.ConnectError:
        console.print("[red]Error: Cannot connect to PyWorkspace API[/]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
