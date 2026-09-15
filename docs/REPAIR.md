# Native repair and Paper admission

`eval` and `load-file` accept `policy: "strict"` (the default) or `policy: "deferred"`. Strict failure preserves the accepted view. Deferred publication returns `status: ["blocked", "done"]` with its revision and original diagnostic. Retrying the same request returns its original receipt, including after a later repair; changing the policy conflicts.

The compiler identifies failed live definitions through owned integer annotations. The controller checks their headers through prototypes, then rechecks submitted bodies against those headers to distinguish independent failures from cascades. The retained typed staging helper checks replacement ABI compatibility. Native blocked entries have no callable implementation. A malformed header, incompatible ABI, static helper failure or mixed expression/failure batch rejects.

Desired source survives rejection independently of accepted source. A mixed deferred batch records accepted source for valid definitions and preserves prior accepted source for blocked definitions. Repairing one body clears its condition and revives existing callers through the dependency graph.

## Admission and dependency coverage

A live function value contains a stable ID and typed gate. An invocation preflights its root and pins one immutable execution view under the same mutex. Nested calls use that view. An older invocation can finish while a newer view blocks or repairs the same function.

Direct live references use Coil's resolved declaration identities, including cross-module names. Replacing a body replaces its outgoing edges. Calls through static helpers, externs, unanalysed globals or indirect calls conservatively depend on every blocked condition. This can defer unrelated work; precise cached dependency coverage for these cases remains unfinished. Typed expressions are currently rejected while any function is blocked because expression dependency admission is not yet implemented.

## Paper

The host registers stable callback gates with their matching root IDs. Draw admission runs before Paper invalidates controls or rebuilds the scene, including resize and initial refresh paths. A denied draw preserves the last scene. A successful admission is released immediately after the application draw callback.

Input enters an owned FIFO queue. The main-thread pump checks and pins the head's root before claiming it; a blocked head prevents later input from overtaking it. Publication needs no queue notification: the main-thread frame pump checks again. Each accepted payload is dropped once after execution or cancellation. Shutdown closes the queue before callback teardown.

The queue holds up to 1,024 waiting events. Overflow rejects the new event, releases its caller-owned payload, increments a visible protocol counter and changes the window title. Pointer/tick coalescing is not implemented. `status` reports queued/completed/cancelled/rejected input and the first waiting ticket. `cancel-input` with `ticket` cancels a waiting event; already executing or absent tickets return an error.

## Evidence

The native suite has 26 passing tests. Coverage includes old-view pinning, direct and conservative dependency admission, void/pointer and aggregate repair, mixed source outcomes, expression rejection without effects, FIFO ownership/cancellation, and preservation of Paper controls when drawing is denied. Both protocol test scripts pass.

A visible Paper run kept its orange scene during a rejected color body, queued a real click, and applied that click exactly once after a one-form repair to blue. All 17 waiting events drained with zero rejected inputs. Raw observations are in `build/paper-repair-visual.json`. Pixel comparison, more concurrency schedules, schema evolution, watcher/durability and asynchronous protocol streaming remain outstanding.
