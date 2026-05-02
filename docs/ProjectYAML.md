# InsurgeNT `project.yaml` layout specifications

## Mandatory fields

* `project`       - This corresponds to the name of your (sub)project.
* `authors`       - The author(s) of the project.
* `license`       - The license used by your project (only mandatory for the top level project, subprojects automatically inherit that of the parent project).
* `language`      - The used programming language (either `c` or `cpp/c++`).
* `standard`      - ISO standard used (only `ansic`, `c99` and `c(++)11` and above are supported).
* `compiler`      - The compiler used for your project (subsequently, the corresponding linker will be used).
* `project_dirs`  - Source directory/directories of your project.
* `project_type`  - Type of the project, either `executable`, `header_lib` or `library`.
* `output`        - Name of the final output file.

## Optional Fields

* `bootstrap`     - For bootstrapping build.
    - `task`   - Task name
    - `command`- Command to run
* `description`   - A description of your project.
* `version`       - The version of your project (defaulted to `0.0.1`).
* `compiler_flags`- The compiler flags used by your project.
    - `global`  - Global flags (inherited by all subprojects).
    - `common`  - Language-agnostic compiler flags.
    - `c`       - C-only language flags.
    - `cpp`     - C++-only language flags.
    - `ar`      - Archiver flags.
    - `ld`      - Linker flags.
    - `as`      - Assembler flags.
* `subprojects`   - The subproject(s) of your main project, specified as subdirectories.
* `ignore`        - A list of file(s)/folder(s) to ignore when resolving source files.
* `include_paths` - Include paths to pass to the compiler, they're resolved automatically by default.
* `unit_tests`    - Optional native unit test harness (separate executable from the main ``output``).
    - ``project_dirs`` - One directory or a list of directories containing test-only sources (scanned like main sources: ``.c``, ``.cpp``, …).
    - ``output``     - Relative path for the linked test executable (for example ``bin/run_tests``). InsurgeNT compiles sources under ``project_dirs``, links this binary, then runs it when you invoke ``insurgent test`` or the shell command ``test``.
    - ``link_project`` - Optional boolean. If ``true``, the main ``output`` archive is appended when linking tests (requires ``project_type: library``). If ``false``, that archive is never linked. If omitted, InsurgeNT links the main archive automatically **only when** ``project_type`` is ``library`` (runs a normal main build first so the static library exists).
    - ``libraries``  - Optional list of extra static library paths **relative to the project root** (for example vendor archives or another subproject’s ``.a``), appended after the test objects when linking.

Executable projects cannot use ``link_project: true``. To test code from an executable-shaped tree, extract it into a ``library`` target or list archives under ``libraries``.