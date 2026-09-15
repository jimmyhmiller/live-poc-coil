# Paper color-edit measurements

These are raw successful runs from September 15, 2026. Each run contains 1,000 measured alternating button-color edits after 20 declared warm-ups. Reports preserve per-request submit and presentation timestamps. Gzip compression is lossless; use `gzip -dc FILE.json.gz` to read a report.

| Implementation/client | Median | p99 | Maximum | Misses |
|---|---:|---:|---:|---:|
| Initial deferred-publication host / Python | 42.2 ms | 50.0 ms | 77.1 ms | 0 |
| Source ledger and expressions / Python | 49.3 ms | 70.5 ms | 88.3 ms | 0 |
| Source ledger and expressions / Emacs unsaved buffer | 48.3 ms | 66.2 ms | 79.0 ms | 0 |

The threshold includes each run's clock uncertainty. Emacs uncertainty was 0.080 ms; its submit timestamp precedes buffer-text extraction and nREPL encoding. Emacs uses its wall-clock timestamp calibrated against the host's presentation clock. A final clock-drift audit is still needed; the Python driver uses a monotonic clock. Neither endpoint measures physical photons.

The Mac reports Apple M2 Max and a built-in display mode at 120 Hz (see `display.json`). Actual frame-clock frequency, render scale, visibility throughout the run, and workload-specific pixel comparison need stronger instrumentation before treating this as a complete visual acceptance gate. The window was visually inspected before and after runs; native drawable callbacks establish presentation of the revision's frame.

A separate interaction check verified counter 2 → 3 for one click and preserved 3 through a blue-color replacement, confirmed in the UI and by querying live application state.

Two preliminary Emacs runs are excluded from these successful reports and retained in `build/`: one invalid report shared mutable list cells; the next valid 50-edit report had one conservative miss with 11.3 ms calibration uncertainty. The recorder and callback-based calibration were fixed before the 1,000-edit run.

These reports establish only the color workload. Blocked repair, schema migration, bursts, larger draw functions, imported helpers, pixel comparisons and long-lived retention require separate gates. Further runtime changes require rerunning the timing workload.
