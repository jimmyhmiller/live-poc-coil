# Native live Coil proof of concept

## Outcome

Submit an unsaved Coil function definition, then see the new button color in a running Paper window in **less than 100 ms**, with application state intact. Measure from the client starting submission to the first presented frame containing that revision. Compilation and publication timing alone cannot establish this result.

Build the session in `live-poc-coil`. Use `paper-test` as the real application dependency and integration fixture. Use the older Experiments implementations as protocol references and regression material. Keep one production session implementation here; any later move to Experiments should move that implementation rather than duplicate it.

## Current checkpoint — September 15, 2026

The native immutable-view runtime, authenticated protocol, real Paper host and presentation timing are implemented. The 1,000-edit color workload passed: median 42.2 ms, p99 50.0 ms, maximum 77.1 ms, zero misses (20 declared warm-ups). Raw records: `build/deferred-paper-1000.json`. Visible inspection confirmed changed color and preserved click count; automated fresh-render pixel comparison remains outstanding. This run predates source-ledger integration and must be repeated for the final implementation.

The Emacs nREPL client has passed unsaved-buffer and successive-definition integration tests. Desired/accepted source tracking is being integrated. Typed expression results, semantic blocked-entry repair, persistent schema migration, watcher and broader durability gates remain unfinished.

The sections below specify the complete intended implementation and its remaining acceptance gates.

## Evidence gathered

Source baseline: Coil `05145eb`, Experiments `42b1913` with pre-existing controller/host edits, Paper `205c5a4`. Those local edits remain untouched. The installed compiler reports `coil 0.1.0`; record its executable hash in future benchmark artifacts because that version string does not identify a build.

| Component | What we established | Use |
|---|---|---|
| Supplied live-session HTML | Read the design and its proposed semantics, publication protocol, migration rules and delivery gates | Governing design, with earlier Paper measurement |
| Current `coil.jit` | Retained session; prepare/commit/abort; function-owned repair diagnostics; generation tokens | Compiler substrate |
| Single-form regression | Reran against the installed compiler; all assertions passed, including zero accepted-body parse/check/emit and the macro replay tripwire | Initial compiler gate; does not establish immutable invocation views |
| `manual-live` | Inspected migration, typed blocked gates, semantic dependencies and ownership tests | Port the contracts; existing JIT tests still reference removed APIs |
| Headless blocked test | `coil check` fails during workspace discovery on the `live.hooks` module name | Fix package integration before claiming these tests pass |
| `paper-test/examples/minimal.coil` | Real 640 × 480 scene with three stock buttons, persistent selection and lighting, draw/event callbacks | First visible fixture |
| Paper GPU/native benchmark | Existing `present-with-handler`, `addPresentedHandler:` and `presentedTime` sampling | Extend for revision-to-frame timing |
| Paper launcher | Imports the heap-inspector controller and sets namespace roots manually | Replace with a manifest-driven session host |
| Original VM design | Heap frames and program counters support exact continuations | Semantic reference; native boundary suspension has a narrower contract |

The existing manual tests, full Paper launcher, migration behavior and UI latency have not passed an integrated run during this investigation.

## Architecture and ownership

Use one Coil package initially, with modules under `live-poc-coil.*`:

- `runtime`: immutable execution views, typed entry gates, handles, conditions, layout leases and publication.
- `meta`: opted-in definition lowering, semantic dependency analysis and migration generation.
- `session`: one retained JIT, desired/accepted forms, candidate planning and serialized writer queue.
- `protocol`: request decoding, session attachment, form/batch submission and inspection.
- `paper`: stable native callback adapters, publication notices and main-thread integration.
- `metrics`: request/revision/frame correlation and bounded timing storage.
- `watch`: later file-diff client of the same session API.

Keep the Paper platform, renderer, Objective-C registrations and scene storage in one runtime instance. Prove shared storage identity between the host and JIT application. Importing or linking a second copy of Paper static storage is a correctness failure. The same rule applies to live runtime and hook storage.

A top-level application invocation pins one immutable execution view. Its nested live calls resolve through that view. Compile replacements to fresh private symbols. Publish a complete view in one swap; keep previous code while an invocation or callback owns it. A body edit does not wait for an unrelated running invocation. A layout edit closes affected admission and waits for old-layout borrows to drain.

A malformed header rejects a candidate. A valid header with a broken body can produce a typed Blocked entry once the checker contract is established. Preflight the dependency closure before application effects. Paper callbacks return promptly when blocked; queued input owns its arguments and cancellation drops them once. Arbitrary native-stack continuation repair is outside this first implementation.

## Build sequence and exit gates

### 0. Establish the package and compiler contracts

Initialize with `coil new` in an empty staging directory, then integrate its manifest and source into this existing repository while preserving its `.gitignore`. Use the required module namespace. Add `/build`, `/.coil` and `/.worktrees` to ignores; put future worktrees under `.worktrees/`.

Use local manifest dependencies for Paper. Read the language guide before writing Coil. Keep production runtime, transport and adapters in Coil; Python may drive tests and analyze results.

Repair the Experiments package namespace mismatch and update relevant reference fixtures to current retained-session semantics in isolated worktrees. Do not mechanically rename old replace APIs: startup imports, delta submissions and generation ownership changed.

Build a headless contract harness that proves:

1. Prepare/abort leaves accepted entries, roots and revision unchanged.
2. Symbol availability and ownership allow reserving candidate callback leases before visibility.
3. Backend acceptance and runtime publication have one safe ordering, with no recoverable failure after the public swap.
4. Checked headers and resolved dependency identities can be obtained for a partially invalid candidate.
5. Work tracing distinguishes submitted, rechecked, emitted and reused artifacts.

If the SDK cannot support a contract, add a small compiler API and its regression. Do not parse error strings or expose unleased pointers as a substitute. Contracts 2 and 3 gate all publication; contract 4 gates repairable entries.

### 1. Build same-signature native replacement

Implement desired/accepted definitions, stable IDs, a serialized compiler lane, typed entries and immutable execution views. Prepare project/import context once. Lower only a changed implementation plus bounded publication glue.

Tests: old caller sees replacement on its next invocation; a running caller keeps its old consistent view; recursive and mutual calls; two modules with the same leaf name; tracked function values; rejected edit leaves accepted behavior intact; concurrent submission order; abort and shutdown release resources. Trace must show zero parse/check/emit for unrelated accepted bodies and no bootstrap/provider replay.

Return a capability diagnostic for unsupported live forms. Start with concrete same-ABI functions and stable opaque resources, and document that support boundary.

### 2. Measure the real Paper color edit early

Add an integration fixture alongside `paper-test/examples/minimal.coil` that uses Paper's normal buttons, layout, lighting and renderer. Extract a concrete `button-pigment` function returning a checked color value. Keep its caller unchanged, and submit replacements of that function through the session. Also test replacing the existing larger draw function so the result does not depend solely on a tiny helper.

Retain the window, selection, lighting and application state across edits. Register stable draw/event trampolines once. Compile on the worker; deliver publication notices to the main thread and request redraw there. `paper_redraw` currently writes a scene dirty flag; the compiler worker must not call it directly.

Add a main-thread publication pump before frame admission, independent of whether the scene is dirty, plus a stable wakeup. Assert thread affinity. Confirm changes redraw an idle window and survive mouse interactions and window resizing. Verify host/JIT storage identity and fixed callback addresses.

First use a small client of the eventual request API. Add nREPL/editor compatibility in step 3. Do not introduce a separate benchmark-only publication path.

**Exit:** the full latency gate below passes on the named Mac and display. Profile and fix the dominant stage before extending the runtime. Keep this benchmark throughout subsequent work.

### 3. Complete the editor session

Implement form and batch submission with namespace, source span, request ID and base revision. Add expression evaluation with typed value printing, streamed output, diagnostics and completion. `jit-evaluate!` currently discards values, so it needs a generated result adapter or narrow SDK hook.

Connect the existing `coil-repl.el` / `coil-live.el` clients to this session. Exercise actual unsaved-buffer submission and include editor serialization/transport time in a second latency run.

Tests: duplicate request returns its original outcome; stale conflicting revision gets a conflict; multiple clients share one ordered world; timeout does not imply cancellation; effectful eval executes once; bounded output/queues; cancel before commit; reconnect and inspect known request outcomes. Bind locally with a session capability. Document supported nREPL operations without claiming full CIDER compatibility.

### 4. Add blocked entries and one-form repair

Generate checked typed gates from semantic artifacts. Propagate blocked status and revival through resolved dependencies to a fixpoint. Keep desired and accepted revisions separate.

Headless acceptance: submit a schema and dependent functions; evolve the schema with a broken dependent; publish only with complete Ready/Blocked coverage; queue affected work; keep unrelated calls working; repair just the broken function; observe the original request complete once. Include void/aggregate ABIs, owned-argument cancellation, lost-wakeup schedules and old-view pinning.

Paper acceptance: keep the last complete scene on blocked draw, preserve input order in a bounded owned queue, define overflow explicitly, coalesce only permitted pointer/tick events, and keep the event loop responsive. Repair causes a new draw before any partial draw effects have occurred.

### 5. Add typed persistent-state evolution

Implement stable handles, registered roots and explicit layout leases. Generate versioned physical schemas and exact migration edges. Prepare a shadow graph in two passes so aliases and cycles survive. Validate before publication, preserve old roots on failure, and retire owners only after commit. Defaults initialize added fields; a retyped existing value requires a typed transition. Editing an initializer does not reset persistent state.

Tests: add/default, remove/drop, reorder, explicit rename, retype, nested records/sums, owned containers, interior slices, cycles, skipped versions, missing migration then repair, revert as a forward edge, cancellation and shutdown. Inject failures at allocation, partial initialization, validation, native loading and ownership reservation. Count drops, leases and graph allocations.

Paper scenario: moving scene → radius edit → added defaulted field → field retyped to a sum with migration → invalid dependent match → repair only that match. Verify preserved positions, input executed once, live unrelated controls, and unchanged accepted state after a forced migration failure.

### 6. Watcher and durability

Implement the watcher as a source snapshot/diff client. Use Coil's reader and module-qualified identities. Distinguish disk, desired buffer and accepted runtime revisions. Test atomic saves, partial writes, new imports, imported-only edits, deletion, rename, file/buffer conflicts and migration edges applied once.

Then run long-lived replacement, rejection, schema, repair and callback workloads separately. Record metadata, native mappings, lease holders, journal size and RSS. Repeated equivalent edits with no remaining leases must reach bounded retention. Add address/thread sanitizers where supported, differential checks against fresh compilation, native failure injection and orderly callback unregister/shutdown. Run supported compiler targets separately; keep Paper's visible gate on macOS.

## Submit-to-visible measurement

For each request, record:

`client submit → server receive → compile start/end → native prepare/load → commit → main-thread notice → draw revision → GPU submission → drawable presented`

Use a shared native monotonic time basis across local client/host processes; verify the conversion to Paper's presentation clock. Wall-clock timestamps cannot be subtracted for this measurement. Include time spent waiting in the writer queue. An editor integration must measure its clock conversion uncertainty and start before encoding/transmitting the code.

Attach request ID, accepted revision and rendered revision to each sample. Capture the revision while pinning the draw view, then carry it with that exact drawable. A presentation of an older frame must not satisfy the request. Preserve sample storage until presentation and GPU callbacks finish; do not recycle it when the compile acknowledgement arrives.

Extend the existing Paper native benchmark's `PresentationBlock` and `present-with-handler` support with owned per-frame records. Use `presentedTime` as the automated presentation endpoint; GPU completion, `paper_redraw`, target timestamps and commit acknowledgements are intermediate events. Validate the actual changed button with pixel comparisons against a fresh-render reference outside the timed run, and inspect a real visible run. Display presentation timestamps measure system presentation; high-speed capture would be needed for a literal photon-level claim.

### Workload and pass rule

- Name the Mac, OS, display, actual refresh rate, render size/scale, renderer, compiler executable hash, backend, optimization level and source revisions.
- Keep the window visible. Record warm-up and cold startup separately, with a fixed declared warm-up count.
- Run 1,000 alternating color edits. Submit the next edit after presentation of the preceding edit, with varied delay to sample different display phases. Do not discard slow accepted edits.
- Require every successful edit to produce the intended frame and **all 1,000 measured latencies to be below 100 ms**. Report p50, p95, p99, maximum and the miss count. This is a tested-workload criterion, not a hard-real-time OS guarantee.
- Run bursts separately. Account for superseded, rejected, cancelled, timed-out and unpresented revisions explicitly; do not count them as fast successes.
- Repeat with normal pointer activity, a larger draw-body replacement and an imported-module helper edit. Show results per workload.
- Increase unrelated retained definitions and verify bounded body-edit work using both timings and compiler traces. Collect detailed traces separately from the primary timing run and quantify instrumentation overhead.

Provisional engineering budget, to revise from measurements:

| Stage | Budget |
|---|---:|
| Client transport and writer queue | 5 ms |
| Candidate analysis, checking, code generation and native load | 45 ms |
| Publication and main-thread delivery | 5 ms |
| Frame scheduling, drawing and presentation | 30 ms |
| Margin | 15 ms |

These numbers allocate the 100 ms goal; they are not measured results or independent percentile guarantees. The measured end-to-end maximum determines the pass. Avoid debounce/polling delays on explicit submissions. Measure a faster JIT backend or optimization level against both compile latency and Paper frame cost before selecting it.

## First implementation checkpoint

Deliver the package, contract harness, same-ABI replacement and instrumented Paper color slice first. The checkpoint report must contain raw request/frame records, reproduction commands, compiler-work assertions, pixel/state checks, timing distributions and unresolved contract gaps. Expand schema/repair support only with its own acceptance tests.

Project notes and external issues: [live-poc-coil](pad://live-poc-coil).
