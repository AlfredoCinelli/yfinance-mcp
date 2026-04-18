"""MCP custom ASCII art."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

_LOGO = r"""
 $$$$$$\  $$\                         $$\
$$  __$$\ $$ |                        $$ |
$$ /  \__|$$$$$$\    $$$$$$\   $$$$$$$\$$ |  $$\
\$$$$$$\  \_$$  _|  $$  __$$\ $$  _____$$ | $$  |
 \____$$\   $$ |    $$ /  $$ |$$ /     $$$$$$  /
$$\   $$ |  $$ |$$\ $$ |  $$ |$$ |     $$  _$$<
\$$$$$$  |  \$$$$  |\$$$$$$  |\$$$$$$$\$$ | \$$\
 \______/    \____/  \______/  \_______\__|  \__|
"""


def _print_banner(host: str, port: int, transport: str) -> None:
    """Render a styled startup banner to stderr."""
    console = Console(stderr=True)

    display_host = "localhost" if host in ("0.0.0.0", "::") else host

    info = Table.grid(padding=(0, 1))
    info.add_row("⚡", "[bold cyan]Finance MCP Server[/]")
    info.add_row("📡", f"[green]http://{display_host}:{port}[/]")
    info.add_row("🔧", f"Transport: [yellow]{transport}[/]")
    info.add_row("📄", f"[dim]Docs: http://{display_host}:{port}/docs[/]")

    logo = Text(_LOGO, style="bold cyan")

    panel = Panel.fit(
        logo,
        subtitle="[dim]Powered by FastMCP + FastAPI[/]",
        border_style="cyan",
    )

    console.print()
    console.print(panel)
    console.print(info)
    console.print()