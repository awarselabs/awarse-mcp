"""SeatPrune Typer CLI for SaaS spend governance and license reclamation."""

import asyncio
import os
from pathlib import Path
from typing import Annotated, Any

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from seatprune.config import settings
from seatprune.connectors.github import GitHubConnector
from seatprune.engine.evaluator import InactivityEvaluator
from seatprune.engine.reclaimer import SeatReclaimer
from seatprune.notifier.slack import SlackNotifier

app = typer.Typer(
    name="seatprune",
    help="SeatPrune: Autonomous SaaS license reclamation and spend governance CLI.",
    add_completion=False,
)

console = Console()


def _load_config_and_resolve(
    config_path: Path | None,
    cli_org: str | None,
    cli_threshold: int | None,
) -> tuple[str, int, dict[str, Any]]:
    """Loads optional YAML config and resolves org, threshold, and exemption allowlist."""
    cfg_data: dict[str, Any] = {}
    if config_path and config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg_data = yaml.safe_load(f) or {}
        except Exception as e:
            console.print(f"[bold red]Error reading config file {config_path}: {e}[/bold red]")

    config_org = None
    if isinstance(cfg_data, dict):
        config_org = cfg_data.get("providers", {}).get("github", {}).get("org")

    resolved_org = cli_org or config_org or settings.github_org

    config_threshold = None
    if isinstance(cfg_data, dict):
        config_threshold = cfg_data.get("thresholds", {}).get("inactive_days")

    resolved_threshold = (
        cli_threshold
        if cli_threshold is not None
        else (config_threshold if config_threshold is not None else settings.inactivity_threshold_days)
    )

    if isinstance(cfg_data, dict):
        exempt_users = cfg_data.get("exemptions", {}).get("users", [])
        if isinstance(exempt_users, list):
            for u in exempt_users:
                if u and isinstance(u, str) and u not in settings.safe_user_allowlist:
                    settings.safe_user_allowlist.append(u)

        token_env = cfg_data.get("providers", {}).get("github", {}).get("token_env")
        if token_env and os.getenv(token_env):
            settings.github_token = os.getenv(token_env)

    return resolved_org, resolved_threshold, cfg_data


@app.command(name="scan", help="Scan organization user activity and identify zombie seats.")
def scan_command(
    org: Annotated[str | None, typer.Argument(help="Target GitHub organization name")] = None,
    config: Annotated[Path | None, typer.Option("--config", "-c", help="Path to configuration YAML file")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run/--no-dry-run", help="Run in safety dry-run mode")] = True,
    threshold: Annotated[int | None, typer.Option("--threshold", "-t", help="Inactivity threshold in days")] = None,
    format: Annotated[str, typer.Option("--format", "-f", help="Output format: table, markdown, json")] = "table",
):
    """Scans organization SaaS seats and prints zombie license analysis."""
    resolved_org, resolved_threshold, cfg_data = _load_config_and_resolve(config, org, threshold)
    fmt = format.lower()

    if fmt == "table":
        mode_str = " (dry-run)" if dry_run else ""
        console.print(
            f"[bold cyan]🔍 SeatPrune Audit Scan[/bold cyan] for organization [yellow]{resolved_org}[/yellow] (threshold={resolved_threshold} days){mode_str}..."
        )

    async def _scan():
        connector = GitHubConnector(org=resolved_org)
        evaluator = InactivityEvaluator(threshold_days=resolved_threshold)

        users = await connector.list_organization_users()
        report = evaluator.evaluate_users(resolved_org, users)
        plan = evaluator.generate_reclamation_plan(resolved_org, users, dry_run=dry_run)

        if fmt in ("markdown", "md"):
            md_lines = [
                f"# 🔍 SeatPrune FinOps Audit Scan: {resolved_org}",
                f"**Inactivity Threshold:** {resolved_threshold} days | **Mode:** {'Dry-Run' if dry_run else 'Live'}\n",
                "## Zombie / Reclaimable Seats",
                "| Username | Seat Type | Days Inactive | Monthly Cost | Rationale |",
                "| --- | --- | --- | --- | --- |",
            ]
            for target in plan.targets:
                md_lines.append(
                    f"| `{target.username}` | {target.seat_type.value} | {target.days_inactive} | ${target.monthly_cost:.2f} | {target.rationale} |"
                )
            if not plan.targets:
                md_lines.append("| _None_ | _None_ | 0 | $0.00 | No zombie seats detected |")

            md_lines.extend([
                "",
                "## 💰 FinOps Spend Summary",
                f"- **Monthly Spend Recovery:** ${plan.total_monthly_savings:,.2f}/mo",
                f"- **Annualized Spend Recovery:** ${plan.total_annual_savings:,.2f}/yr",
                f"- **Zombie Seats Identified:** {len(plan.targets)} of {report.total_users} total users",
            ])
            print("\n".join(md_lines))

        elif fmt == "json":
            import json
            out = {
                "organization": resolved_org,
                "threshold_days": resolved_threshold,
                "dry_run": dry_run,
                "total_users": report.total_users,
                "zombie_seats": len(plan.targets),
                "total_monthly_savings": plan.total_monthly_savings,
                "total_annual_savings": plan.total_annual_savings,
                "targets": [
                    {
                        "username": t.username,
                        "seat_type": t.seat_type.value,
                        "days_inactive": t.days_inactive,
                        "monthly_cost": t.monthly_cost,
                        "rationale": t.rationale,
                    }
                    for t in plan.targets
                ],
            }
            print(json.dumps(out, indent=2))

        else:
            table = Table(title=f"SeatPrune Audit Results: {resolved_org}", border_style="cyan")
            table.add_column("Username", style="bold white")
            table.add_column("Seat Type", style="magenta")
            table.add_column("Days Inactive", justify="right", style="yellow")
            table.add_column("Monthly Cost", justify="right", style="green")
            table.add_column("Status / Rationale", style="dim")

            for target in plan.targets:
                table.add_row(
                    target.username,
                    target.seat_type.value,
                    str(target.days_inactive),
                    f"${target.monthly_cost:.2f}",
                    target.rationale,
                )

            console.print(table)

            summary_panel = Panel(
                f"[bold green]Monthly Spend Recovery:[/bold green] ${plan.total_monthly_savings:,.2f}/mo\n"
                f"[bold green]Annualized Spend Recovery:[/bold green] ${plan.total_annual_savings:,.2f}/yr\n"
                f"[bold yellow]Zombie Seats Identified:[/bold yellow] {len(plan.targets)} of {report.total_users} total users",
                title="💰 FinOps Spend Summary",
                border_style="green",
            )
            console.print(summary_panel)

    asyncio.run(_scan())


@app.command(name="notify", help="Dispatch Slack webhook alert for pending license reclamation plan.")
def notify_command(
    org: Annotated[str | None, typer.Argument(help="Target GitHub organization name")] = None,
    config: Annotated[Path | None, typer.Option("--config", "-c", help="Path to configuration YAML file")] = None,
    webhook_url: Annotated[str | None, typer.Option("--webhook", "-w", help="Slack webhook URL override")] = None,
):
    """Generates reclamation plan and sends Slack check-in notification."""
    resolved_org, resolved_threshold, cfg_data = _load_config_and_resolve(config, org, None)
    console.print(f"[bold cyan]🔔 Dispatching Slack Alert[/bold cyan] for org [yellow]{resolved_org}[/yellow]...")

    async def _notify():
        connector = GitHubConnector(org=resolved_org)
        evaluator = InactivityEvaluator(threshold_days=resolved_threshold)
        notifier = SlackNotifier(webhook_url=webhook_url)

        users = await connector.list_organization_users()
        plan = evaluator.generate_reclamation_plan(resolved_org, users)

        sent = await notifier.send_alert(plan)
        if sent:
            console.print(f"[bold green]✔ Successfully dispatched Slack alert for {len(plan.targets)} zombie seats![/bold green]")
        else:
            console.print("[bold yellow]⚠️ Slack alert dispatch skipped or failed (check webhook URL configuration).[/bold yellow]")

    asyncio.run(_notify())


@app.command(name="prune", help="Execute seat reclamation with dry-run safety locks.")
def prune_command(
    org: Annotated[str | None, typer.Argument(help="Target GitHub organization name")] = None,
    config: Annotated[Path | None, typer.Option("--config", "-c", help="Path to configuration YAML file")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run/--no-dry-run", help="Safety guard toggle")] = True,
):
    """Executes license revocations and seat downgrades."""
    resolved_org, resolved_threshold, cfg_data = _load_config_and_resolve(config, org, None)
    mode_tag = "[bold yellow]DRY-RUN[/bold yellow]" if dry_run else "[bold red]LIVE DE-PROVISIONING[/bold red]"
    console.print(f"[bold cyan]✂️ SeatPrune Pruning Engine[/bold cyan] ({mode_tag}) for org [yellow]{resolved_org}[/yellow]...")

    async def _prune():
        connector = GitHubConnector(org=resolved_org)
        evaluator = InactivityEvaluator(threshold_days=resolved_threshold)
        reclaimer = SeatReclaimer(connectors={"github": connector})

        users = await connector.list_organization_users()
        plan = evaluator.generate_reclamation_plan(resolved_org, users, dry_run=dry_run)
        results = await reclaimer.execute_plan(plan, dry_run=dry_run)

        table = Table(title=f"Pruning Execution Log ({'DRY-RUN' if dry_run else 'LIVE'})", border_style="magenta")
        table.add_column("Username", style="bold white")
        table.add_column("Seat Type", style="cyan")
        table.add_column("Status", style="bold green")
        table.add_column("Execution Message")

        for res in results:
            status_str = "[green]SUCCESS[/green]" if res.success else "[red]FAILED[/red]"
            table.add_row(res.username, res.seat_type.value, status_str, res.message)

        console.print(table)

    asyncio.run(_prune())


@app.command(name="report", help="Display full FinOps audit report of organization SaaS spend.")
def report_command(
    org: Annotated[str | None, typer.Argument(help="Target GitHub organization name")] = None,
    config: Annotated[Path | None, typer.Option("--config", "-c", help="Path to configuration YAML file")] = None,
):
    """Prints comprehensive SaaS activity and spend breakdown."""
    resolved_org, resolved_threshold, cfg_data = _load_config_and_resolve(config, org, None)
    console.print(f"[bold cyan]📊 FinOps Audit Report[/bold cyan] for [yellow]{resolved_org}[/yellow]...")

    async def _report():
        connector = GitHubConnector(org=resolved_org)
        evaluator = InactivityEvaluator(threshold_days=resolved_threshold)

        users = await connector.list_organization_users()
        report = evaluator.evaluate_users(resolved_org, users)

        console.print(
            Panel(
                f"[bold]Organization:[/bold] {report.organization}\n"
                f"[bold]Evaluation Date:[/bold] {report.evaluation_date}\n"
                f"[bold]Inactivity Limit:[/bold] {report.threshold_days} days\n"
                f"[bold]Total Assigned Seats:[/bold] {report.total_users}\n"
                f"[bold green]Active Seats:[/bold green] {report.active_users}\n"
                f"[bold red]Zombie Seats:[/bold red] {report.inactive_users}\n"
                f"[bold red]Monthly Spend Leakage:[/bold red] ${report.monthly_wasted_spend:,.2f}\n"
                f"[bold red]Annual Spend Leakage:[/bold red] ${report.annual_wasted_spend:,.2f}",
                title="SeatPrune FinOps Report",
                border_style="cyan",
            )
        )

    asyncio.run(_report())


if __name__ == "__main__":
    app()

