# Runtime path resolution: self-location and the ${ORIGIN} token

The stack self-locates its own resources (bundled CppInterOp, the cpyrt API
headers, clang's builtin headers) relative to its load path: `libcppjit.so`
calls `dladdr` on itself and joins the baked relative spellings
(`cppjit_backend/lib/...`, `cppjit_backend/include`) onto that directory — see
`cppinterop_paths()` in `src/interop/interop_wrapper.cxx`. `staging.bzl` shows
how the Bazel tree recreates the wheel layout that makes this work. The only
paths a consumer must supply are its *own* toolchain args (e.g.
`--gcc-toolchain`) in `CPPINTEROP_EXTRA_INTERPRETER_ARGS`.

No installer knows its final absolute prefix at build time, and relative paths
break as soon as the process runs from a different cwd (a notebook kernel, a
tool run from $HOME). Args may therefore reference `${ORIGIN}` — the directory
of libcppjit.so itself, mirroring ELF rpath $ORIGIN semantics.

Bazel consumers: the solib dir sits two levels below the runfiles root, so
sibling repos resolve via ORIGIN_RUNFILES_ROOT (defs.bzl), e.g.
`"--gcc-toolchain=" + ORIGIN_RUNFILES_ROOT + "/" + repo_name("@gcc")`.
The expanded args carry literal `..` components; clang handles them fine.

Note: no loader in this repo expands `${ORIGIN}` today. ORIGIN_RUNFILES_ROOT
stays exported for consumers that build such args, but a consumer that needs the
token resolved must expand it itself before the args reach the interpreter.
