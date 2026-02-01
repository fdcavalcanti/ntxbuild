# Project Features

## Basic NuttX Scripts Wrapper
- Supports the most used functions of the `tools/configure.sh` script on NuttX.
- Makefile build support
- Environemnt `clean` and `distclean`
- Menuconfig available and also kconfig options modification directly from command line
- Full Python API support

## Toolchain Management
- The toolchain module provides a quick way to download toolchains for supported architectures.
- Installed on home directory for general use when needed even outside `ntxbuild` CLI.
- Toolchains are organized by NuttX release and default to latest version.

## CMake Support
The use of Makefile is the default state of `ntxbuild`. To build using CMake, pass
`--use-cmake` to the `ntxbuild start` command. This will setup the directory to CMake
and Ninja generator.

Currently, CMake support uses the `build` directory for output and Ninja generator when invoked
from the CLI. Using the Python API allows more flexibility.

## Real-time Build Output
When building directly from NuttX, the user can see build output in real-time.
This tool keeps the output the same, as the user will see the logging output
with no buffering.

- Live progress display with proper ANSI colors
- No buffering for immediate feedback
- Preserves terminal control sequences

## Lightweight Workspace Copies
The API provides functions that assist in generating lightweight copies of the NuttX
workspace, which can be useful in CI environments.

See usage examples on {doc}`api_examples`.

- Excludes unnecessary files (.git, build artifacts, etc.)
- Configurable target directory
- Automatic cleanup

## Board Explorer

The Board Explorer feature provides a simple way to discover and inspect
the boards and available defconfigs inside a NuttX repository. It is available
both through the CLI (commands that list boards) and the Python API
(see `ntxbuild.nuttx` helpers).

- Quickly find which boards support a particular architecture or SoC.
- Programmatically build a list of candidate boards for automated testing or
	CI matrix generation.
- Provide a lightweight UI (or CLI output) that helps users choose a board
	and defconfig before running `start` or `build` commands.

## Curses Support
Menuconfig works just as usual through this tool.

- Full support for interactive tools like menuconfig
- Proper terminal handling
- No broken interfaces

## To-Do

```{note}
Active feature tracking and new feature requests are now handled on the [project board](https://github.com/users/fdcavalcanti/projects/5).
```

The following are features that should be added to this project:

1. (OK) Publish on PyPi
2. (OK) Add build using CMake
3. Checkpatch script support
4. (OK) Download and install compilers
5. Open the docs for a board
6. Improve support for installing source (multi thread and API improvements)
7. Export defconfig (make savedefconfig)
8. (OK) Support kconfig-merger
9. (OK) Support disabling build log output
10. Prettify logging: add colored output and option to log to file
11. (OK) Replace the shelve module: use .ini file instead
12. Add support for custom Make options on `NuttXBuilder.build`
13. (Partial support) Support extra flags on configure.sh script
