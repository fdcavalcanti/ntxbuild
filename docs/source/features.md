# Project Features

## Basic NuttX Scripts Wrapper
- Supports the most used functions of the `tools/configure.sh` script on NuttX.
- Makefile build support
- Environemnt `clean` and `distclean`
- Menuconfig available and also kconfig options modification directly from command line
- Full Python API support

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

## Curses Support
Menuconfig works just as usual through this tool.

- Full support for interactive tools like menuconfig
- Proper terminal handling
- No broken interfaces

## To-Do

The following are features that should be added to this project:

1. Publish on PyPi
2. Add build using CMake
3. Checkpatch script support
4. Download and install compilers
5. Open the docs for a board
6. Improve support for installing source (multi thread and API improvements)
7. Export defconfig (make savedefconfig)
8. Support disabling build log output
9. Prettify logging: add colored output and option to log to file
10. Replace the shelve module: use .ini file instead
11. Add support for custom Make options on `NuttXBuilder.build`
