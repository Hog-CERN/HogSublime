# Syntax Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite the Hog list-file syntax, add a `hog.conf` syntax, comment toggling, Goto Symbol and syntax tests, for Sublime Text 4, without breaking existing users.

**Architecture:** Two `version: 2` sublime-syntax files (`Hog.sublime-syntax` rewritten in place, new `Hog Conf.sublime-syntax`), two `.tmPreferences` files, and Sublime syntax-test files under `tests/`. Tests run locally, headless, through `tests/run_syntax_tests.sh`, a thin wrapper around the Docker/podman runner of [SublimeText/UnitTesting](https://github.com/SublimeText/UnitTesting) (`docker/run_tests.py`), which runs the syntax tests and the syntax compatibility checks in Sublime Text build 4215.

**Tech Stack:** Sublime Text 4 sublime-syntax (YAML, Oniguruma regex), tmPreferences (plist XML).

**Spec:** `docs/superpowers/specs/2026-10-30-syntax-overhaul-design.md` — read it in full; its token tables are the source of truth for every scope name.

## Global Constraints

- `Hog.sublime-syntax` stays at the repo root with `name: Hog` and `scope: source.hog`. Never rename it.
- New conf syntax: file `Hog Conf.sublime-syntax`, `name: Hog Conf`, `scope: source.hog-conf`.
- Both syntaxes use `version: 2`; ST4 only, minimum build 4075.
- Every scope ends in `.hog` (list) or `.hog-conf` (conf).
- List `file_extensions`: `src sim con lst ext ipb` (no `sub`). Conf `file_extensions`: `hog.conf`, `sim.conf`.
- No Python files. No CI configuration. No git tags created or pushed.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **A path with a modifier word as a directory** (`src/top/nosim/lib/x.vhd`) — the whole token is a path with no `storage.modifier`. Pinned in Task 2 `syntax_test_hog.src`.
2. **Tabs or multiple spaces between tokens** (`x.vhd\t\tnosim`, `x.vhd   lib=a`) — modifiers still recognised. Pinned in Task 2.
3. **Windows line endings / trailing whitespace** after the last token (`x.vhd nosim   `) — `nosim` still a modifier; no stray scope leaks onto the next line. Pinned in Task 2 (trailing-space case; CRLF is verified manually in Task 5).
4. **Unterminated double-quoted string** on a property line (`HOG_SIMPASS_STR="oops`) — the string ends at end of line and the next line highlights normally. Pinned in Task 3 and Task 4.
5. **Indented section header or indented comment** (`  [files]`, `   # x`) — still a section / comment. Pinned in Task 3 and Task 4.

---

## File structure

| Path | Responsibility | Task |
|---|---|---|
| `tests/run_syntax_tests.sh` | Run Sublime's headless syntax tests against this repo | 1 |
| `.gitattributes` | Keep `tests/` and `docs/` out of the installed package | 1 |
| `Hog.sublime-syntax` | List files (file lines, sections, properties, directive) | 2, 3 |
| `tests/syntax_test_hog.{src,con,lst,ext,ipb}` | List file-line tests | 2 |
| `tests/syntax_test_hog.sim` | Sections, properties, directive tests | 3 |
| `Hog Conf.sublime-syntax` | `hog.conf` / `sim.conf` | 4 |
| `tests/syntax_test_hog.conf` | Conf tests | 4 |
| `Comments.tmPreferences`, `Symbol List - Files.tmPreferences`, `Symbol List - Sections.tmPreferences` | Ctrl+/ and Goto Symbol | 5 |
| `README.md` | User docs | 6 |

Syntax-test assertion syntax reminder: the comment token is `#`, so assertion lines start with `#`. `# <-` asserts the column of the `#` on the line above; `#  ^^^ scope` asserts the columns under the carets; `- scope` asserts absence. Every test file's first line is `# SYNTAX TEST "Packages/Hog/<syntax file>"`. Caret columns in this plan were aligned by hand: if an assertion fails only because its carets are off by a column and the intended token is unambiguous, fix the carets, never the syntax to fit them.

---

### Task 1: Test tooling

**Files:**
- Create: `tests/run_syntax_tests.sh`, `.gitattributes`
- Create (placeholder): `tests/syntax_test_hog.src`

**Interfaces:**
- Produces: `tests/run_syntax_tests.sh [UNITTESTING_DIR]` — exit 0 when all syntax tests and compatibility checks pass, non-zero otherwise. The UnitTesting checkout defaults to `$UNITTESTING_DIR`. Every later task's verification step is `tests/run_syntax_tests.sh`.

- [ ] **Step 1: Write a placeholder test that must fail against the current syntax**

`tests/syntax_test_hog.src`:
```
# SYNTAX TEST "Packages/Hog/Hog.sublime-syntax"
src/top/x.vhd
#   ^^^ - keyword
```

- [ ] **Step 2: Write `tests/run_syntax_tests.sh`**

Takes a local clone of `https://github.com/SublimeText/UnitTesting` (argument or `$UNITTESTING_DIR`). Runs `python3 -I "$UT/docker/run_tests.py" "<repo root>" --package-name Hog --no-unit-tests` and propagates its exit status. `--package-name Hog` is required: the checkout directory is `HogSublime`, but test headers reference `Packages/Hog/...`. Prints a usage message and exits 2 if no checkout is given or `docker/run_tests.py` is missing. `set -euo pipefail`, executable bit set. Note: the runner syncs only files not ignored by git, so new files are picked up before they are committed.

- [ ] **Step 3: Run it; expect FAIL**

Run: `tests/run_syntax_tests.sh`
Expected: non-zero exit, one failed assertion in `syntax_test_hog.src` line 3 (the current regex scopes `top` in the path as `keyword`). If the exit status is 0 despite the failure, the wrapper must detect failure from the output (`=== SYNTAX TESTS OUTPUT ===` section not ending in `OK`) instead; fix the wrapper before moving on.

- [ ] **Step 4: Write `.gitattributes`**

```
/tests/       export-ignore
/docs/        export-ignore
/.gitattributes export-ignore
```

- [ ] **Step 5: Commit** (placeholder test is allowed to fail at this commit; Task 2 replaces it)

```bash
git add tests .gitattributes
git commit -m "Add syntax test tooling"
```

---

### Task 2: List syntax — file lines

Rewrite `Hog.sublime-syntax` from scratch (keep header fields per Global Constraints) covering comments and file lines. Sections/properties/directive come in Task 3; structure the contexts so Task 3 can add a section header rule that `set`s between a `files` body context and a `properties` body context.

**Files:**
- Modify: `Hog.sublime-syntax` (full rewrite)
- Test: `tests/syntax_test_hog.src` (replace placeholder), `tests/syntax_test_hog.con`, `tests/syntax_test_hog.lst`, `tests/syntax_test_hog.ext`, `tests/syntax_test_hog.ipb`

**Interfaces:**
- Produces, for Tasks 3 and 5:
  - context `file-line` (one list-file line: path then tokens, pops at end of line), and context `files-body` that includes `comments` and `file-line`.
  - context `comments` (`#` at line start or after whitespace → `comment.line.number-sign.hog`).
  - context `quoted-string` (`string.quoted.double.hog`, ends at `"` or end of line).
  - the first path token of each line carries `meta.path.hog string.unquoted.path.hog entity.name.file.hog`; later path tokens carry `meta.path.hog string.unquoted.path.hog` only. Task 5's symbol list selects `entity.name.file.hog`.

- [ ] **Step 1: Write the failing tests**

`tests/syntax_test_hog.src` must contain at least these cases (assertions shown for the key columns; write full caret coverage of each token):

```
# SYNTAX TEST "Packages/Hog/Hog.sublime-syntax"
src/top/nosim/lib/x.vhd lib=my_lib nosim 93
# <- meta.path.hog string.unquoted.path.hog entity.name.file.hog
#       ^^^^^ meta.path.hog - storage.modifier
#                       ^^^ storage.modifier.hog
#                          ^ keyword.operator.assignment.hog
#                           ^^^^^^ string.unquoted.hog
#                                  ^^^^^ storage.modifier.hog
#                                        ^^ constant.numeric.integer.decimal.hog
v1.2/a.vhd 2008
#^^^ - constant.numeric
#          ^^^^ constant.numeric.integer.decimal.hog
*/src/*.vhd nosynth noimpl
# <- keyword.operator.wildcard.hog
#     ^ keyword.operator.wildcard.hog
#           ^^^^^^^ storage.modifier.hog
#                   ^^^^^^ storage.modifier.hog
x.vhd nosimx nosyth
#     ^^^^^^ - storage.modifier
#            ^^^^^^ - storage.modifier
x.vhd		nosim
#      ^^^^^ storage.modifier.hog
x.vhd   lib=a   
#       ^^^ storage.modifier.hog
x.vhd nosim   
#     ^^^^^ storage.modifier.hog
top.v top=top_module topsim=tb_top SystemVerilog verilog_header
#     ^^^ storage.modifier.hog
#                    ^^^^^^ storage.modifier.hog
#                                  ^^^^^^^^^^^^^ storage.modifier.hog
#                                                ^^^^^^^^^^^^^^ storage.modifier.hog
bar.src lib=my_library path=path/to/submodule
#                           ^^^^^^^^^^^^^^^^^ meta.path.hog string.unquoted.path.hog - entity.name.file
ip/fifo.xci locked   # trailing comment
#           ^^^^^^ storage.modifier.hog
#                    ^ comment.line.number-sign.hog punctuation.definition.comment.hog
src/a#b.vhd --opt=a#b foo=bar
#    ^ - comment
#                  ^ - comment
#                     ^^^ storage.modifier.hog
#                         ^^^ string.unquoted.hog
sys.qsys --synthesis=VHDL nogenerate noadd
#        ^^^^^^^^^^^ variable.parameter.option.hog
#                   ^ keyword.operator.assignment.hog
#                    ^^^^ string.unquoted.hog
#                         ^^^^^^^^^^ storage.modifier.hog
#                                    ^^^^^ storage.modifier.hog
"dir with space/x.vhd" lib="my lib"
# <- meta.path.hog string.quoted.double.hog punctuation.definition.string.begin.hog
#                          ^^^^^^^^ string.quoted.double.hog
   # indented comment
#  ^^^^^^^^^^^^^^^^^^ comment.line.number-sign.hog
```

`tests/syntax_test_hog.con`: `constr.xdc nosynth`, `constr.xdc scoped_to_ref=uart_tx_ctl`, `constr.xdc scoped_to_cells=uart_tx_i0/uart_tx_ctl_i0`, `pins.sdc notiming noplace`, `diamond.lpf enable`, `x.xdc XDC` — flags `storage.modifier.hog`, `scoped_to_*` keys `storage.modifier.hog`, values `string.unquoted.hog`.

`tests/syntax_test_hog.lst`: two plain file lines and one nested list `common.src lib=shared` — paths scoped, `lib` modifier.

`tests/syntax_test_hog.ext`:
```
/afs/cern.ch/project/restricted/file_1.vhd  725cda057150d688c7970cfc53dc6db6
#                                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ constant.other.hash.hog
file_2.xci 725cda05
#          ^^^^^^^^ - constant.other.hash
```

`tests/syntax_test_hog.ipb`:
```
xml/regs.xml gen/regs_decode.vhd
#            ^^^^^^^^^^^^^^^^^^^ meta.path.hog string.unquoted.path.hog - entity.name.file
regs.xml regs_decode.vhd
#        ^^^^^^^^^^^^^^^ meta.path.hog - entity.name.file
```

- [ ] **Step 2: Run; expect FAIL**

Run: `tests/run_syntax_tests.sh`
Expected: many failed assertions across the five files.

- [ ] **Step 3: Implement the file-line contexts in `Hog.sublime-syntax`**

Token rules (exact lists from the spec, whole-token matches only, token boundary = whitespace, `#`-comment, or end of line):
- flags: `nosynth noimpl nosim noadd nogenerate notiming noplace locked SystemVerilog verilog verilog_header XDC source qsys enable`
- versions: `93 1987 1993 2008 2019 1995 2001 2005 2009`
- hash: exactly 32 `[0-9a-fA-F]`
- options: `--[\w-]+`, optionally `=value`
- key=value: `[A-Za-z_][\w.-]*=` followed by value (`path=` value uses path scopes)
- later path: contains `/` or matches `\.\w+$` within the token
- anything else: no scope.
Wildcards `*` `?` inside any path token get `keyword.operator.wildcard.hog`.

- [ ] **Step 4: Run; expect PASS**

Run: `tests/run_syntax_tests.sh`
Expected: exit 0, all assertions pass.

- [ ] **Step 5: Commit**

```bash
git add Hog.sublime-syntax tests
git commit -m "Rewrite list-file syntax for file lines and modifiers"
```

---

### Task 3: List syntax — sections, properties, first-line directive

**Files:**
- Modify: `Hog.sublime-syntax`
- Test: `tests/syntax_test_hog.sim`

**Interfaces:**
- Consumes: `files-body`, `comments`, `quoted-string` from Task 2.
- Produces: `meta.section.hog` / `entity.name.section.hog` for Task 5's symbol list.

- [ ] **Step 1: Write the failing tests**

`tests/syntax_test_hog.sim`:
```
# SYNTAX TEST "Packages/Hog/Hog.sublime-syntax"
#Simulator xsim
# <- comment.line.number-sign.hog - meta.directive
#^^^^^^^^^ - keyword.other.directive
tb_before_sections.vhd
# <- meta.path.hog
[files]
# <- meta.section.hog punctuation.definition.section.begin.hog
#^^^^^ entity.name.section.hog
#     ^ punctuation.definition.section.end.hog
myfile.vhd
# <- meta.path.hog entity.name.file.hog
RUNTIME=10us
# <- meta.path.hog
[properties]
RUNTIME=10us
# <- variable.other.property.hog
#      ^ keyword.operator.assignment.hog
#       ^^^^ constant.numeric.hog
TOP = TB_fifo
#     ^^^^^^^ string.unquoted.hog
MODELSIM.SIMULATE.RUNTIME=-1.5
# <- variable.other.property.hog
#                         ^^^^ constant.numeric.hog
ACTIVE=true # comment
#      ^^^^ constant.language.boolean.hog
#           ^ comment.line.number-sign.hog
HOG_SIMPASS_STR="oops
#               ^^^^^ string.quoted.double.hog
  [generics]
# ^ meta.section.hog
MYGENERIC=1
# <- variable.other.property.hog
#         ^ constant.numeric.hog
[hog]
HOG_SIMPASS_STR="sim \"passed\""
#               ^^^^^^^^^^^^^^^^ string.quoted.double.hog
#                    ^^ constant.character.escape.hog
[files]
back.vhd nosim
# <- meta.path.hog
#        ^^^^^ storage.modifier.hog
```
Line 2 asserts the directive is *not* recognised on a non-first line (line 1 is the test header). The positive line-1 case is checked manually in Step 4.

- [ ] **Step 2: Run; expect FAIL**

Run: `tests/run_syntax_tests.sh`
Expected: failures only in `syntax_test_hog.sim`.

- [ ] **Step 3: Implement**

- Section header rule (indent allowed, name `[\w.:-]+`) available in every body context; `[files]` sets `files-body`, any other name sets `properties-body`.
- `properties-body`: `KEY` (`[A-Za-z_][\w.]*`), optional spaces, `=`, value per spec (default `string.unquoted.hog`; quoted string; number `-?\d+(\.\d+)?[A-Za-z]*` as whole value token; `true|false`), trailing comment rule as Task 2.
- First-line directive: `main` pushes a one-shot context that tries `^(#)(Simulator)\s+(\S+)` (scopes per spec: `meta.directive.hog`, `keyword.other.directive.hog`, `support.constant.simulator.hog`, all within `comment.line.number-sign.hog`) and otherwise pops with a zero-width match, so only line 1 can match.

- [ ] **Step 4: Verify**

Run: `tests/run_syntax_tests.sh` → exit 0.
Manual: in ST4, open a scratch `.sim` file whose first line is `#Simulator xsim`; `Tools › Developer › Show Scope Name` on `Simulator` shows `keyword.other.directive.hog`. Record the result in the commit message body.

- [ ] **Step 5: Commit**

```bash
git add Hog.sublime-syntax tests/syntax_test_hog.sim
git commit -m "Add sections, properties and simulator directive to list syntax"
```

---

### Task 4: Conf syntax

**Files:**
- Create: `Hog Conf.sublime-syntax`
- Test: `tests/syntax_test_hog.conf`

**Interfaces:**
- Produces: `entity.name.section.hog-conf` for Task 5.

- [ ] **Step 1: Write the failing tests**

`tests/syntax_test_hog.conf` (header `# SYNTAX TEST "Packages/Hog/Hog Conf.sublime-syntax"`), covering:
- `#vivado 2020.2` on line 2 → `comment.line.number-sign.hog-conf - meta.directive`.
- `[main]`, `  [synth_1]`, `[platform:MyTestPlatform1]` (`platform`, `:`, `MyTestPlatform1` all `entity.name.section.hog-conf`; `:` also `punctuation.separator.hog-conf`), `[hls:my_hls_component]`, `[sim_1]`.
- `PART = xcku15p-ffva1760-2-e` → key `variable.other.property.hog-conf`, `=` `keyword.operator.assignment.hog-conf`, value `string.unquoted.hog-conf`.
- `IP_REPO_PATHS = "path1/ path2/"` → `string.quoted.double.hog-conf`.
- `STEPS.SYNTH_DESIGN.ARGS.RETIMING = true` → `constant.language.boolean.hog-conf`.
- `xsim.elaborate.rangecheck = true` (lowercase key) → `variable.other.property.hog-conf`.
- `MAX_THREADS=16` → `constant.numeric.hog-conf`.
- `PART = xc7 # note` → `xc7` `string.unquoted.hog-conf`, `#` `comment.line.number-sign.hog-conf`.
- `GEN="oops` unterminated, next line `KEY=1` → `KEY` `variable.other.property.hog-conf`.
- `   # indented comment` → comment.

- [ ] **Step 2: Run; expect FAIL**

Run: `tests/run_syntax_tests.sh`
Expected: runner reports the conf syntax file missing / all conf assertions fail.

- [ ] **Step 3: Implement `Hog Conf.sublime-syntax`**

Header per Global Constraints, `file_extensions: [hog.conf, sim.conf]`. Same rules as Task 3's `properties-body` and section header, with `.hog-conf` scopes. Line-1 directive: `^(#)(\w+)(?:\s+(\w+))?(?:\s+([\d][\w.]*))?` — tool-name groups `support.constant.tool.hog-conf`, version `constant.numeric.version.hog-conf`, inside `comment.line.number-sign.hog-conf meta.directive.hog-conf`; one-shot as in Task 3. Do not include `Hog.sublime-syntax` (keep the two independent).

- [ ] **Step 4: Verify**

Run: `tests/run_syntax_tests.sh` → exit 0.
Manual in ST4: a file named `hog.conf` opens as *Hog Conf*; `sim.conf` opens as *Hog Conf*; `nginx.conf` does not; first line `#vivado vitis_classic 2023.1` shows both tool scopes and the version scope. If `hog.conf` does not auto-select the syntax, stop and report (spec requires this before any workaround).

- [ ] **Step 5: Commit**

```bash
git add "Hog Conf.sublime-syntax" tests/syntax_test_hog.conf
git commit -m "Add Hog Conf syntax for hog.conf and sim.conf"
```

---

### Task 5: Comment toggling and Goto Symbol

**Files:**
- Create: `Comments.tmPreferences`, `Symbol List - Files.tmPreferences`, `Symbol List - Sections.tmPreferences`
- Test: append symbol assertions to `tests/syntax_test_hog.src`, `tests/syntax_test_hog.sim`, `tests/syntax_test_hog.conf`

**Interfaces:**
- Consumes: `entity.name.file.hog`, `entity.name.section.hog`, `entity.name.section.hog-conf`.

- [ ] **Step 1: Write the failing tests**

Using ST4 syntax-test symbol assertions (`@@@ local-definition` for symbols shown in Ctrl+R only, `@@@ definition` for indexed ones): first path of a `.src` line → `local-definition`; second path on an `.ipb`-style line → no symbol; section name in `.sim` and `.conf` → `definition`. If build 4215's runner does not support symbol assertions, drop this step, note it in the commit, and verify Step 4's manual checks instead.

- [ ] **Step 2: Run; expect FAIL** — `tests/run_syntax_tests.sh` reports missing symbols.

- [ ] **Step 3: Implement**

- `Comments.tmPreferences`: scope `source.hog, source.hog-conf`; `shellVariables` `TM_COMMENT_START` = `# `.
- `Symbol List - Files.tmPreferences`: scope `source.hog entity.name.file.hog`; `showInSymbolList` 1, `showInIndexedSymbolList` 0.
- `Symbol List - Sections.tmPreferences`: scope `source.hog entity.name.section.hog, source.hog-conf entity.name.section.hog-conf`; `showInSymbolList` 1, `showInIndexedSymbolList` 1.

- [ ] **Step 4: Verify**

`tests/run_syntax_tests.sh` → exit 0. Manual in ST4: Ctrl+/ on a list line and a conf line inserts `# `; Ctrl+R in a `.src` shows paths and sections; Goto Symbol in Project shows sections but not paths; a CRLF `.src` file (Review Focus 3) highlights identically.

- [ ] **Step 5: Commit**

```bash
git add *.tmPreferences tests
git commit -m "Add comment toggling and Goto Symbol preferences"
```

---

### Task 6: README and release notes

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Rewrite `README.md`**

Sections: what the package does (both syntaxes, supported extensions `.src .sim .con .lst .ext .ipb`, `hog.conf`, `sim.conf`); features (highlighting summary, Ctrl+/, Ctrl+R); requirements (Sublime Text 4, build 4075+; ST3 users stay on v0.0.2); development (running `tests/run_syntax_tests.sh` with a clone of SublimeText/UnitTesting and Docker or podman). Keep the link to https://cern.ch/hog.

- [ ] **Step 2: Verify** — every extension in `Hog.sublime-syntax` and `Hog Conf.sublime-syntax` `file_extensions` appears in the README; `tests/run_syntax_tests.sh` exit 0.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "Update README for syntax overhaul"
```

- [ ] **Step 4: Hand-off note (no action)**

Report to the user, verbatim in substance: release requires (1) a PR to `wbond/package_control_channel` splitting the Hog entry into an ST3 release (`"sublime_text": "<4075"`, `v0.0.x` tags) and an ST4 release (`"sublime_text": ">=4075"`, tags from `v0.1.0`); (2) only after it merges, tag and push `v0.1.0`. Do not tag or push.
