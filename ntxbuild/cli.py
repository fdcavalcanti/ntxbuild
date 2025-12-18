"""
Command-line interface for ntxbuild.
"""

import logging
import sys
from pathlib import Path

import click

from .build import NuttXBuilder
from .config import ConfigManager
from .env_data import clear_ntx_env, has_ntx_env, load_ntx_env, save_ntx_env
from .setup import download_nuttx_apps_repo, download_nuttx_repo
from .utils import find_nuttx_root

logger = logging.getLogger("ntxbuild.cli")


def prepare_env(nuttx_dir: str = None, apps_dir: str = None, start: bool = False):
    current_dir = Path.cwd()
    if has_ntx_env():
        nuttxspace, nuttx, apps = load_ntx_env()
        if not start:
            assert current_dir == nuttxspace
        return nuttxspace, nuttx, apps
    else:
        if start:
            try:
                find_nuttx_root(current_dir, nuttx_dir, apps_dir)
            except FileNotFoundError as e:
                raise click.ClickException(e)
            save_ntx_env(current_dir, nuttx_dir, apps_dir)
            return current_dir, nuttx_dir, apps_dir
        else:
            raise click.ClickException(
                "No .ntxenv found. Please run 'start' command first."
            )


@click.group()
@click.option(
    "--log-level",
    type=click.Choice(
        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False
    ),
    default="WARNING",
    help="Set the logging level (default: WARNING)",
)
@click.version_option()
def main(log_level):
    """NuttX Build System Assistant"""
    # Reconfigure logging with the user-specified level
    logger.info(f"Setting logging level to {log_level}")
    log_level_value = getattr(logging, log_level.upper())

    # Get the root logger and update its level
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level_value)

    # Update all existing handlers to use the new level
    for handler in root_logger.handlers:
        handler.setLevel(log_level_value)

    # Set the ntxbuild parent logger level (this will affect all child loggers)
    ntxbuild_logger = logging.getLogger("ntxbuild")
    ntxbuild_logger.setLevel(log_level_value)

    # Set the specific logger level
    logger.setLevel(log_level_value)


@main.command()
def install():
    """Install NuttX and Apps repositories"""
    current_dir = Path.cwd()
    click.echo("🚀 Downloading NuttX and Apps repositories...")
    nuttx_dir = "nuttx"
    apps_dir = "nuttx-apps"

    try:
        find_nuttx_root(current_dir, nuttx_dir, apps_dir)
        click.echo("✅ NuttX and Apps directories already exist.")
    except FileNotFoundError:
        download_nuttx_repo()
        download_nuttx_apps_repo()
        find_nuttx_root(current_dir, nuttx_dir, apps_dir)

    click.echo("✅ Installation completed successfully.")
    sys.exit(0)


@main.command()
@click.option("--apps-dir", "-a", help="Apps directory", default="nuttx-apps")
@click.option("--nuttx-dir", help="NuttX directory", default="nuttx")
@click.option("--store-nxtmpdir", "-S", is_flag=True, help="Use nxtmpdir on nuttxspace")
@click.argument("board", nargs=1, required=True)
@click.argument("defconfig", nargs=1, required=True)
def start(apps_dir, nuttx_dir, store_nxtmpdir, board, defconfig):
    """Initialize and validate NuttX environment"""
    current_dir = Path.cwd()
    click.secho("  📦 Board: ", fg="cyan", nl=False)
    click.secho(f"{board}", bold=True)
    click.secho("  ⚙️  Defconfig: ", fg="cyan", nl=False)
    click.secho(f"{defconfig}", bold=True)

    # Check if .ntxenv file exists
    _, nuttx_dir, apps_dir = prepare_env(nuttx_dir, apps_dir, True)

    # Run NuttX setup using the builder (includes validation)
    click.echo("\n🔧 Setting up NuttX configuration...")
    click.echo(f"   NuttX directory: {nuttx_dir}")
    click.echo(f"   Apps directory: {apps_dir}\n")

    builder = NuttXBuilder(current_dir, nuttx_dir, apps_dir)

    extra_args = []
    if store_nxtmpdir:
        extra_args.append("-S")

    setup_result = builder.setup_nuttx(board, defconfig, extra_args)

    if setup_result != 0:
        click.echo("❌ Setup failed")
        clear_ntx_env()
        return sys.exit(setup_result)

    click.echo("")
    click.echo("✅ Configuration completed successfully")
    click.echo("\n🚀 NuttX environment is ready!")
    return sys.exit(0)


@main.command()
@click.option("--read", "-r", help="Path to apps folder (relative or absolute)")
@click.option("--set-value", help="Set Kconfig value")
@click.option("--set-str", help="Set Kconfig string")
@click.option("--apply", "-a", help="Apply Kconfig options", is_flag=True)
@click.option("--merge", "-m", help="Merge Kconfig file", is_flag=True)
@click.argument("value", nargs=1, required=False)
def kconfig(read, set_value, set_str, apply, value, merge):
    """Read Kconfig file"""
    try:
        nuttxspace_path, nuttx_dir, _ = prepare_env()
        config_manager = ConfigManager(nuttxspace_path, nuttx_dir)
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
        elif merge:
            if not value:
                click.echo("❌ Merge file is required")
            config_manager.kconfig_merge_config_file(value, None)
        else:
            click.echo("❌ No action specified")
    except click.ClickException as e:
        click.echo(f"❌ {e}")
        sys.exit(1)

    sys.exit(0)


@main.command()
@click.option(
    "--parallel", "-j", required=False, type=int, help="Number of parallel jobs"
)
def build(parallel):
    """Build NuttX project"""
    try:
        nuttxspace_path, nuttx_dir, apps_dir = prepare_env()
        builder = NuttXBuilder(nuttxspace_path, nuttx_dir, apps_dir)
        result = builder.build(parallel)
        sys.exit(result)
    except click.ClickException as e:
        click.echo(f"❌ {e}")
        sys.exit(1)


@main.command()
def distclean():
    """Clean build artifacts"""
    click.echo("🧹 Resetting NuttX environment...")
    current_dir, nuttx_dir, apps_dir = prepare_env()
    builder = NuttXBuilder(current_dir, nuttx_dir, apps_dir)
    builder.distclean()
    clear_ntx_env()
    sys.exit(0)


@main.command()
def clean():
    """Clean build artifacts"""
    try:
        click.echo("🧹 Cleaning build artifacts...")
        nuttxspace_path, nuttx_dir, apps_dir = prepare_env()
        builder = NuttXBuilder(nuttxspace_path, nuttx_dir, apps_dir)
        builder.clean()
        sys.exit(0)
    except click.ClickException as e:
        click.echo(f"❌ {e}")
        sys.exit(1)


@main.command()
@click.argument("command", nargs=1, required=True)
def make(command):
    """Passes make commands to NuttX build system.
    Can be used to run any make command.
    """
    try:
        click.echo(f"🧹 Running make {command}")
        nuttxspace_path, nuttx_dir, apps_dir = prepare_env()
        builder = NuttXBuilder(nuttxspace_path, nuttx_dir, apps_dir)
        builder.make(command)
        sys.exit(0)
    except click.ClickException as e:
        click.echo(f"❌ {e}")
        sys.exit(1)


@main.command()
@click.option("--menuconfig", "-m", help="Run menuconfig", is_flag=True)
def menuconfig(menuconfig):
    """Run menuconfig"""
    try:
        nuttxspace_path, nuttx_dir, apps_dir = prepare_env()
        builder = NuttXBuilder(nuttxspace_path, nuttx_dir, apps_dir)
        builder.run_menuconfig()
        sys.exit(0)
    except click.ClickException as e:
        click.echo(f"❌ {e}")
        sys.exit(1)


@main.command()
@click.option("--binary", "-b", help="Run menuconfig", is_flag=True)
@click.argument("binary_name", nargs=1, required=False, default="nuttx.bin")
def info(binary, binary_name):
    """Show build information"""
    try:
        nuttxspace_path, nuttx_dir, apps_dir = prepare_env()
        click.echo(f"NuttX root found at: {nuttxspace_path}")
        click.echo(f"NuttX directory: {nuttxspace_path / nuttx_dir}")
        click.echo(f"Apps directory: {nuttxspace_path / apps_dir}")
    except click.ClickException as e:
        click.echo(f"❌ {e}")
        sys.exit(1)

    if binary:
        builder = NuttXBuilder(nuttxspace_path, nuttx_dir, apps_dir)
        builder.print_binary_info(binary_name)

    sys.exit(0)


if __name__ == "__main__":
    main()
