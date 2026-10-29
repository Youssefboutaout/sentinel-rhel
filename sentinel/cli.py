import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from sentinel.core.system import get_system_summary
from sentinel.core.lvm import get_volume_groups, get_logical_volumes, auto_heal_lvs

app = typer.Typer(help="Sentinel-RHEL: Autonomous Linux & LVM Self-Healing CLI")
console = Console()


@app.callback()
def main():
    """Sentinel-RHEL: Autonomous Linux Infrastructure & Storage Platform."""
    pass


@app.command()
def status(threshold: float = typer.Option(80.0, "--threshold", "-t", help="Warning threshold %")):
    """Display live RHEL 10 system health, security posture, and LVM topology."""
    sys_info = get_system_summary()

    summary_text = (
        f"[bold cyan]Hostname:[/bold cyan] {sys_info['hostname']}   "
        f"[bold cyan]Kernel:[/bold cyan] {sys_info['kernel']}\n"
        f"[bold cyan]CPU:[/bold cyan] {sys_info['cpu_cores']} vCPUs ({sys_info['cpu_usage']})   "
        f"[bold cyan]RAM:[/bold cyan] {sys_info['ram_usage']}\n"
        f"[bold cyan]SELinux:[/bold cyan] [green]{sys_info['selinux']}[/green]   "
        f"[bold cyan]Firewalld:[/bold cyan] [green]{sys_info['firewalld']}[/green]"
    )
    console.print(Panel(summary_text, title="🛡️ Sentinel-RHEL v0.1.0 — System Telemetry", border_style="bright_blue"))

    vg_table = Table(title="LVM Volume Groups (VGs)", header_style="bold magenta")
    vg_table.add_column("VG Name", style="cyan")
    vg_table.add_column("PV Count", justify="center")
    vg_table.add_column("LV Count", justify="center")
    vg_table.add_column("Total Size", justify="right")
    vg_table.add_column("Free Space (Auto-Heal Pool)", justify="right", style="bold green")

    for vg in get_volume_groups():
        vg_table.add_row(vg["vg_name"], vg["pv_count"], vg["lv_count"], vg["vg_size"], vg["vg_free"])
    console.print(vg_table)

    lv_table = Table(title="LVM Logical Volumes (LVs)", header_style="bold yellow")
    lv_table.add_column("LV Name", style="cyan")
    lv_table.add_column("VG Name")
    lv_table.add_column("Size", justify="right")
    lv_table.add_column("Filesystem", justify="center")
    lv_table.add_column("Mount Point")
    lv_table.add_column("Used %", justify="right", style="bold")

    for lv in get_logical_volumes():
        usage_str = lv["usage"]
        if lv["usage_val"] >= threshold:
            usage_str = f"[bold red]⚠️ {usage_str}[/bold red]"
        elif lv["usage_val"] > 0:
            usage_str = f"[green]{usage_str}[/green]"
        lv_table.add_row(lv["lv_name"], lv["vg_name"], lv["size"], lv["fstype"], lv["mountpoint"], usage_str)
    console.print(lv_table)


@app.command()
def heal(
    threshold: float = typer.Option(80.0, "--threshold", "-t", help="Usage % trigger for auto-extension"),
    extend_mb: int = typer.Option(512, "--extend-mb", "-e", help="Size in MiB to add when healing"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulate healing without modifying LVM")
):
    """Automatically detect and extend Logical Volumes exceeding capacity threshold."""
    console.print(f"[bold cyan]🔍 Scanning Logical Volumes (Threshold: {threshold}%, Extend: +{extend_mb}M)...[/bold cyan]")
    results = auto_heal_lvs(threshold=threshold, extend_mb=extend_mb, dry_run=dry_run)

    if not results:
        console.print("[bold green]✅ All Logical Volumes are healthy and below threshold. No action needed.[/bold green]")
        return

    for r in results:
        color = "green" if r["status"] == "HEALED" else ("yellow" if r["status"] == "DRY-RUN" else "red")
        console.print(f"[{color}][{r['status']}][/{color}] [bold]{r['lv']}[/bold]: {r['reason']}")
