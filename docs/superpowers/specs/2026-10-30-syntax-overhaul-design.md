# Phase 1: Syntax Overhaul — Design

**Date:** 2026-10-30
**Scope:** Rewrite syntax highlighting for Hog list files, add a syntax for `hog.conf`, add comment toggling, Goto Symbol support and syntax tests. No Python plugin code (hover, completion, diagnostics, build integration are later phases).

---

## Why

The package is published on Package Control, but its single grammar is buggy and covers only part of what Hog accepts. The VSCode extension ([Hog-CERN/HogVSCode](https://github.com/Hog-CERN/HogVSCode)) has already been brought up to date; Sublime users should get the same highlighting quality. This phase is also the base the later plugin phases build on (scopes the plugin can query).

## Goals

- Correct, complete highlighting of every list-file type Hog supports and of `hog.conf` / `sim.conf`.
- Parity with the VSCode grammars (`syntaxes/hog-list.tmLanguage.json`, `syntaxes/hog-conf.tmLanguage.json` in HogVSCode), and better where Sublime allows it (context-aware sections, see below).
- Ctrl+/ comment toggling and Ctrl+R Goto Symbol in both syntaxes.
- Syntax tests that run with Sublime's built-in test runner, so grammar regressions are caught.

## Non-goals

- Any `.py` plugin code.
- Supporting Sublime Text 3.

## Anti-goals (would make this a failure even if highlighting is better)

- **Breaking existing users.** The list-file syntax must stay at `Packages/Hog/Hog.sublime-syntax`, keep `name: Hog` and keep the top-level scope `source.hog`. Views already assigned to the syntax, user settings files (`Hog.sublime-settings` keyed by syntax name) and color-scheme rules targeting `source.hog` must keep working.
- Highlighting words inside paths as keywords (the current bug: `src/top/x.vhd` colours `top`).
- Flooding the project-wide symbol index (Goto Symbol in Project) with every file of every list.

---

## Constraints

- Sublime Text 4 only. Use `version: 2` sublime-syntax. Minimum build: whatever `version: 2` requires (4075+); state it in the README.
- Releases are published by git tag (`v0.0.1`, `v0.0.2` exist). The next release is `v0.1.0`. **The plan does not create or push any tag.** Releasing is a manual follow-up, in this order: (1) PR to `wbond/package_control_channel` splitting the Hog entry into an ST3 release (`"sublime_text": "<4075"`, pinned to the `v0.0.x` tags) and an ST4 release (`"sublime_text": ">=4075"`, tags from `v0.1.0`); (2) only after it is merged, tag and push `v0.1.0`. Pushing the tag first would auto-update ST3 users to a syntax they cannot load. Record this sequence in the plan's final step and in the PR description, nothing more.
- *(Builder's call)* "Parity with VSCode" means visual parity in spirit; **this document's token tables are the complete specification** and win wherever they differ from the VSCode grammars. Old modifiers such as `runtime=`, `wavefile=`, `dofile=` (pre-2025.2 `.sim` style) are covered by the "unknown `key=value`" rule; no extra keyword list is needed.
- Follow Sublime's scope naming guidelines (https://www.sublimetext.com/docs/scope_naming.html); every scope ends in `.hog` (list syntax) or `.hog-conf` (conf syntax).

---

## Files

| File | Status | Purpose |
|---|---|---|
| `Hog.sublime-syntax` | rewritten in place | List files. `name: Hog`, `scope: source.hog` (unchanged). |
| `Hog Conf.sublime-syntax` | new | `hog.conf` and `sim.conf`. `name: Hog Conf`, `scope: source.hog-conf`. |
| `Comments.tmPreferences` | new | `#` line comment for `source.hog, source.hog-conf`. |
| `Symbol List.tmPreferences` | new | Sections (both syntaxes) and file paths (list syntax) in Goto Symbol; only sections in the project index (`showInIndexedSymbolList` off for paths). |
| `tests/syntax_test_*.{src,sim,con,lst,ext,ipb}`, `tests/syntax_test_hog.conf` (or equivalent name, see below) | new | Syntax tests. |
| `.gitattributes` | new | `tests/ export-ignore`, `docs/ export-ignore` so they are not shipped to users. |
| `README.md` | updated | Supported files, features, ST4 requirement, how to run the tests. |

### File association

- `Hog`: `src sim con lst ext ipb` (adds `ext` and `ipb` to the existing four). `.sub` is deprecated in Hog and deliberately not associated.
- `Hog Conf`: files named exactly `hog.conf` and `sim.conf`. The builder must verify how ST4 matches `file_extensions` against whole filenames (e.g. that `Top/p/hog.conf` gets Hog Conf while `nginx.conf` does not); if a whole-name match is not possible this way, report back before choosing a workaround.

---

## List-file syntax (`source.hog`)

### Line structure

A list file is line-based. Each non-blank, non-comment line is a **file line**: a path, then zero or more space-separated tokens (modifiers, a second path, a hash). *(Builder's call)* A `#` starts a comment only at the start of a line (after optional whitespace) or when preceded by whitespace and outside a quoted string; `src/a#b.vhd` and `--opt=a#b` contain no comment. The same rule applies in the conf syntax: `PART = xc7 # note` ends the value before ` # note`, while `"a # b"` is a string.

*(Builder's call)* **Second path on a line:** any token after the first that contains a `/` or ends in a file extension (`\.\w+$`, e.g. `regs_decode.vhd`) and is not a key=value, option or hash is scoped as a path. Only the first path of a line goes into Goto Symbol (give it an extra marker scope, e.g. `entity.name.file.hog` or `meta.path.first.hog`, that the symbol-list preference selects).

*(Builder's call)* **Quoted strings on file lines:** a key=value or option value may be double-quoted (`lib="x"`, `--synthesis="VHDL"`); it then gets the quoted-string scopes from the property-value row. A path token may also be a double-quoted string (path with spaces): string scopes plus `meta.path.hog`.

`.sim` files may also contain TOML-like sections (Hog2025.2+):

```
#Simulator xsim
[files]
myfile.vhd
mytb.vhd
[properties]
RUNTIME=10us
TOP=TB_fifo
[generics]
MYGENERIC=1
[hog]
HOG_SIMPASS_STR="simulation passed"
```

**Context-sensitivity (improvement over VSCode):** before any section header, and after `[files]`, lines are file lines. After any other section header (`[properties]`, `[generics]`, `[hog]`, or an unknown one), lines are `KEY=VALUE` property lines. A new section header switches context again. VSCode instead guesses property lines by an all-uppercase key; do not copy that heuristic.

### First-line directive

On **line 1 only**, `#Simulator <name>` is a directive rather than a plain comment. It is still scoped as a comment (so toggling/colour schemes treat it as one) but with inner scopes:

`#Simulator xsim` → `comment.line.number-sign.hog meta.directive.hog`, with `#` = `punctuation.definition.comment.hog`, `Simulator` = `keyword.other.directive.hog`, `xsim` = `support.constant.simulator.hog`.

The same word on any later line is an ordinary comment.

### Tokens and scopes

| Token | Example | Scope |
|---|---|---|
| Comment | `# text`, trailing `... # text` | `comment.line.number-sign.hog`, `#` = `punctuation.definition.comment.hog` |
| Section header | `[files]` | `meta.section.hog`; `[` `]` = `punctuation.definition.section.begin/end.hog`; name = `entity.name.section.hog` |
| File path (first token of a file line) | `src/adder.vhd`, `IP/fifo/fifo.xci`, `*/src/*.vhd`, `/afs/cern.ch/x.vhd`, `bar.src` | `meta.path.hog string.unquoted.path.hog` |
| Wildcard inside a path | `*`, `?` | additionally `keyword.operator.wildcard.hog` |
| Second path on a line (`.ipb` VHDL file) | `xml/regs.xml gen/regs_decode.vhd` | same as file path |
| Flag modifier | `nosynth noimpl nosim noadd nogenerate notiming noplace locked SystemVerilog verilog verilog_header XDC source qsys enable` | `storage.modifier.hog` |
| Language-version modifier | `93 1987 1993 2008 2019 1995 2001 2005 2009` | `constant.numeric.integer.decimal.hog` |
| Key=value modifier | `lib=my_lib`, `top=top_fifo`, `topsim=tb`, `path=sub/module`, `scoped_to_ref=uart`, `scoped_to_cells=a/b` | key = `storage.modifier.hog`, `=` = `keyword.operator.assignment.hog`, value = `string.unquoted.hog` (for `path=`, the value gets the path scope instead) |
| Unknown `key=value` after a path | `foo=bar` | same as key=value modifier (Hog may add keys; don't flag them as errors) |
| Tool option (qsys) | `--synthesis=VHDL`, `--part` | `variable.parameter.option.hog`; for `--x=y`, `=` and value as in key=value |
| MD5 hash (`.ext`) | `725cda057150d688c7970cfc53dc6db6` (exactly 32 hex chars) | `constant.other.hash.hog` |
| Unknown bare word after a path | `nosyth` (typo) | no extra scope beyond the line's `meta` scope — leaving it uncoloured is a visible hint |
| Property line key (in non-`[files]` sections) | `RUNTIME`, `MODELSIM.SIMULATE.RUNTIME` | `variable.other.property.hog` |
| Property `=` | | `keyword.operator.assignment.hog` |
| Property value | `10us`, `TB_fifo`, `"simulation passed"`, `true` | `string.unquoted.hog` by default; double-quoted string = `string.quoted.double.hog` with `punctuation.definition.string.begin/end.hog` and `\\.` = `constant.character.escape.hog`; number with optional unit (`10`, `-1.5`, `10us`) = `constant.numeric.hog`; `true`/`false` = `constant.language.boolean.hog` |

Rules that must hold:

- Modifier/keyword recognition happens **only on tokens after the path**, never inside the path token. `src/top/nosim/x.vhd` is one path, nothing inside it is a modifier.
- Numbers are only recognised as whole tokens (versions after a path, numeric property values) — never inside a path or filename (`v1.2/x.vhd`).
- Flags must be whole tokens: `nosimx` is not `nosim`.
- Whitespace around `=` in property lines is allowed (`KEY = VALUE`); in modifiers it is not (`lib=x`).

## Conf syntax (`source.hog-conf`)

INI-style. Examples from the Hog docs:

```
#vivado 2020.2
[main]
PART = xcku15p-ffva1760-2-e
IP_REPO_PATHS = "path1/ path2/"
[synth_1]
STEPS.SYNTH_DESIGN.ARGS.RETIMING = true
[platform:MyTestPlatform1]
[app:MyTestApp1]
[hls:my_hls_component]
[sim_1]
xsim.elaborate.rangecheck = true
```

| Token | Scope |
|---|---|
| Line-1 directive `#<tool> [<tool2>] [<version>]`, e.g. `#vivado 2020.2`, `#vivado vitis_classic 2023.1`, `#vivado 2020.1_AR75210`, `#quartus 19.1.0`, `#vivado` | inside `comment.line.number-sign.hog-conf meta.directive.hog-conf`: tool names = `support.constant.tool.hog-conf`, version = `constant.numeric.version.hog-conf`. Known tools: `vivado vitis_classic vitis_unified quartus planahead libero diamond ghdl`; an unknown word still gets the tool scope (don't over-validate). |
| Comment | `comment.line.number-sign.hog-conf` |
| Section `[main]` | as list syntax, `.hog-conf` suffix. Names may contain `\w . : -`. For `[platform:Name]`, `platform` and `Name` are both inside `entity.name.section.hog-conf`, `:` = `punctuation.separator.hog-conf`. |
| Key | any case, letters/digits/`_`/`.` → `variable.other.property.hog-conf` |
| `=` | `keyword.operator.assignment.hog-conf`; whitespace around it allowed |
| Value | same rules as list-file property values (unquoted string default, quoted string, number with optional unit, boolean) |

## Goto Symbol

- Ctrl+R in list files: section names and file paths (first path of each line). Ctrl+R in conf files: section names.
- Project index (Ctrl+Shift+R): section names only.

---

## Syntax tests

- One test file per list extension (`.src .sim .con .lst .ext .ipb`) plus one conf test, using the standard `# SYNTAX TEST "Packages/Hog/..."` header. Note the header line is line 1, so the line-1 directive tests need their own file whose first line *is* the directive — the builder must check how Sublime's test format handles this (the `SYNTAX TEST` header must itself be line 1) and pick a workable approach (e.g. test only that the directive is not recognised on later lines, and verify line 1 manually), reporting which.
- Each test covers every row of the token tables above, plus the anti-cases: keyword inside a path, number inside a path, partial flag (`nosimx`), directive on a non-first line, uppercase key in `[files]` section treated as a path.
- Tests must pass with Sublime's syntax test runner. If headless running isn't available in this environment, document the manual command (`Tools › Build` with the `Syntax Tests` build on a test file) in the README and state in the plan that tests were not executed automatically.

## Left to the builder

- Context structure and naming inside the `.sublime-syntax` files.
- Exact regexes, as long as the rules above hold.
- Test-file contents beyond the required coverage.
- Wording of the README.
