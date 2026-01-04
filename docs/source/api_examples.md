
# API Examples

ntxbuild provides its full API for usage with examples.
It allows the use of Python scripts to execute the same commands available
to the command line, such as: configuring repository, building, creating
workspace and others, with complete access to stdout, stderr and return codes.

## Configuring and Building (Make)
This example shows how to set up and build a NuttX binary using the Python API.
Choose between the `MakeBuilder` (traditional Makefile-based workflow) or
the `CMakeBuilder` (CMake-based workflow). The script below demonstrates the
`MakeBuilder` usage. Execute the script from inside the `nuttxspace`.

```{note}
Makefiles are supported by default on all boards, while CMakeLists is partially
available.
```

```python
from pathlib import Path
from ntxbuild.build import MakeBuilder

current_dir = Path.cwd()

# Use the Makefile-based builder
builder = MakeBuilder(current_dir, "nuttx", "nuttx-apps")
# Initialize the board/defconfig (returns exit code)
setup_result = builder.initialize("sim", "nsh")

# Execute the build with 10 parallel jobs
builder.build(parallel=10)

# You can now clean the environment if needed
builder.distclean()
```

## CMake-based workflow (CMakeBuilder)
If you prefer a CMake-driven workflow, use `CMakeBuilder`. Key differences:

- **Build system**: `MakeBuilder` drives the traditional `configure.sh` + `make` flow, while
    `CMakeBuilder` configures and builds using `cmake` (the CMake build directory is used).
- **Build directory**: `CMakeBuilder` uses a `build` directory (default) and typically
    uses the Ninja generator by default; `MakeBuilder` builds in-tree using Makefiles.
- **Distclean**: `MakeBuilder.distclean()` is available and removes generated files. `CMakeBuilder.distclean()`
    is not supported and will raise a `RuntimeError` (use `clean()` instead).

Example:

```python
from pathlib import Path
from ntxbuild.build import CMakeBuilder

current_dir = Path.cwd()

# Use the CMake-based builder
cmake_builder = CMakeBuilder(current_dir, "nuttx", "nuttx-apps")
# Initialize the build directory and configure for board:defconfig
ret = cmake_builder.initialize("sim", "nsh")

# Build using 8 parallel jobs
cmake_builder.build(parallel=8)

# Clean build artifacts (note: no distclean on CMakeBuilder)
cmake_builder.clean()
```

## Apply custom options
ntxbuild allows you to set Kconfig options through the `ConfigManager`.

```python
from pathlib import Path
from ntxbuild.build import MakeBuilder
from ntxbuild.config import ConfigManager

current_dir = Path.cwd()

builder = MakeBuilder(current_dir, "nuttx", "nuttx-apps")
builder.initialize("sim", "nsh")

config = ConfigManager(current_dir)
config.kconfig_enable("CONFIG_EXAMPLES_MOUNT")
config.kconfig_set_str("CONFIG_EXAMPLES_HELLO_PROGNAME", "hello_app")

builder.build(parallel=8)
```

## Copying `nuttxspace`
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
