# Persistent state and field transitions

Managed records opt in explicitly. Plain Coil records retain their ordinary behavior. Managed schemas own the lifetime of generated physical types; an authored `:jit/retain` option is rejected.

```coil
(defstruct State :live/state true
  [(visible bool true)
   (value i64 7)])

(letonce world (State :visible false :value 42))
(defn value [] (-> i64) (.value world))
```

`letonce` registers a stable root identity. Resubmitting its initializer does not reset the object. Constructors use named fields; omitted fields use checked defaults. Generated defaults retain separate lexical identities even when they share a display name.

Submitting only a replacement schema rechecks the module's existing live functions against its new physical type. Existing fields retain their values; added fields require defaults. Field order does not define field identity.

## Retyping an existing field

A construction default does not authorize discarding an existing value. Supply a typed transition for the accepted source version and proposed destination version:

```coil
(defsum Visibility (Hidden) (Visible))

(defstruct State :live/state true
  [(visible Visibility (Visible))
   (value i64 7)])

(migrate State visible old
  (if old (Visible) (Hidden)))
```

The existing `false` becomes `Hidden`; newly constructed objects default to `Visible`. Transition parameters and results must match their field types. The pure preparation checker rejects mutation, raw pointers, global reads, unchecked calls and recursive helper cycles. Allocation, preparation and validation happen before graph publication. Failed preparation leaves accepted objects and code unchanged.

Transition syntax is recorded with exact source and destination versions. Re-reading an unchanged transition does not authorize a later version edge. Equivalent type spellings are currently derived conservatively: a changed spelling can require an explicit transition even if it denotes an equivalent type.

## Repairing a missing transition

With deferred publication, a missing transition preserves the desired schema separately from accepted state. Submit only the missing `migrate` form to retry that schema. A rejected strict repair does not replace the pending snapshot. Edits in other modules preserve that snapshot. Source inspection records the actual schema and function bodies accepted by the repair.

The current native tests cover stable roots, repeated initializers, added/reordered fields, distinct defaults, explicit overrides, bool-to-sum transitions, missing-edge rollback and transition-only repair.

## Work still in progress

Layout publication closes admission while readers drain. A pending transition then blocks only native roots whose checked call closure depends on that schema; unknown calls and raw evaluation remain conservative. If condition storage cannot be allocated, admission stays blocked until the complete pending source is repaired. Nested ownership policies, managed sums, generic schemas and explicit state reset are not complete. Versioned compiler roots now retire obsolete schema metadata and native generations; the 1,000-edit durability gate passes. The moving Paper scenario has passed radius/default/retype/repair checks, including independent input domains; visible migration-failure injection remains outstanding. The complete contract remains in [PLAN.md](PLAN.md).
