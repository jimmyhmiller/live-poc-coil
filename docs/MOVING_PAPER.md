# Moving Paper state

Build the host and run it with `LPC_FIXTURE=fixtures/moving.coil`. The fixture uses the same retained compiler, socket protocol, native callback gates and Paper renderer as the color benchmark. Its persistent record owns position, velocity, tick time, visibility and click count.

The visible September 15 run exercised these edits through the socket in namespace `moving-demo`:

1. Replace `radius` with a function returning `40.0`; the circle grows while motion continues.
2. Add `(mass f64 2.0)` to the complete `State` definition. The new field reads `2.0`, while position continues from its existing value.
3. Define `Visibility` with `Hidden` and `Visible` variants. Retype the `visible` field to `Visibility`, with construction default `(Visible)` and `(migrate State visible old (if old (Visible) (Hidden)))`. Submit with deferred publication.
4. The old `visible?` body returns the sum where its signature requires bool. It becomes blocked, and Paper preserves the last complete scene.
5. Click once, then submit only the repaired function:

```coil
(defn visible? [] (-> bool)
  (match (.visible world) (Hidden [] false) (Visible [] true)))
```

Drawing resumes and the counter reads `1`. The added field still reads `2.0`. Native drawable presentation and screenshots were inspected during this run. Raw request/reply records are in [moving-schema-repair.json](measurements/moving-schema-repair.json).

This check establishes visible schema migration and repair. It does not establish pixel equality against a fresh render or migration-failure injection in the visible host. Those remain separate acceptance work. The radius/schema edits were not a latency benchmark.

## Schema retention

Run `python3 scripts/test_schema_retention.py`. It builds a standalone native probe and performs 1,000 reorder/default edits with constructor evaluations and rejected incompatible proposals. The probe checks root identity, values, schema/handle/owner counts and native generations. The driver checks complete sampling, stable allocator bytes, and a fixed 768 MiB peak process ceiling.

The archived [1,000-edit report](measurements/schema-retention-1000.json.gz) passed with 702,693,376 bytes peak resident memory. After warm-up, four native generations and 1,560,853 live session allocation bytes remained stable. Compiler hashes, worktree status, samples and raw output are included. This measures repeated schema edits; other durability workloads remain separate.

## Independent input domains

`paper/run-routed` accepts a slice of `input-routes/Route` values. Each route names an event kind, widget ID (`-1` for any ID of that kind), positive ordering domain, and typed live handler. Exact IDs take precedence. The host copies at most 64 unique routes before starting the event loop and rejects invalid tables. The ordinary `paper/run` API retains global FIFO behavior in domain zero.

The moving fixture assigns ticks and the scene button to domain 1, and the independent control to domain 2. The queue only considers the oldest event of each domain. A blocked head prevents its peers from overtaking it, while another domain may run. Coalescing never crosses an intervening input or a domain boundary. Cancel and shutdown drop every owned payload once.

The visible check blocked `tick`, clicked the scene button, then clicked the independent control. The control counter advanced to `1` while the scene counter remained `0`. Status showed the scene click had no code condition but was waiting behind its blocked domain peer. Repairing only `tick` produced counters `1` and `1`. [Raw status and repair records](measurements/moving-input-domains.json).

Admission recognizes the audited, non-reentrant Paper host drawing/redraw entry points. Callback-taking run functions and unknown externs remain conservative. Checked scalar arithmetic uses the same classification as pure defaults; its operands still contribute dependencies. Regression coverage includes a counter update through a managed root, live arguments to host calls, and an unknown alias of a host symbol.

`status` now includes `pending-input`, keyed by ticket, with domain, root, propagated code condition and whether the root has an opaque dependency. State admission conditions remain available separately.
