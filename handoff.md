# Live Coil handoff

**Status (2026-09-16): this is a working proof of concept, not a finished generic hot-reload system.** Live code publication, persistent roots, transactional schema migration, blocked-code repair, and the real Paper host work on the covered cases. Do not describe arbitrary Coil values as migratable or the final under-100-ms visible-frame goal as reverified. The last 1,000-color-edit latency run predates the latest schema and input changes.

## Repositories and delivered commits

- This repository: `live-poc-coil`, `main` at `b788421` (`Use generated migration implementations for schema edges`), pushed to `origin/main`.
- Compiler and standard library: `../coil/.worktrees/compositional-migration-final`, branch `feature/compositional-migration-final` at `fec3f47` (`Keep distinct generated impls visible across types`), pushed to origin. Its verified self-hosted compiler and standard library were installed globally on this machine. Check `command -v coil` and record the executable hash before a new benchmark; `coil 0.1.0` is not a unique build identifier.
- Both working trees were clean after those commits. Check again before starting. The Coil worktree lives under `.worktrees` as required by the project instructions.
- Project notes: `pad use live-poc-coil`; compiler notes: `pad use coil`; compiler bug reports: `pad use coil-bugs`. Read the instructions in Coil's `AGENTS.md` before editing that repository. Record newly discovered Coil bugs in `coil-bugs`; keep project status in the project pads.

## What currently works

- A retained Coil compiler accepts live definitions and expressions. Native calls pin immutable execution views; replacements publish without changing an in-flight call. Desired and accepted source, diagnostics, request receipts, cancellation, and deferred blocked-code repair are implemented.
- The Paper app runs in one host with native draw/event callbacks. The moving fixture has exercised radius edits, adding a defaulted field, a typed `bool`-to-sum field transition, blocked drawing, one-form repair, independent input domains, and forced allocation and validation failures in a visible window.
- Every ordinary live `defstruct` is versioned without an annotation. `letonce` keeps root identity and value across initializer edits; `reset-state!` is explicit. Added/reordered fields, checked defaults, explicit field renames (`migrate ... :from ...`), and typed field transitions have tested paths. Failed preparation leaves accepted code, state, and UI intact; a corrected submission can retry.
- Nested record changes version containing records. Runtime schema edges now invoke generated `Migration` implementations. The tested recursive cases include `Inner → Outer → Envelope`, `ArrayList` elements whose physical size changes, and borrowed interior slices. Coil's resolver fix retains multiple implementations emitted from one template; the regression is `tests/compiler/features/generated_impl_same_origin.coil` in the Coil repository.
- At the last verification, 76/76 native tests and all five headless protocol suites passed on the corrected candidate compiler. Coil's `modernize-fast`, generated-code gate, full self-hosting fixpoint, and installed-compiler regression passed. The archived 1,000-schema-edit durability run passed; its measurements and scope are in `docs/measurements/`.

## What is **not** complete

1. **Arbitrary pure-Coil type composition.** `src/migration.coil` has `ValuePolicy` and `Migration` traits and generic policies for pointers, slices, and `ArrayList`; `src/schema_adapters.coil` generates directed record migration. This does not yet cover every owned container, nested resource-bearing element and cleanup path, sum variant evolution, or generic schema declaration/instantiation. Implement each remaining ownership and migration rule through the same recursive policy contract. Prove alias/cycle preservation, correct drop counts, failure rollback, and successful retry. Do not add an opt-in struct annotation or a second field-copy migration path.
2. **Compiler generic trait-wrapper limitation.** Direct `migration/migrate-value` dispatch works and is used by runtime edges. A wrapper with bounds like `migrate! [Old (New (Migration Old))]` fails when a generic impl's source type is absent from `Self`; a checker-only experiment then failed in monomorphization and was reverted. The exact reproduction and affected `check.coil`/`mono.coil` sites are in the `coil-bugs` pad under “Generic trait wrapper cannot select a source type absent from Self.” Fix it if required for a genuinely compositional public API; do not reintroduce the broken wrapper as a workaround.
3. **Full live-program semantics.** The design still calls for ABI lineage, broader ownership/retention/failure gates, and careful treatment of foreign/C resources. Generic, attributed, `defn*`, sum, `const`, and ordinary `def` replacement is implemented, but that does not itself prove every type or call graph can migrate. Arbitrary native-stack continuation repair is explicitly outside the design.
4. **Source synchronization and editor completeness.** There is no file watcher that reconciles disk, unsaved buffer, desired source, and accepted runtime revisions. The Emacs client can submit an unsaved buffer and has earlier integration tests, but streamed output, completion, watcher integration, and the complete editor workflow remain. See `docs/PLAN.md` sections 3 and 6.
5. **Final visible and durability gates.** Rerun the 1,000-edit latency benchmark on the final build with the window visible, exact request-to-presented-frame correlation, and fresh-render pixel comparison. The archived color run was median 44.907 ms and maximum 53.138 ms, all under 100 ms, but is stale. Also run larger draw-body, imported-helper, burst, schema, repair, input, long-lived retention, and shutdown workloads described in `docs/PLAN.md`. Do not call compilation acknowledgement or GPU completion a presented frame.

## Recommended finish sequence

1. **Lock down the acceptance matrix.** Turn each uncovered value shape into a small executable case: nested records, sums with variant/payload changes, generic records, every owned container, resource-bearing elements, pointers/interior slices, sharing/cycles, version skips, reverts, and explicit rename/retype. For each, test successful migration and every allocation/validation/partial-initialization failure. `docs/PLAN.md` section 5 is the contract; `tests/migration_test.coil`, `tests/graph_test.coil`, `tests/schema_records_test.coil`, `tests/schema_session_test.coil`, and `tests/relocation_test.coil` are starting points.
2. **Finish one recursive policy system.** Extend `src/migration.coil` and generated schema lowering in `src/schema_lower.coil`/`src/schema_adapters.coil`. Keep physical type mapping, trait visibility, initialization-prefix cleanup, ownership transfer, relocation journaling, and exact old/new versions coherent. `src/graph.coil`, `src/managed.coil`, and `src/relocation.coil` implement transactional graph preparation/publication; retain their rollback contract. Add Coil compiler regressions when a language feature blocks generation rather than special-casing the POC.
3. **Add file watching as a client of the existing session API.** Diff source by Coil module/declaration identity; distinguish disk, buffer, desired, and accepted revisions. Cover atomic save, partial write, imports, deletion/rename, conflicts, and exactly-once migration. Do not create a separate publication mechanism.
4. **Complete editor/protocol affordances** and test a real unsaved-buffer workflow, reconnect, output streaming, completion, and revision conflicts. Keep the server's bounded queues and receipt semantics.
5. **Verify on real Paper and measure.** Run the visible moving scenario, fault tests, fresh-render pixel comparison, then the final 1,000-edit benchmark and broader workloads. Record compiler hash, source revisions, OS/display, renderer, frame metadata, every request/revision/presentation record, misses, and RSS/retention. Fix failures before claiming readiness.
6. **Update stale documentation.** `README.md` still names an older Coil commit and says 75 tests; `docs/PLAN.md`, `docs/MIGRATION.md`, and `docs/SCHEMA_LOWERING.md` contain checkpoint prose from earlier stages. Reconcile them with current code and final evidence. Keep `docs/SCHEMAS.md` precise about supported value shapes.

## Reproduction and verification

From this repository on the macOS development machine, with the matching Paper worktree at `../paper-test/.worktrees/live-poc`:

```sh
coil build src/main.coil -o build/live-poc
LPC_TOOLCHAIN="$(command -v coil)" coil test
LPC_TOOLCHAIN="$(command -v coil)" build/live-poc --headless
```

Run each protocol script against a fresh headless host from the repository root: `scripts/test_protocol.py`, `test_repair_protocol.py`, `test_async_protocol.py`, `test_schema_protocol.py`, and `test_reset_protocol.py` (with `PYTHONPATH=scripts python3 scripts/<name>.py` if needed). The host creates private `.nrepl-port` and `.live-token` discovery files. `scripts/test_schema_retention.py` builds its own 1,000-edit probe. The visible Paper command is `LPC_FIXTURE=fixtures/moving.coil LPC_TOOLCHAIN="$(command -v coil)" build/live-poc`; use `LPC_TESTING=1` only for the explicit fault workload in `scripts/test_paper_failure.py`. `scripts/benchmark.py --count 1000 --warmup 20 --output build/paper-1000.json` drives the visible color run; follow the stricter measurement rules in `docs/PLAN.md`.

For Coil compiler edits, read its `AGENTS.md` and language guide. Build one candidate, run `python3 scripts/dev.py test modernize-fast --compiler <candidate>` and the generated-code gate where relevant, then run `python3 scripts/dev.py build full` once at final verification. At a stopping point, install, commit, and push Coil changes as that repository requires.

The authoritative design and limits are `docs/PLAN.md`, `docs/SCHEMAS.md`, `docs/MOVING_PAPER.md`, and `docs/measurements/README.md`. Some older checkpoint sections are stale; use executable tests and fresh measurements to establish current behavior.
