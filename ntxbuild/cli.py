"""
Command-line interface for ntxbuild.
"""

import click
import os
from pathlib import Path
from .build import NuttXBuilder
from .config import ConfigManager
from .utils import find_nuttx_root
from typing import List, Optional, Dict
import subprocess

@click.group()
@click.version_option()
def main():
    """NuttX Build System Assistant"""
    pass

@main.command()
@click.option('--apps', '-a', required=True, help='Path to apps folder (relative or absolute)')
@click.argument('board', nargs=1, required=True)
@click.argument('defconfig', nargs=1, required=True)
def start(apps, board, defconfig):
    """Initialize and validate NuttX environment"""
    current_dir = Path.cwd()
    click.secho(f"  📦 Board: ", fg="cyan", nl=False)
    click.secho(f"{board}", bold=True)
    click.secho(f"  ⚙️  Defconfig: ", fg="cyan", nl=False)
    click.secho(f"{defconfig}", bold=True)

    # Handle apps path (now mandatory)
    apps_path = Path(apps)
    if not apps_path.is_absolute():
        apps_path = current_dir / apps_path
    
    # Run NuttX setup using the builder (includes validation)
    click.echo(f"\n🔧 Setting up NuttX configuration...")
    click.echo(f"   Root directory: {current_dir}")
    click.echo(f"   Apps directory: {apps_path.resolve()}")
    
    builder = NuttXBuilder()
    setup_result = builder.setup_nuttx(current_dir, apps_path, board, defconfig)
    
    if setup_result != 0:
        click.echo("❌ Setup failed")
        return setup_result
    
    click.echo("   ✅ Configuration completed successfully")
    click.echo("\n🚀 NuttX environment is ready!")
    return 0

@main.command()
@click.option('--read', '-r', help='Path to apps folder (relative or absolute)', required=False)
def kconfig(read):
    """Read Kconfig file"""
    builder = NuttXBuilder()
    if read:
        builder.kconfig_read(read)

@main.command()
@click.option('--parallel', '-j', required=False, type=int, help='Number of parallel jobs')
def build(parallel):
    """Build NuttX project"""
    builder = NuttXBuilder()
    builder.build(parallel)

@main.command()
def distclean():
    """Clean build artifacts"""
    click.echo("🧹 Resetting NuttX environment...")
    builder = NuttXBuilder()
    builder.distclean()

@main.command()
def clean():
    """Clean build artifacts"""
    click.echo("🧹 Cleaning build artifacts...")
    builder = NuttXBuilder()
    builder.clean()

@main.command()
def info():
    """Show build information"""
    nuttx_root = find_nuttx_root()
    if nuttx_root:
        click.echo(f"NuttX root found at: {nuttx_root}")
    else:
        click.echo("NuttX root not found in current directory tree")

if __name__ == '__main__':
    main()
