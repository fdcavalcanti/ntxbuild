# ntxbuild

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Linux](https://img.shields.io/badge/platform-Linux-lightgrey.svg)](https://www.linux.org/)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/fdcavalcanti/ntxbuild/python-package.yml)
![Read the Docs](https://img.shields.io/readthedocs/ntxbuild)

**NuttX Build System Assistant** - A Python tool for managing and building NuttX RTOS projects with ease.

ntxbuild is a wrapper around the many tools available in the NuttX repository. It wraps around utilities
such as make, kconfig-tweak, menuconfig and most used bash scripts (such as configure.sh).

Also, it provides different features, such as downloading required toolchains and managing PATH.

This tool provides a command line interface that supports NuttX configuration and building,
while also providing a Python API that allows you to script your builds.

## Features

- **Environment Management**: Automatic NuttX workspace detection and configuration
- **Python API**: ntxbuild is available as a Python package for building NuttX using Python scripts
- **Real-time Output**: Live build progress with proper ANSI escape sequence handling
- **Configuration Management**: Kconfig integration for easy system configuration
- **Interactive Tools**: Support for curses-based tools like menuconfig
- **Toolchin Support**: Download and use your required toolchain automatically through the CLI

## Documentation

Complete documentation, including usage examples and API reference, see: https://ntxbuild.readthedocs.io

## Requirements

- **Python 3.10+**
- **NuttX** source code and applications
- **Make** and standard build tools required by NuttX RTOS
- **CMake** supported but optional

## Quick Start


### Build using CLI

Navigate to your NuttX workspace and download latest NuttX and NuttX Apps using `ntxbuild`.
```bash
$ mkdir ~/nuttxspace
$ cd ~/nuttxspace
$ ntxbuild download
```

Build the simulator using the `nsh` defconfig.
```bash
$ ntxbuild start sim nsh
$ ntxbuild build --parallel 8
```

### Build using Python script
Alternatively, you can automate your builds using a Python script instead of the CLI.

```python
from pathlib import Path
from ntxbuild.build import MakeBuilder

current_dir = Path.cwd()

# Use the Makefile-based builder
builder = MakeBuilder(current_dir, "nuttx", "nuttx-apps")
# Initialize the board/defconfig
setup_result = builder.initialize("sim", "nsh")

# Execute the build with 10 parallel jobs
builder.build(parallel=10)

# You can now clean the environment if needed
builder.distclean()
```

### Installing toolchains
Support for installing some of the most common toolchains is available.

```bash
$ ntxbuild toolchain install gcc-arm-none-eabi
Installing toolchain gcc-arm-none-eabi for NuttX v12.12.0
✅ Toolchain gcc-arm-none-eabi installed successfully
Installation directory: /home/user/ntxenv/toolchains
Note: Toolchains are sourced automatically during build.
```

## Installation

### Using pip

As an user, you can install this tool using pip:
```bash
pip install ntxbuild
```

### From Source
If you are a developer or simply wants to install from source, you can clone
this repository and install using `pip install -e <repo>`

```bash
git clone <repository-url>
cd ntxbuild
pip install -e .
```

Use the `dev` configuration to install development tools and `docs` to install
documentation tools.

```bash
pip install -e ".[dev]"
```
```bash
pip install -e ".[docs]"
```

## Contributing
Contributions are always welcome but will be subject to review and approval.
Basic rules:
- Testing and documentation are mandatory for new features
- Depedencies should be kept to a minimal
- Code linting using pre-commit is mandatory
