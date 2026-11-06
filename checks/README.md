# Custom checks

Each check lives in its own directory, grouped by the tool that runs it:

```
checks/<tool>/<check-name>/<check-name>.<ext>
checks/<tool>/<check-name>/tests/pass/*.cpp
checks/<tool>/<check-name>/tests/fail/*.cpp
```

| tool          | implementation         | runs as                                    |
|---------------|------------------------|--------------------------------------------|
| `clang-query` | `<check-name>.query`   | `clang-query -f <check-name>.query <case>` |
| `cppcheck`    | `<check-name>.py`      | `cppcheck --addon=<check-name>.py <case>`  |

`clang-query` checks are written in the AST matcher language used by
clang-tidy's query-based `CustomChecks`, so a query can be moved into a
`.clang-tidy` configuration unchanged once clang-tidy 22+ is available.
Queries should restrict themselves to `isExpansionInMainFile()` and report the
offending node as the match root.

`cppcheck` checks are addons using `cppcheck.checker`; findings are reported
with ids of the form `<check-name>-<function-name>`.

## Test cases

Every check needs at least one `pass` case and one `fail` case, and may have as
many of each as needed.

* A `pass` case must produce no findings from the check.
* A `fail` case marks every line that must be reported with
  `// expect-finding`; the check must report exactly those lines.

Every case is also compiled as C++20 with the project's warnings, so it must be
valid, warning-free code; clang-tidy runs over it too, with the checks that
duplicate the custom checks turned off in `checks/.clang-tidy`.

## Running

```
cmake -S . -B build
ctest --test-dir build --output-on-failure
```

or directly, optionally narrowed with `--tool`, `--check`, or case paths:

```
tools/run_check_tests.py
```

Set `CLANG_QUERY` / `CPPCHECK` to choose a specific tool binary. Cases for a
tool that is not installed are reported as skipped.
