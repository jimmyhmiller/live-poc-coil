# Investigation reproducers

These files are outside the package source roots and are not supported launch paths.

- `source-provider/provider.coil`: source-provider lowering experiment. Repeated submissions exposed an orphan synthetic-entry collision and provider recompilation cost; both are recorded in `coil-bugs`. Production uses the retained before-expand policy.
- `full-jit-paper/fixture.coil`: historical full-renderer-in-JIT latency/lifecycle probe. It contains diagnostic output and the superseded frame-drain code. Production compiles Paper once in the native host and uses `fixtures/paper.coil` through its scalar ABI.

Keep these as reproduction material. Their timings and lifecycle behavior do not establish production correctness.
