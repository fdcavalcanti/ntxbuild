# How It Works
This page describes how the main functionalities of this tool work.

## Environment Setup
`ntxbuild` usage starts with setting up the NuttX environment.
When `start` option is called, the "environment" is prepared. This means things:
- An environment file is created which is used to store some information
- The path to the NuttX repository is added to the env file
- The path to the NuttX Application repository is also added to the env file

This env file will be used by the tool to locate the repositories.
In the future (as a TO-DO task), the same file (which may be changed to a .ini file)
could be used to store other stuff, such as out-of-tree repositories and path
to toolchains.

Once the environment file is setup, a `NuttXBuilder` instance is created and
it sets up the NuttX environment by checking if the repository is valid
and finally, executes the `nuttx/tools/configure.sh` script (remember, this tool
is a wrapper around NuttX).

## Setting KConfig Options
KConfig options are set through the `ConfigManager` class. When instantiated,
it only requires the path to the NuttX workspace and it defaults to accessing
NuttX on the `nuttx` directory.

The methods are wrappers around the `kconfig-tweak` program. Menuconfig is
available as well but it does require some tweaks to make it work underneath.

## Building
Building is still done by the `NuttXBuilder` class. The method `build` triggers
a `make` command and optionally supports passing the parallel jobs.
TO-DO: it should support extra options.

## Cleaning Environment
Also done by the `NuttXBuilder` class, it wraps the `make` and `make distclean`
on NuttX.
