# InsurgeNT `project.yaml` layout specifications

## Mandatory fields

`project`       - This corresponds to the name of your (sub)project.
`authors`       - The author(s) of the project.
`license`       - The license used by your project (only mandatory for the top level project, subprojects automatically inherit that of the parent project).
`language`      - The used programming language (either `c` or `cpp/c++`).
`standard`      - ISO standard used (only `ansic`, `c99` and `c(++)11` and above are supported).
`compiler`      - The compiler used for your project (subsequently, the corresponding linker will be used).
`project_dirs`  - Source directory/directories of your project.
`project_type`  - Type of the project, either `executable` or `library`.
`output`        - Name of the final output file.

## Optional Fields

`description`   - A description of your project.
`version`       - The version of your project (defaulted to `0.0.1`).
`build_rule`    - The build rule of your project (defaulted to `all`).
`clean_rule`    - The clean rule of your project (defaulted to `clean`).
`compiler_flags`- The compiler flags used by your project (will override `make` flags, be careful!).
    - `common`  - Language-agnostic compiler flags.
    - `c`       - C-only language flags.
    - `cpp`     - C++-only language flags.
    - `ar`      - Archiver flags.
    - `ld`      - Linker flags.
    - `as`      - Assembler flags.
`subprojects`   - The subproject(s) of your main project.