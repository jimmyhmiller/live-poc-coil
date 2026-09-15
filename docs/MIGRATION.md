# Managed-state migration

## Runtime checkpoint

`graph.coil` implements a native graph transaction. `managed.coil` coordinates it with source and native code publication, including rollback before rejected candidate adapters unload. Retained-JIT fixtures exercise this bridge; ordinary schema source lowering and Paper state integration remain in progress. `runtime.coil` supplies the admission barrier around incompatible layout changes.

Schemas identify a nominal type and an exact physical version. Transitions bind a specific source schema to a specific destination schema. Missing edges report both versions and the nominal identity. Reverts require a new forward version; this layer does not guess or compose intermediate transitions.

Handles preserve identity across publication. Named roots retain those handles; a repeated initializer proposal leaves existing values intact. Multiple root identities can intentionally share one handle. Candidate registration savepoints roll back new schemas, transitions, and initialized roots before their native adapter image is unloaded. A savepoint cannot roll back a committed heap epoch. Preparation allocates all destination payloads first, then invokes ownership policies, rewrites references, and validates the complete shadow graph. Unchanged objects are cloned too so their incoming references can be rewritten privately. This is an intentionally conservative whole-graph implementation.

Object references relocate by exact base identity and nominal type. Interior slices use separate allocation-range mappings supplied by their owning value policies. Reordered struct fields cannot be relocated by assuming that their old byte offsets still mean the same thing. Invalid extents, overlapping owners, null nonempty ranges, and integer overflow are rejected.

The internal policy ABI has initialize, clone/transition prepare, rewrite, validate, abort, and retire callbacks. Preparation advances an initialized prefix, allowing failure to destroy only independently constructed candidate ownership. Abort runs in reverse object order. Publication changes stable headers without allocation or user callbacks; retirement destroys old owners afterwards. Generated public adapters must enforce the effect discipline before using this ABI. Handwritten callbacks are currently used by the contract tests and retained-JIT adapter fixtures.

Allocation failure during transaction metadata or payload construction is recoverable. `fallible-list.coil` uses the allocator's existing failure-returning API because normal ArrayList growth deliberately aborts on exhaustion.

## Admission and draining

`close-layout!` denies new invocations immediately. Existing invocations retain their view and finish normally. `drain-layout!` waits on a generation-counted completion event with the runtime mutex released. It checks cooperative cancellation at bounded intervals. The main thread never performs this wait. Admission remains closed until the controller explicitly reopens it after publication, rollback, or repair.

This first barrier closes all application roots. Per-layout admission and foreign pointer lease inspection remain to implement; it must not be described as selective.

## Verified

The native suite has 46 passing tests. Migration contracts cover:

- Reordered fields and a new default, with stable object identity.
- Two-object cycles and references from an unchanged nominal type.
- Shared slices into another object's independently cloned owned buffer.
- Missing exact edges, failed copying, failed validation, and cancellation.
- Allocation fault injection across transaction construction, with zero remaining allocator-owned blocks after shutdown.
- New work denied during layout drain, old pinned work completing, and explicit reopening.

## Publication reservation

The native publication entry calls a host preflight before returning success to the JIT. It prepares source replacement ownership and reserves runtime and timing registries. Source publication swaps owned strings; old strings are freed after the view is consistent. Cancellation is checked again in that preflight. The image record is allocated before compilation, then receives its generation token after native acceptance.

The managed bridge now attaches graph preparation to this hook. SDK token capacity is reserved during preflight, and token acquisition after native acceptance uses the allocation-free reserved API.

## Remaining integration

The source transform must generate versioned physical types and ownership adapters, check migration purity, preserve roots and initializer-once semantics, recheck affected definitions, and coordinate schema and native-code publication. The compiler rejects duplicate struct declarations, so schema edits must generate distinct physical declarations. No ordinary struct redefinition or source replay should be presented as a working schema update.

Missing-migration repair composition, checked sums and nested value policies, selective admission, and the moving Paper acceptance sequence remain unfinished.

## Adapter ownership and roots

The managed bridge owns exact native image references for schemas and transitions. After a completed migration, it releases obsolete schemas and completed transitions; live physical layouts and schemas available for constructing roots remain owned. Shutdown destroys graph payloads before releasing their callback code.

Root-specific initializers use `root-with!`. Two roots of one nominal type may have different initial values. Re-evaluating an initializer preserves an existing root; a failed new initializer cleans its initialized ownership and leaves no root registration.

Compiler generation tokens now support explicit fallible reservation and allocation-free acquisition. Publication reserves SDK token capacity, runtime view/image registries, metrics, graph ownership metadata, and source replacements before native acceptance. This closes the generation-token reservation gap in the earlier checkpoint.
