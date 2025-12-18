# Command Line Usage

## start
Initializes NuttX environment on current directory.
`nuttx-apps` and `nuttx` directories must be present or a custom path can be
passed using the options.

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

## `build`
Builds the firmware. User can select the number of parallel jobs, otherwise
it defauls to one.

```bash
ntxbuild build [OPTIONS]
```

**Options:**
- `--parallel, -j INTEGER`: Number of parallel jobs

**Example:**
```bash
ntxbuild build --parallel 4
```

## `menuconfig`
Opens the Kconfig menu.

```bash
ntxbuild menuconfig
```

## `kconfig`
Executes operations on Kconfig options such as read and set.

```bash
ntxbuild kconfig [OPTIONS] [VALUE]
```

**Options:**
- `--read, -r TEXT`: Path to apps folder
- `--set-value TEXT`: Set Kconfig value
- `--set-str TEXT`: Set Kconfig string
- `--apply, -a`: Apply Kconfig options
- `--merge, -m`: Merge Kconfig file

**Examples:**
```bash
ntxbuild kconfig --set-value CONFIG_DEBUG=y
ntxbuild kconfig --set-str CONFIG_APP_NAME="MyApp"
ntxbuild kconfig merge /path/to/kconfig
ntxbuild kconfig --apply
```

## `install`
Downloads NuttX kernal and application source code to the current directory.

```bash
ntxbuild install
```

## `clean`
Cleans build artifacts.

```bash
ntxbuild clean
```

## `distclean`
Resets the entire environment to its default state (no board configured).

```bash
ntxbuild distclean
```

## `info`
Show binary information.

```bash
ntxbuild info
```
