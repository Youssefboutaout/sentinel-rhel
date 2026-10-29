import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from sentinel.core.system import get_system_summary
from sentinel.core.lvm import get_volume_groups, get_logical_volumes, auto_heal_lvs
from sentinel.core.network import get_network_interfaces
from sentinel.core.security import get_security_audit

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


@app.command()
def network():
    """Inspect active network interfaces, IP configurations, and speed."""
    console.print(Panel("[bold cyan]🌐 Sentinel-RHEL — Network Telemetry[/bold cyan]", border_style="bright_blue"))

    net_table = Table(title="Network Interfaces", header_style="bold blue")
    net_table.add_column("Interface", style="cyan")
    net_table.add_column("Status", justify="center")
    net_table.add_column("IPv4 Address", style="green")
    net_table.add_column("Speed", justify="right")

    for iface in get_network_interfaces():
        net_table.add_row(iface["name"], iface["status"], iface["ipv4"], iface["speed"])

    console.print(net_table)


@app.command()
def audit():
    """Run a CIS-style security hardening and compliance audit on RHEL 10."""
    console.print(Panel("[bold cyan]🔒 Sentinel-RHEL — Security & Compliance Audit[/bold cyan]", border_style="bright_blue"))

    sec = get_security_audit()
    score = sec["score"]
    score_color = "green" if score >= 80 else ("yellow" if score >= 50 else "red")

    console.print(f"\n[bold]System Compliance Score:[/bold] [{score_color}]⭐ {score}/100[/{score_color}]")
    console.print(f"[bold]SELinux Status:[/bold] [cyan]{sec['selinux']}[/cyan]")
    console.print(f"[bold]SSH PermitRootLogin:[/bold] [cyan]{sec['ssh'].get('PermitRootLogin', 'N/A')}[/cyan]")

    if sec["deductions"]:
        console.print("\n[bold yellow]⚠️ Hardening Recommendations:[/bold yellow]")
        for d in sec["deductions"]:
            console.print(f"  • {d}")
    else:
        console.print("\n[bold green]✅ System fully hardened! No compliance violations found.[/bold green]")
from sentinel.core.watchdog import run_watchdog_loop

@app.command()
def watch(
    interval: int = typer.Option(60, "--interval", "-i", help="Seconds between checks"),
    threshold: float = typer.Option(80.0, "--threshold", "-t", help="Usage % trigger")
):
    """Run Sentinel in continuous background monitoring and self-healing mode."""
    run_watchdog_loop(interval_seconds=interval, threshold=threshold)

@app.command(name="check-all")
def check_all():
    """Run full system health, network, security audit, and LVM telemetry in one go."""
    console.print(Panel("[bold cyan]🚀 Sentinel-RHEL — Full System Master Diagnostic[/bold cyan]", border_style="bright_blue"))
    
    # 1. Appeler l'audit de sécurité
    audit()
    console.print("\n" + "─" * 50 + "\n")
    
    # 2. Appeler le statut général & LVM
    status(threshold=80.0)
    console.print("\n" + "─" * 50 + "\n")
    
    # 3. Appeler le réseau
    network()
from rich.tree import Tree

@app.command()
def tree():
    """Display LVM topology and filesystem mount points as a visual tree structure."""
    console.print(Panel("[bold cyan]🌳 Sentinel-RHEL — Storage Topology Tree[/bold cyan]", border_style="bright_blue"))

    root_tree = Tree("🖥️ [bold magenta]RHEL 10 Storage Infrastructure[/bold magenta]")

    vgs = get_volume_groups()
    lvs = get_logical_volumes()

    for vg in vgs:
        vg_branch = root_tree.add(
            f"📦 [bold cyan]VG: {vg['vg_name']}[/bold cyan] "
            f"([dim]Total: {vg['vg_size']} | Free Pool: {vg['vg_free']}[/dim])"
        )
        
        vg_lvs = [lv for lv in lvs if lv["vg_name"] == vg["vg_name"]]
        
        for lv in vg_lvs:
            usage_color = "red" if lv["usage_val"] >= 80 else "green"
            vg_branch.add(
                f"📂 [bold yellow]{lv['lv_name']}[/bold yellow] ➔ "
                f"Mount: [blue]{lv['mountpoint']}[/blue] "
                f"({lv['size']}, fs: {lv['fstype']}) | "
                f"Usage: [{usage_color}]{lv['usage']}[/{usage_color}]"
            )

    console.print(root_tree)
from pathlib import Path
from rich.tree import Tree

def add_directory_tree(parent_node, path: Path, depth=1, max_depth=2):
    """Recursively add directory folders and files to the Rich tree."""
    if depth > max_depth or not path.exists() or not path.is_dir():
        return
    try:
        entries = sorted(path.iterdir(), key=lambda e: (not e.is_dir(), e.name))
        count = 0
        for entry in entries:
            if entry.name.startswith('.'):
                continue
            if entry.is_dir():
                branch = parent_node.add(f"📁 [bold blue]{entry.name}/[/bold blue]")
                if depth < max_depth:
                    add_directory_tree(branch, entry, depth + 1, max_depth)
            else:
                parent_node.add(f"📄 [dim]{entry.name}[/dim]")
            count += 1
            if count > 15:  # Limiter pour garder un affichage propre
                parent_node.add("[italic dim]... (more items hidden)[/italic dim]")
                break
    except PermissionError:
        parent_node.add("🔒 [red]Permission Denied[/red]")

@app.command(name="tree")
def display_tree():
    """Display comprehensive system info, LVM storage topology, and directory trees."""
    sys_info = get_system_summary()

    # 1. Panneau d'informations système globales approfondies
    sys_panel_text = (
        f"[bold cyan]OS Release:[/bold cyan] {sys_info['os_release']}\n"
        f"[bold cyan]Hostname:[/bold cyan] {sys_info['hostname']}   [bold cyan]Kernel:[/bold cyan] {sys_info['kernel']} ({sys_info['architecture']})\n"
        f"[bold cyan]Uptime:[/bold cyan] {sys_info['uptime']}   [bold cyan]Load Avg (1, 5, 15m):[/bold cyan] {sys_info['load_avg']}\n"
        f"[bold cyan]CPU:[/bold cyan] {sys_info['cpu_cores']} vCPUs @ {sys_info['cpu_freq']} (Usage: {sys_info['cpu_usage']})\n"
        f"[bold cyan]RAM Usage:[/bold cyan] {sys_info['ram_usage']}   [bold cyan]Swap:[/bold cyan] {sys_info['swap_usage']}\n"
        f"[bold cyan]SELinux:[/bold cyan] [green]{sys_info['selinux']}[/green]   [bold cyan]Firewalld:[/bold cyan] [green]{sys_info['firewalld']}[/green]"
    )
    console.print(Panel(sys_panel_text, title="🛡️ Sentinel-RHEL — Comprehensive System & Storage Inspector", border_style="bright_blue"))

    # 2. Arbre combiné LVM + Dossiers physiques
    root_tree = Tree("🖥️ [bold magenta]RHEL 10 Infrastructure Topology & File Tree[/bold magenta]")

    vgs = get_volume_groups()
    lvs = get_logical_volumes()

    for vg in vgs:
        vg_branch = root_tree.add(
            f"📦 [bold cyan]VG: {vg['vg_name']}[/bold cyan] "
            f"([dim]Total: {vg['vg_size']} | Free Pool: {vg['vg_free']}[/dim])"
        )
        
        vg_lvs = [lv for lv in lvs if lv["vg_name"] == vg["vg_name"]]
        
        for lv in vg_lvs:
            usage_color = "red" if lv["usage_val"] >= 80 else "green"
            mount_path = lv["mountpoint"]
            
            lv_branch = vg_branch.add(
                f"📂 [bold yellow]{lv['lv_name']}[/bold yellow] ➔ "
                f"Mount: [blue]{mount_path}[/blue] "
                f"({lv['size']}, fs: {lv['fstype']}) | "
                f"Usage: [{usage_color}]{lv['usage']}[/{usage_color}]"
            )

            # Ajouter l'arborescence des dossiers physiques sous ce point de montage
            if mount_path != "[SWAP]" and mount_path != "N/A":
                target_path = Path(mount_path)
                if target_path.exists():
                    add_directory_tree(lv_branch, target_path, depth=1, max_depth=2)

    console.print(root_tree)
