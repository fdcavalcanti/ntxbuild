# ntxbuild

**NuttX Build System Assistant** - A Python tool for managing and building NuttX RTOS projects with ease.

ntxbuild is simply a wrapper around the many tools available in the NuttX repository. It wraps around tools
such as make, kconfig-tweak, menuconfig and most used bash scripts (such as configure.sh).

This tool provides a command line interface that supports NuttX configuration and building,
while also providing a Python API that allows you to script your builds.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Linux](https://img.shields.io/badge/platform-Linux-lightgrey.svg)](https://www.linux.org/)

## Features

- **Environment Management**: Automatic NuttX workspace detection and configuration
- **Parallel Builds**: Support for multi-threaded builds with isolated workspaces
- **Real-time Output**: Live build progress with proper ANSI escape sequence handling
- **Configuration Management**: Kconfig integration for easy system configuration
- **Build Cleanup**: Automated artifact management and cleanup
- **Persistent Settings**: Environment configuration saved in `.ntxenv` files
- **Interactive Tools**: Support for curses-based tools like menuconfig

## Requirements

- **Python 3.9+**
- **NuttX** source code and applications
- **Make** and standard build tools required by NuttX RTOS

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


## Quick Start

### 1. Initialize Your NuttX Environment

```bash
# Navigate to your NuttX workspace
cd /path/to/your/nuttx-workspace

# Initialize with board and defconfig
ntxbuild start sim nsh
```

### 2. Build Your Project

```bash
# Build with default settings
ntxbuild build

# Or, build with parallel jobs
ntxbuild build --parallel 8
```

### 3. Configure Your System

```bash
# Run menuconfig
ntxbuild menuconfig

# Set Kconfig values
ntxbuild kconfig --set-value CONFIG_DEBUG=y
ntxbuild kconfig --set-str CONFIG_APP_NAME="MyApp"
```

## 🏗️ Project Structure

```
your-nuttx-workspace/
├── nuttx/                   # NuttX kernel source
├── nuttx-apps/              # NuttX applications
├── .ntxenv                  # Environment configuration (auto-generated)
```

## 🔧 Environment Configuration

The `.ntxenv` file stores your workspace configuration:

- **NuttX directory name**
- **Apps directory name**
- **Workspace path**

This allows ntxbuild to remember your setup between sessions.


## Contributing
Contributions are always welcome but will be subject to review and approval.
Basic rules:
- Testing and documentation are mandatory for new features
- Depedencies should be kept to a minimal
- Code linting using pre-commit is mandatory
