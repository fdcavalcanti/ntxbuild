# ntxbuild

**NuttX Build System Assistant** - A Python tool for managing and building NuttX RTOS projects with ease.

ntxbuild is simply a wrapper around the many tools available in the NuttX repository. It wraps around tools
such as make, kconfig-tweak, menuconfig and most used bash scripts (such as configure.sh).

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Linux](https://img.shields.io/badge/platform-Linux-lightgrey.svg)](https://www.linux.org/)

## 🚀 Features

- **🔧 Environment Management**: Automatic NuttX workspace detection and configuration
- **⚡ Parallel Builds**: Support for multi-threaded builds with isolated workspaces
- **🎯 Real-time Output**: Live build progress with proper ANSI escape sequence handling
- **📝 Configuration Management**: Kconfig integration for easy system configuration
- **🧹 Build Cleanup**: Automated artifact management and cleanup
- **💾 Persistent Settings**: Environment configuration saved in `.ntxenv` files
- **🖥️ Interactive Tools**: Support for curses-based tools like menuconfig

## 📋 Requirements

- **Linux** (Ubuntu, Debian, CentOS, etc.)
- **Python 3.8+**
- **NuttX** source code and applications
- **Make** and standard build tools

## 🛠️ Installation

### From Source

```bash
git clone <repository-url>
cd ntxbuild
pip install -e .
```

### Development Setup

```bash
pip install -e ".[dev]"
```

## 🎯 Quick Start

### 1. Initialize Your NuttX Environment

```bash
# Navigate to your NuttX workspace
cd /path/to/your/nuttx-workspace

# Initialize with board and defconfig
ntxbuild start esp32c6-devkitc nsh
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

## 📖 Command Reference

### `start` - Initialize NuttX Environment
```bash
ntxbuild start [OPTIONS] BOARD DEFCONFIG
```

**Options:**
- `--nuttx-dir TEXT`: NuttX directory name (default: nuttx)
- `--apps-dir TEXT`: Apps directory name (default: nuttx-apps)

**Example:**
```bash
ntxbuild start esp32c6-devkitc nsh
```

### `build` - Build NuttX Project
```bash
ntxbuild build [OPTIONS]
```

**Options:**
- `--parallel, -j INTEGER`: Number of parallel jobs

**Example:**
```bash
ntxbuild build --parallel 4
```

### `menuconfig` - Interactive Configuration
```bash
ntxbuild menuconfig
```

### `kconfig` - Configuration Management
```bash
ntxbuild kconfig [OPTIONS] [VALUE]
```

**Options:**
- `--read, -r TEXT`: Path to apps folder
- `--set-value TEXT`: Set Kconfig value
- `--set-str TEXT`: Set Kconfig string
- `--apply, -a`: Apply Kconfig options

**Examples:**
```bash
ntxbuild kconfig --set-value CONFIG_DEBUG=y
ntxbuild kconfig --set-str CONFIG_APP_NAME="MyApp"
ntxbuild kconfig --apply
```

### `clean` - Clean Build Artifacts
```bash
ntxbuild clean
```

### `distclean` - Reset Environment
```bash
ntxbuild distclean
```

### `info` - Show Build Information
```bash
ntxbuild info
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

## ⚡ Parallel Builds

ntxbuild supports creating parallel environments by creating isolated copies of your workspace.
This could assist on CI and running multiple config builds in parallel.

```python
from ntxbuild.utils import copy_nuttxspace_to_tmp, cleanup_tmp_copies

# Create 4 copies for parallel builds
copied_paths = copy_nuttxspace_to_tmp("/path/to/nuttxspace", 4)

# Use each copy in different threads
for path in copied_paths:
    # Run build in thread with isolated workspace
    pass

# Clean up when done
cleanup_tmp_copies(copied_paths)
```

## 🎨 Advanced Features

### Real-time Build Output
- Live progress display with proper ANSI colors
- No buffering for immediate feedback
- Preserves terminal control sequences

### Lightweight Workspace Copies
- Excludes unnecessary files (.git, build artifacts, etc.)
- Configurable target directory
- Automatic cleanup

### Curses Support
- Full support for interactive tools like menuconfig
- Proper terminal handling
- No broken interfaces

## 🐛 Troubleshooting

### Common Issues

**"No .ntxenv found"**
```bash
# Run the start command first
ntxbuild start <board> <defconfig>
```

**"NuttX workspace not found"**
```bash
# Make sure you're in the correct directory
# Your workspace should contain both 'nuttx' and 'nuttx-apps' directories
```

**Build failures**
```bash
# Check your toolchain and dependencies
# Ensure all required packages are installed
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Filipe Cavalcanti**

## 🙏 Acknowledgments

- NuttX community for the excellent embedded OS
- Python community for the amazing ecosystem
- All contributors and users
