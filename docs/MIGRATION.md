# Managed-state migration

## Runtime checkpoint

`graph.coil` implements an internal native graph transaction. It is not yet wired to source submission or Paper state. `runtime.coil` supplies the admission barrier that the session will use around incompatible layout changes.

Schemas identify a nominal type and an exact physical version. Transitions bind a specific source schema to a specific destination schema. Missing edges report both versions and the nominal identity. Reverts require a new forward version; this layer does not guess or compose intermediate transitions.

Handles preserve identity across publication. Preparation allocates all destination payloads first, then invokes ownership policies, rewrites references, and validates the complete shadow graph. Unchanged objects are cloned too so their incoming references can be rewritten privately. This is an intentionally conservative whole-graph implementation.

Object references relocate by exact base identity and nominal type. Interior slices use separate allocation-range mappings supplied by their owning value policies. Reordered struct fields cannot be relocated by assuming that their old byte offsets still mean the same thing. Invalid extents, overlapping owners, null nonempty ranges, and integer overflow are rejected.

The internal policy ABI has initialize, clone/transition prepare, rewrite, validate, abort, and retire callbacks. Preparation advances an initialized prefix, allowing failure to destroy only independently constructed candidate ownership. Abort runs in reverse object order. Publication changes stable headers without allocation or user callbacks; retirement destroys old owners afterwards. Generated public adapters must enforce the effect discipline before using this ABI. Handwritten callbacks are currently used only by the contract tests.

Allocation failure during transaction metadata or payload construction is recoverable. `fallible-list.coil` uses the allocator's existing failure-returning API because normal ArrayList growth deliberately aborts on exhaustion.

## Admission and draining

`close-layout!` denies new invocations immediately. Existing invocations retain their view and finish normally. `drain-layout!` waits on a generation-counted completion event with the runtime mutex released. It checks cooperative cancellation at bounded intervals. The main thread never performs this wait. Admission remains closed until the controller explicitly reopens it after publication, rollback, or repair.

This first barrier closes all application roots. Per-layout admission and foreign pointer lease inspection remain to implement; it must not be described as selective.

## Verified

The native suite has 37 passing tests. Migration contracts cover:

- Reordered fields and a new default, with stable object identity.
- Two-object cycles and references from an unchanged nominal type.
- Shared slices into another object's independently cloned owned buffer.
- Missing exact edges, failed copying, failed validation, and cancellation.
- Allocation fault injection across transaction construction, with zero remaining allocator-owned blocks after shutdown.
- New work denied during layout drain, old pinned work completing, and explicit reopening.

## Remaining integration

The source transform must generate versioned physical types and ownership adapters, check migration purity, preserve roots and initializer-once semantics, recheck affected definitions, and coordinate schema and native-code publication. The compiler rejects duplicate struct declarations, so schema edits must generate distinct physical declarations. No ordinary struct redefinition or source replay should be presented as a working schema update.

Persistent schema/adapter generation ownership, obsolete-version retirement, missing-migration repair composition, checked sums and nested value policies, and the moving Paper acceptance sequence remain unfinished.
