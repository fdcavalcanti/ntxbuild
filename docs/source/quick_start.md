
# Quick Start

ntxbuild must be used in a directory that contains the NuttX directory with
the kernel and the apps directory with applications (nuttx-apps).

## 1. Prepare the source code
NuttX requires two repositories for building: `nuttx` and `nuttx-apps`.
You should clone those from Github inside a directory usually named `nuttxspace`
or simply use the `install` command to quickly download both repositories.

```bash
# Create the workspace
mkdir nuttxspace

# Navigate to the workspace
cd nuttxspace

# Use ntxbuild install to quickly fetch the repositories
ntxbuild install
🚀 Downloading NuttX and Apps repositories...
✅ Installation completed successfully.
```

## 2. Initialize Your NuttX Environment
The start command sets up the entire NuttX environment to a board and a defconfig.
Below the environment is configured to the `nsh` defconfig of the simulation.

```bash
# Navigate to your NuttX workspace
cd nuttxspace

# Initialize with board and defconfig (sim:nsh)
ntxbuild start sim nsh
```

## 3. Build Your Project
To build the project, use the `build` command, which supports parallel build jobs.

```bash
# Build with default settings
ntxbuild build

# Or, build with parallel jobs
ntxbuild build --parallel 8
```

## 4. Configure Your Build
You can execute configuration changes using menuconfig or even set custom
config options directly from the terminal.

```bash
# Run menuconfig
ntxbuild menuconfig

# Set Kconfig values
ntxbuild kconfig --set-value CONFIG_DEBUG=y
ntxbuild kconfig --set-str CONFIG_APP_NAME="MyApp"
```

## Using Python
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

## Downloading Toolchains
To visualize currently available toolchains, execute the `toolchain list` command:

```bash
$ ntxbuild toolchain list
Available toolchains:
  - clang-arm-none-eabi
  - gcc-aarch64-none-elf
  - gcc-arm-none-eabi
  - xtensa-esp-elf
  - riscv-none-elf
Installed toolchains:
  - xtensa-esp-elf
```

To install, execute the `toolchain install` command using any of the toolchains from the list above.

```bash
$ ntxbuild toolchain install gcc-arm-none-eabi
Installing toolchain gcc-arm-none-eabi for NuttX v12.12.0
✅ Toolchain gcc-arm-none-eabi installed successfully
Installation directory: /home/fdcavalcanti/ntxenv/toolchains
Note: Toolchains are sourced automatically during build.
```

> **_NOTE:_**  Toolchains are automatically appended to PATH when building from the CLI.

> **_NOTE:_**  Toolchains are installed to `~/ntxenv/toolchains`.
