# Live Coil

A native live-programming session with a real Paper window. Concrete function body edits publish through immutable execution views; a running invocation keeps its original view. Editor connections share one application state.

## Build and run

Requires macOS, the Paper integration worktree at `../paper-test/.worktrees/live-poc`, and Coil with commits `6485d21` and `3273588` from branch `live-poc-jit-project`. The compiler is installed globally on the development machine. `Coil.toml` declares the Paper dependency and native frameworks.

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

Bencoded string-keyed requests support `clone`, `describe`, `eval`, `load-file`, `source`, `status`, `metrics`, and `shutdown`. This is a documented nREPL subset. `eval` accepts concrete function definitions and expressions with typed `Debug` results. `load-file` reads the `file` field. Requests may include a `base-revision`; stale bases conflict. A duplicate mutation ID with identical input returns the original result; changing its input conflicts. Receipts are retained up to a declared limit of 4,096.

`source` with `ns` and `symbol` returns desired and accepted function source, the latest diagnostic, source span, attempt and accepted revision. Compilation failures preserve the accepted native view. Expression effects occur after publication and execute once per request ID. Formatted results are limited to 65,536 bytes; overflow reports that execution occurred.

## Verification

```sh
LPC_TOOLCHAIN="$(command -v coil)" coil test tests/session_test.coil
coil test tests/source_test.coil
coil test tests/presentation_test.coil
python3 scripts/test_protocol.py  # fresh running headless host
emacs --batch -Q --eval '(progn (require (quote package)) (package-initialize))' \
  -L editor/emacs -l coil-live-test -f ert-run-tests-batch-and-exit
python3 scripts/benchmark.py --count 1000 --warmup 20 \
  --output build/paper-1000.json  # visible running Paper host
```

The September 15 color run presented all 1,000 measured edits below 100 ms: median 42.2 ms, p99 50.0 ms, maximum 77.1 ms. This measured client submission through the exact drawable's presentation timestamp, including clock uncertainty in threshold checks. Raw data is in `build/deferred-paper-1000.json`. The run predates source-ledger and expression integration; repeat it for the final build. Visible color and persistent click state were checked separately. Fresh-render pixel comparison remains outstanding.

## Remaining scope

This implementation is in progress. Semantic blocked-entry repair, persistent-state schema migration, output streaming, cancellation, watcher integration, automated pixel comparison and broader retention/failure gates remain. Live generic and attributed function definitions receive capability diagnostics; use `defn*` for static helpers. Arbitrary native-stack continuation repair is outside the design.

See [the complete plan](docs/PLAN.md) and project notebook `live-poc-coil` for contracts, measurements and external bugs.
