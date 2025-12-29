"""
Command-line interface for ntxbuild.
"""

import logging
import sys
from pathlib import Path

import click

from .build import NuttXBuilder
from .config import ConfigManager
from .env_data import clear_ntx_env, load_ntx_env, save_ntx_env
from .setup import download_nuttx_apps_repo, download_nuttx_repo
from .utils import find_nuttx_root

logger = logging.getLogger("ntxbuild.cli")


def prepare_env(
    nuttx_dir: str = None,
    apps_dir: str = None,
    start: bool = False,
    build_tool: str = "make",
) -> tuple[Path, str, str]:
    """Prepare and validate the NuttX environment.

    Loads the environment from .ntxenv file if it exists, or initializes
    a new environment if start is True. Validates that the current
    directory matches the stored environment.

    Must be executed by CLI commands.

    Args:
        nuttx_dir: Name of the NuttX OS directory. Defaults to None.
        apps_dir: Name of the NuttX apps directory. Defaults to None.
        start: If True, allows initializing a new environment. If False,
            requires an existing .ntxenv file. Defaults to False.

    Returns:
        tuple[Path, str, str]: A tuple containing:
            - Path to the NuttX workspace
            - Name of the NuttX OS directory
            - Name of the NuttX apps directory

    Raises:
        click.ClickException: If environment validation fails or
            .ntxenv is not found when start is False.
    """
    current_dir = Path.cwd()

    if start:
        # This validates the directory structure
        nuttxspace = find_nuttx_root(current_dir, nuttx_dir, apps_dir)

        save_ntx_env(nuttxspace, nuttx_dir, apps_dir, build_tool)
        return nuttxspace, nuttx_dir, apps_dir

    try:
        env = load_ntx_env(current_dir)
    except FileNotFoundError:
        raise click.ClickException(
            "No .ntxenv found. Please run 'start' command first."
        )

    nuttxspace = env["nuttxspace_path"]
    nuttx = env["nuttx_dir"]
    apps = env["apps_dir"]

    return nuttxspace, nuttx, apps


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
    """NuttX Build System Assistant.

    Main entry point for the ntxbuild command-line interface.
    Configures logging based on the specified log level.

    Args:
        log_level: Logging level to use. Can be one of:
            DEBUG, INFO, WARNING, ERROR, or CRITICAL.
            Defaults to WARNING.
    """
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
    """Install NuttX and Apps repositories.

    Downloads the NuttX OS and Apps repositories if they don't already
    exist in the current directory. If the repositories are already
    present, this command will verify their existence.

    Exits with code 0 on success.
    """
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
@click.option(
    "--build-tool", help="Build tool to record (default: make)", default="make"
)
@click.argument("board", nargs=1, required=True)
@click.argument("defconfig", nargs=1, required=True)
def start(apps_dir, nuttx_dir, store_nxtmpdir, build_tool, board, defconfig):
    """Initialize and validate NuttX environment.

    Sets up the NuttX build environment for a specific board and
    defconfig. This command validates the environment, runs the
    configure script, and saves the environment state.

    Args:
        apps_dir: Name of the NuttX apps directory. Defaults to "nuttx-apps".
        nuttx_dir: Name of the NuttX OS directory. Defaults to "nuttx".
        store_nxtmpdir: If True, use nxtmpdir on nuttxspace. Defaults to False.
        board: The board name (e.g., "stm32f4discovery").
        defconfig: The defconfig name (e.g., "nsh").

    Exits with code 0 on success, or the setup exit code on failure.
    """
    click.secho("  📦 Board: ", fg="cyan", nl=False)
    click.secho(f"{board}", bold=True)
    click.secho("  ⚙️  Defconfig: ", fg="cyan", nl=False)
    click.secho(f"{defconfig}", bold=True)

    # Check if .ntxenv file exists
    nuttxspace_path, nuttx_dir, apps_dir = prepare_env(
        nuttx_dir, apps_dir, True, build_tool
    )

    # Run NuttX setup using the builder (includes validation)
    click.echo("\n🔧 Setting up NuttX configuration...")
    click.echo(f"   NuttX directory: {nuttx_dir}")
    click.echo(f"   Apps directory: {apps_dir}\n")

    builder = NuttXBuilder(nuttxspace_path, nuttx_dir, apps_dir)

    extra_args = []
    if store_nxtmpdir:
        extra_args.append("-S")

    setup_result = builder.setup_nuttx(board, defconfig, extra_args)

    if setup_result != 0:
        click.echo("❌ Setup failed")
        clear_ntx_env(nuttxspace_path)
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
    """Manage Kconfig options.

    Provides commands to read, set, and manage Kconfig configuration
    options. Only one action can be performed at a time.

    Args:
        read: Path to the Kconfig option to read (use with --read/-r).
        set_value: Name of the Kconfig option to set a numerical value
            (use with --set-value). Requires value argument.
        set_str: Name of the Kconfig option to set a string value
            (use with --set-str). Requires value argument.
        apply: If True, apply Kconfig changes by running olddefconfig
            (use with --apply/-a flag).
        merge: If True, merge a Kconfig file (use with --merge/-m flag).
            Requires value argument with the source file path.
        value: Value to set (for --set-value or --set-str) or source
            file path (for --merge). Defaults to None.

    Exits with code 0 on success, 1 on error.
    """
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
    """Build NuttX project.

    Compiles the NuttX project using the configured board and defconfig.
    Can optionally specify the number of parallel build jobs.

    Args:
        parallel: Number of parallel jobs to use for building.
            If None, uses default make parallelism. Defaults to None.

    Exits with code 0 on success, 1 on error, or the build exit code
    on build failure.
    """
    try:
        nuttxspace_path, nuttx_dir, apps_dir = prepare_env()
        builder = NuttXBuilder(nuttxspace_path, nuttx_dir, apps_dir)
        result = builder.build(parallel)
        sys.exit(result.returncode)
    except click.ClickException as e:
        click.echo(f"❌ {e}")
        sys.exit(1)


@main.command()
def distclean():
    """Perform a distclean and reset NuttX environment.

    Removes all generated files including configuration files, and
    clears the saved environment state (.ntxenv file).

    Exits with code 0 on success.
    """
    click.echo("🧹 Resetting NuttX environment...")
    nuttxspace_path, nuttx_dir, apps_dir = prepare_env()
    builder = NuttXBuilder(nuttxspace_path, nuttx_dir, apps_dir)
    builder.distclean()
    clear_ntx_env(nuttxspace_path)
    sys.exit(0)


@main.command()
def clean():
    """Clean build artifacts.

    Removes object files and other build artifacts, but preserves
    configuration files.

    Exits with code 0 on success, 1 on error.
    """
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
    """Pass make commands to NuttX build system.

    Executes any make command in the NuttX directory. This allows
    running arbitrary make targets that are not directly exposed
    as separate commands.

    Args:
        command: The make command to run. Can be any make target,
            such as "all", "clean", "distclean", "menuconfig", etc.
            Multiple arguments can be space-separated.

    Exits with code 0 on success, 1 on error, or the make command's
    exit code on failure.
    """
    try:
        click.echo(f"🧹 Running make {command}")
        nuttxspace_path, nuttx_dir, apps_dir = prepare_env()
        builder = NuttXBuilder(nuttxspace_path, nuttx_dir, apps_dir)
        result = builder.make(command)
        sys.exit(result.returncode)
    except click.ClickException as e:
        click.echo(f"❌ {e}")
        sys.exit(1)


@main.command()
@click.option("--menuconfig", "-m", help="Run menuconfig", is_flag=True)
def menuconfig(menuconfig):
    """Run the interactive menuconfig interface.

    Opens the curses-based menu configuration interface for interactive
    Kconfig editing.

    Args:
        menuconfig: If True, run menuconfig (use with --menuconfig/-m flag).
            Defaults to False.

    Exits with code 0 on success, 1 on error.
    """
    try:
        nuttxspace_path, nuttx_dir, apps_dir = prepare_env()
        builder = NuttXBuilder(nuttxspace_path, nuttx_dir, apps_dir)
        builder.run_menuconfig()
        sys.exit(0)
    except click.ClickException as e:
        click.echo(f"❌ {e}")
        sys.exit(1)


@main.command()
@click.option("--binary", "-b", help="Show binary information", is_flag=True)
@click.argument("binary_name", nargs=1, required=False, default="nuttx.bin")
def info(binary, binary_name):
    """Show build information.

    Displays information about the NuttX build environment, including
    paths to the NuttX and Apps directories. Optionally displays
    binary file information if --binary flag is used.

    Args:
        binary: If True, display binary file information
            (use with --binary/-b flag). Defaults to False.
        binary_name: Path to the binary file relative to nuttx directory.
            Only used when --binary flag is set. Defaults to "nuttx.bin".

    Exits with code 0 on success, 1 on error.
    """
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
