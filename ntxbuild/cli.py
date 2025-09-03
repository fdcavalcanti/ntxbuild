"""
Command-line interface for ntxbuild.
"""

from pathlib import Path

import click
import sys

from .build import NuttXBuilder
from .config import ConfigManager
from .utils import find_nuttx_root


@click.group()
@click.version_option()
def main():
    """NuttX Build System Assistant"""
    pass


@main.command()
@click.argument("board", nargs=1, required=True)
@click.argument("defconfig", nargs=1, required=True)
def start(board, defconfig):
    """Initialize and validate NuttX environment"""
    current_dir = Path.cwd()
    click.secho("  📦 Board: ", fg="cyan", nl=False)
    click.secho(f"{board}", bold=True)
    click.secho("  ⚙️  Defconfig: ", fg="cyan", nl=False)
    click.secho(f"{defconfig}", bold=True)

    nuttxspace_path = find_nuttx_root(current_dir, "nuttx", "nuttx-apps")
    assert isinstance(nuttxspace_path, Path)

    # Run NuttX setup using the builder (includes validation)
    click.echo("\n🔧 Setting up NuttX configuration...")
    click.echo(f"   NuttX directory: {current_dir}")
    click.echo(f"   Apps directory: nuttx-apps")

    builder = NuttXBuilder(nuttxspace_path)
    setup_result = builder.setup_nuttx(board, defconfig)

    if setup_result != 0:
        click.echo("❌ Setup failed")
        return sys.exit(setup_result)

    click.echo("   ✅ Configuration completed successfully")
    click.echo("\n🚀 NuttX environment is ready!")
    return sys.exit(0)


@main.command()
@click.option("--read", "-r", help="Path to apps folder (relative or absolute)")
@click.option("--set-value", help="Set Kconfig value")
@click.option("--set-str", help="Set Kconfig string")
@click.option("--apply", "-a", help="Apply Kconfig options", is_flag=True)
@click.argument("value", nargs=1, required=False)
def kconfig(read, set_value, set_str, apply, value):
    """Read Kconfig file"""
    config_manager = ConfigManager()
    if read:
        config_manager.kconfig_read(read)
    elif set_value:
        if not value:
            click.echo("❌ Set value is required")
        config_manager.kconfig_set_value(set_value, value)
    elif set_str:
        if not value:
            click.echo("❌ Set string is required")
        config_manager.kconfig_set_str(set_str, value)
    elif apply:
        config_manager.kconfig_apply_changes()
    else:
        click.echo("❌ No action specified")

    sys.exit(0)


@main.command()
@click.option(
    "--parallel", "-j", required=False, type=int, help="Number of parallel jobs"
)
def build(parallel):
    """Build NuttX project"""
    nuttxspace_path = find_nuttx_root(Path.cwd(), "nuttx", "nuttx-apps")
    builder = NuttXBuilder(nuttxspace_path)
    builder.build(parallel)


@main.command()
def distclean():
    """Clean build artifacts"""
    click.echo("🧹 Resetting NuttX environment...")
    nuttxspace_path = find_nuttx_root(Path.cwd(), "nuttx", "nuttx-apps")
    builder = NuttXBuilder(nuttxspace_path)
    builder.distclean()
    sys.exit(0)


@main.command()
def clean():
    """Clean build artifacts"""
    click.echo("🧹 Cleaning build artifacts...")
    nuttxspace_path = find_nuttx_root(Path.cwd(), "nuttx", "nuttx-apps")
    builder = NuttXBuilder(nuttxspace_path)
    builder.clean()
    sys.exit(0)

@main.command()
def info():
    """Show build information"""
    nuttx_root = find_nuttx_root(Path.cwd(), "nuttx", "nuttx-apps")
    if nuttx_root:
        click.echo(f"NuttX root found at: {nuttx_root}")
        click.echo(f"NuttX directory: {nuttx_root / 'nuttx'}")
        click.echo(f"Apps directory: {nuttx_root / 'nuttx-apps'}")
    else:
        click.echo("NuttX root not found in current directory tree")
    sys.exit(0)

if __name__ == "__main__":
    main()
