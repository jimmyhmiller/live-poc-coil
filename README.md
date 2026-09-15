# Live Coil

A native live-programming session with a real Paper window. Concrete function body edits publish through immutable execution views; a running invocation keeps its original view. Editor connections share one application state.

## Build and run

Requires macOS, the Paper integration worktree at `../paper-test/.worktrees/live-poc`, and Coil at `885a755` from branch `live-poc-jit-project`. The compiler is installed globally on the development machine. `Coil.toml` declares the Paper dependency and native frameworks.

```sh
coil build src/main.coil -o build/live-poc
LPC_TOOLCHAIN="$(command -v coil)" build/live-poc
```

For the app bundle, `python3 scripts/bundle.py` packages the executable. Its development configuration currently uses `build/toolchain/bin/coil`. Launch the executable inside `build/Live Coil.app/Contents/MacOS/` from the project directory, setting `LPC_PROJECT` and `LPC_TOOLCHAIN` for the intended checkout/toolchain.

Use `--headless` for protocol tests. The host writes private `.nrepl-port` and `.live-token` discovery files. The server binds to loopback and requires the capability on every connection. Do not check those files into source control.

## Submit an unsaved edit

Load `editor/emacs/coil-live.el` with the Emacs `nrepl-client` package available. In a Coil buffer with `(module live-demo)`, run `M-x coil-live-connect`. `C-c C-c` submits the definition at point; `C-c C-r` submits a region; `C-c C-k` submits the unsaved buffer. The Paper fixture is `fixtures/paper.coil`.

```coil
(defn button-pigment [] (-> u32) 5471164)
```

Python is used only for test and benchmark drivers:

```sh
PYTHONPATH=scripts python3 - <<'PY'
from client import Client
c = Client()
print(c.request('eval', ns='live-demo',
                code='(defn button-pigment [] (-> u32) 5471164)'))
c.close()
PY
```

## Protocol

Bencoded string-keyed requests support `clone`, `describe`, `eval`, `load-file`, `source`, `status`, `metrics`, `interrupt`, `cancel-input`, and `shutdown`. This is a documented nREPL subset. `eval` accepts concrete function definitions and expressions with typed `Debug` results. `load-file` reads the `file` field. Requests may include a `base-revision`; stale bases conflict. A duplicate mutation ID with identical input returns the original result; changing its input conflicts. Receipts are retained up to a declared limit of 4,096.

Compilation runs on a dedicated worker. `status` and `source` remain responsive, including on a connection with an outstanding edit. `interrupt` takes `interrupt-id`; its acknowledgement means cancellation was requested. The original request determines the outcome: `interrupted` before publication, or a committed result with `interrupt: requested-after-publication` if publication already occurred. Running expressions can poll `live-poc-coil.cancellation/cancelled?` at safe points. This never forcibly unwinds a native stack or rolls back effects. Disconnecting does not cancel an edit. There are at most 64 active compiler jobs and 8 pending jobs per connection; responses and input queues are bounded.


`eval` and `load-file` accept `policy: "deferred"` to publish typed blocked entries; strict rejection is the default. See [repair and callback contracts](docs/REPAIR.md). In Emacs, set buffer-local `coil-live-publication-policy` to `"deferred"`.

`source` with `ns` and `symbol` returns desired and accepted function source, the latest diagnostic, source span, attempt and accepted revision. Compilation failures preserve the accepted native view. Expression effects occur after publication and execute once per request ID. Formatted results are limited to 65,536 bytes; overflow reports that execution occurred.

## Verification

```sh
LPC_TOOLCHAIN="$(command -v coil)" coil test
python3 scripts/test_protocol.py  # fresh running headless host
python3 scripts/test_repair_protocol.py
python3 scripts/test_async_protocol.py
python3 scripts/test_schema_protocol.py
emacs --batch -Q --eval '(progn (require (quote package)) (package-initialize))' \
  -L editor/emacs -l coil-live-test -f ert-run-tests-batch-and-exit
python3 scripts/benchmark.py --count 1000 --warmup 20 \
  --output build/paper-1000.json  # visible running Paper host
```

The latest 1,000-edit color run passed with median 44.9 ms, p99 52.8 ms and maximum 53.1 ms; zero misses including clock uncertainty. Every frame reported the app active and window visible. The measured Paper render was 1280 × 960 at scale 2 with a 16.67 ms frame duration. [Raw measurements and limits](docs/measurements/README.md) include Python and actual unsaved Emacs runs.

Visible repair verification kept the prior scene while the color function was broken, queued a click, and applied it exactly once after a one-form repair. The native suite has 52 passing tests, all four protocol scripts pass, and three Emacs integration tests pass.

## Remaining scope

This implementation is in progress. Ordinary persistent records, typed field transitions and transition-only deferred repair work; see [schema contracts](docs/SCHEMAS.md). Selective layout admission, broader value policies, metadata retirement, output streaming, watcher integration, automated pixel comparison and broader retention/failure gates remain. Direct semantic repair and input cancellation work; unanalysed calls use conservative admission, and expressions are rejected while any function is blocked. Live generic and attributed function definitions receive capability diagnostics; use `defn*` for static helpers. Arbitrary native-stack continuation repair is outside the design.

See [the complete plan](docs/PLAN.md) and project notebook `live-poc-coil` for contracts, measurements and external bugs.
