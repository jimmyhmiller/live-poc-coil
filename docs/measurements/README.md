# Paper color-edit measurements

These are raw successful runs from September 15, 2026. Each run contains 1,000 measured alternating button-color edits after 20 declared warm-ups. Reports preserve per-request submit and presentation timestamps. Gzip compression is lossless; use `gzip -dc FILE.json.gz` to read a report.

| Implementation/client | Median | p99 | Maximum | Misses |
|---|---:|---:|---:|---:|
| Initial deferred-publication host / Python | 42.2 ms | 50.0 ms | 77.1 ms | 0 |
| Source ledger and expressions / Python | 49.3 ms | 70.5 ms | 88.3 ms | 0 |
| Source ledger and expressions / Emacs unsaved buffer | 48.3 ms | 66.2 ms | 79.0 ms | 0 |
| Semantic repair and Paper admission / Python | 45.2 ms | 53.3 ms | 71.8 ms | 0 |
| Semantic repair and Paper admission / Emacs | 38.4 ms | 50.4 ms | 63.1 ms | 0 |
| Separate compiler worker and publication preflight / Python | 44.9 ms | 52.8 ms | 53.1 ms | 0 |

The threshold includes each run's clock uncertainty. Emacs uncertainty was 0.080 ms; its submit timestamp precedes buffer-text extraction and nREPL encoding. Emacs uses its wall-clock timestamp calibrated against the host's presentation clock. The initial Emacs run lacks an endpoint drift audit; the later repair run includes the audit described below. The Python driver uses a monotonic clock. Neither endpoint measures physical photons.

The Mac reports Apple M2 Max and a built-in display mode at 120 Hz (see `display.json`). The later repair runs record every measured frame at 1280 × 960 pixels, scale 2, with Paper frame duration 16.67 ms (60 Hz). Every measured frame reports the app active and window visible. The earlier runs lack those per-frame checks. Workload-specific pixel comparison remains outstanding. The window was visually inspected before and after runs; native drawable callbacks establish presentation of the revision's frame.

A separate interaction check verified counter 2 → 3 for one click and preserved 3 through a blue-color replacement, confirmed in the UI and by querying live application state.

Two preliminary Emacs runs are excluded from these successful reports and retained in `build/`: one invalid report shared mutable list cells; the next valid 50-edit report had one conservative miss with 11.3 ms calibration uncertainty. The recorder and callback-based calibration were fixed before the 1,000-edit run.

These reports establish only the color workload. Blocked repair, schema migration, bursts, larger draw functions, imported helpers, pixel comparisons and long-lived retention require separate gates. Further runtime changes require rerunning the timing workload.

## Repair run details

`paper-repair-1000.json.gz` is the Python monotonic-clock run after native blocked repair and Paper admission. All 1,000 frames passed the conservative 100 ms check and the activity/visibility check. The original environment correctly records an uncommitted working tree based on `1002657`; this checkpoint contains those implementation changes.

`emacs-paper-repair-1000.json.gz` includes a start/end clock audit. Observed endpoint drift was 8.927 ms; start/end calibration uncertainty plus that drift totals 9.018 ms. Adding this to every latency leaves zero misses. This is an observed drift allowance, not a proof against an unobserved intermediate wall-clock step. Use the monotonic Python result for the stronger timing claim.

The Emacs recorder initially omitted its new telemetry field because adding an alist key changed only a local list head. Frame metadata was recovered from the same host's retained revision samples, checking exact equality with each original presentation timestamp. The enriched report records that provenance, and the original remains in `build/emacs-paper-repair-1000.json`. The recorder now preallocates the field.

`paper-repair-visual.json` records the blocked scene and queued-click verification. Precise static/indirect dependency analysis, schema migration, tick coalescing, watcher, streaming and broader stress gates remain separate work.

## Separate worker and preflight run

`paper-async-preflight-1000.json.gz` records the native host at commit `4acbe4f`, after compiler/network separation, input tick coalescing, and publication preflight. Twenty declared warm-ups precede 1,000 measured edits. All measured revisions presented while the app was active and the window visible. Median 44.907 ms, p95 51.998 ms, p99 52.775 ms, maximum 53.138 ms; zero misses including clock uncertainty. This validates the color path with the new control lane. It does not exercise schema migration or replace the outstanding pixel comparison.
