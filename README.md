# ntxbuild

[![PyPI](https://img.shields.io/pypi/v/ntxbuild.svg)](https://pypi.org/project/ntxbuild/)
[![Python 3.10+](https://img.shields.io/pypi/pyversions/ntxbuild.svg)](https://pypi.org/project/ntxbuild/)
[![Linux](https://img.shields.io/badge/platform-Linux-lightgrey.svg)](https://www.linux.org/)
[![CI](https://img.shields.io/github/actions/workflow/status/fdcavalcanti/ntxbuild/python-package.yml?label=CI)](https://github.com/fdcavalcanti/ntxbuild/actions/workflows/python-package.yml)
[![Docs](https://img.shields.io/readthedocs/ntxbuild?label=docs)](https://ntxbuild.readthedocs.io)
[![License](https://img.shields.io/github/license/fdcavalcanti/ntxbuild.svg)](LICENSE)

**NuttX Build System Assistant** for configuring and building NuttX RTOS projects through a CLI and a Python API.

`ntxbuild` wraps common NuttX tools and workflows, including `make`, `kconfig-tweak`, `menuconfig`, and `configure.sh`.
It also provides helpers for downloading toolchains, listing boards and defconfigs, and managing build environment paths.

## Installation

Install from PyPI:

```bash
python -m pip install ntxbuild
```

## Features

- **Environment management**: automatic NuttX workspace detection and configuration.
- **Python API**: script builds directly from Python.
- **Real-time output**: live build progress with proper ANSI escape sequence handling.
- **Configuration management**: Kconfig integration for easy configuration.
- **Interactive tools**: support for curses-based tools such as `menuconfig`.
- **Toolchain support**: install and use common toolchains directly from the CLI.

## Requirements

- **Python 3.10+**
- **NuttX** source code and applications
- **Make** and standard build tools required by NuttX
- **CMake** (optional)

## Quick Start

### Build with the CLI

Create a workspace and download NuttX and NuttX Apps:

```bash
mkdir -p ~/nuttxspace
cd ~/nuttxspace
ntxbuild download
```

Build the simulator using the `nsh` defconfig:

```bash
ntxbuild start sim nsh
ntxbuild build --parallel 8
```

### Build with Python

```python
from pathlib import Path
from ntxbuild.build import MakeBuilder

current_dir = Path.cwd()

# First parameter is the NuttX workspace path, second is the apps directory name.
builder = MakeBuilder(current_dir, "nuttx-apps")
builder.initialize("sim", "nsh")
builder.build(parallel=10)
builder.distclean()
```

### Install toolchains

```bash
ntxbuild toolchain install gcc-arm-none-eabi
```

## Documentation

Full documentation (usage and API reference): https://ntxbuild.readthedocs.io

## Support

- Report bugs or request features in [GitHub Issues](https://github.com/fdcavalcanti/ntxbuild/issues).
- For usage details, see the [documentation](https://ntxbuild.readthedocs.io).

## Contributing

Contributions are welcome and reviewed before merge.

- Tests and documentation are required for new features.
- Dependencies should be kept to a minimum.
- Code linting via `pre-commit` is required.

Installing from source:

```bash
git clone https://github.com/fdcavalcanti/ntxbuild.git
cd ntxbuild
pip install -e .
```

Optional extras automatically install required development tools or documentation build tools:

```bash
pip install -e ".[dev]"
pip install -e ".[docs]"
```

## License

This project is licensed under the terms in [`LICENSE`](LICENSE).
