# Hog Sublime Text Package

Syntax support for [Hog (HDL-on-git)](https://cern.ch/hog) projects.

## Supported files

| Syntax | Files |
|---|---|
| **Hog** | list files: `.src`, `.sim`, `.con`, `.lst`, `.ext`, `.ipb` |
| **Hog Conf** | `hog.conf` and `sim.conf` |

## Features

- **List files**: file paths (with `*`/`?` wildcards), modifiers (`nosynth`, `noimpl`, `nosim`, `locked`, `93`, `2008`, ...), `lib=`/`top=`/`topsim=`/`path=`/`scoped_to_ref=` and other `key=value` properties, tool options such as `--synthesis=VHDL`, MD5 hashes in `.ext` files and comments. Misspelt modifiers are left uncoloured.
- **`.sim` files**: `[files]`, `[properties]`, `[generics]` and `[hog]` sections. Lines in `[files]` are files, lines in the other sections are `KEY=VALUE` properties. The `#Simulator <name>` first line is highlighted.
- **`hog.conf`**: sections (including `[platform:<name>]`, `[app:<name>]`, `[hls:<name>]`), properties, strings, numbers, booleans and the `#<tool> <version>` first line.
- **Toggle comment** (<kbd>Ctrl</kbd>+<kbd>/</kbd>) in both syntaxes.
- **Goto Symbol** (<kbd>Ctrl</kbd>+<kbd>R</kbd>): sections and files. **Goto Symbol in Project** (<kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>R</kbd>): sections.

## Requirements

Sublime Text 4 (build 4075 or later). Sublime Text 3 users stay on release `v0.0.2`.

## Development

The tests are in `tests/`:

- `syntax_test_hog.*`: Sublime syntax tests, one per file type.
- `test_hog.py`: checks that syntax tests cannot express (first-line directives, file associations, comment toggling, symbols).

They run headless in a container with the runner of [UnitTesting](https://github.com/SublimeText/UnitTesting), which needs Docker or podman:

```sh
git clone https://github.com/SublimeText/UnitTesting ../UnitTesting
tests/run_syntax_tests.sh ../UnitTesting
```

The script also accepts the UnitTesting checkout in the `UNITTESTING_DIR` environment variable. Inside Sublime Text, the syntax tests can also be run by opening a `syntax_test_*` file and using **Tools › Build**.
