
# API Examples

ntxbuild provides its full API for usage with examples.
It allows the use of Python scripts to execute the same commands available
to the command line, such as: configuring repository, building, creating
workspace and others, with complete access to stdout, stderr and return codes.

## Configuring and Building
This examples shows how to setup and build a NuttX binary using only the Python API.
The script is executed from inside the `nuttxspace`.

```python
from pathlib import Path
from ntxbuild.build import NuttXBuilder

current_dir = Path.cwd()

builder = NuttXBuilder(current_dir, "nuttx-apps")
setup_result = builder.setup_nuttx("sim", "nsh")

# Execute the build with 10 parallel jobs
builder.build(parallel=10)

# You can now clean the environment if needed
builder.distclean()
```

## Apply custom options
ntxbuild allows you to set Kconfig options through the ConfigManager.

```python
from pathlib import Path
from ntxbuild.build import NuttXBuilder
from ntxbuild.config import ConfigManager

current_dir = Path.cwd()

builder = NuttXBuilder(current_dir, "nuttx-apps")
setup_result = builder.setup_nuttx("sim", "nsh")

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
