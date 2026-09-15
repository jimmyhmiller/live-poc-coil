# Source lowering for managed schemas

This is the next implementation layer. The native bridge works with explicit generated-adapter fixtures; the ordinary source transform below is not implemented yet.

## Required source behavior

Opted-in record declarations produce distinct physical versions. Root declarations preserve identity, and re-evaluating an initializer does not reset an existing root. A layout change rechecks the affected function closure, derives justified field copies/defaults, and requires explicit transitions for retyped fields. A failed migration preserves the accepted heap. Repair must compose with the desired source while migrating from the actual accepted version.

## Compiler constraints established locally

- A second declaration of the same struct name is rejected. Physical names must be fresh.
- A `Code` value cannot be stored in an ordinary runtime annotation.
- Before-expansion transforms do not have semantic reflection. After-expansion transforms see expanded core forms before resolve/typecheck; they must emit core syntax without relying on new macro expansion.
- The accepted Code session state is immutable during a candidate. Staging a replacement does not change what `code-session-state` reads.
- Exact declaration and local-binding identities become available in the semantic phase. Do not substitute identifier spellings in arbitrary expressions or serialize syntax in a way that loses hygiene.

## Planned representation

The function registry is now one section of a structured session policy state, with schema and root sections alongside it. The semantic pass stages the complete value transactionally.

Carry a candidate's schema/root syntax through the compiler phases without losing syntax identity. `syntax-state.coil` supplies a temporary, unretained Code-returning carrier whose quoted body contains the records. A retained-JIT test verifies that after-expansion and semantic passes both observe preserved fresh-identifier identity, that the semantic pass removes the carrier before acceptance, and that later edits do not retain or collide with it.

After ordinary macro expansion, rewrite managed type references in the core grammar with lexical binding awareness. Type positions, constructors, qualified/imported names, local shadowing, match binders, and quoted syntax need separate handling. Existing retained implementations already refer to their physical types and must not be rewritten.

A root getter can expand to the stable native borrow operation. The after-expansion pass chooses the candidate's physical type and exact schema version for that root. This keeps root identity separate from the payload's type. Do not implement a root getter whose ordinary function ABI silently changes behind its retained gate.

Generated schema adapters call the existing staging bridge. They must be unretained native declarations whose generation remains owned by the managed runtime. Field migration/default functions require an enforceable purity policy: reject arbitrary I/O, globals, indirect calls, mutation of accepted storage, and unchecked helper effects. Internal graph callbacks are a trusted ABI, not the public effect policy.

## Bridge behavior already tested

The candidate entry closes admission, drains readers, registers private schemas/edges/roots, prepares the shadow graph, and reserves ownership. A failing entry rolls back its registrations and calls candidate abort adapters before the JIT unloads their image. Success coordinates source, code, graph and view publication, then retires old owners and reopens admission.

Named roots retain identity through failure and repair. Obsolete schema metadata and completed transition ownership are collected after publication; current object layouts and constructible schemas remain owned.

The current failed-state gate is global. Selective state dependency conditions, desired-schema repair composition, signature/ABI lineage changes, explicit root reset, sums and nested value policies remain to implement. The explicit adapter fixtures do not establish those source-level features.

Root-specific initializers now use `root-with!`: the initializer is called only for a new root, and partial ownership is cleaned through the schema abort policy if creation fails. Existing roots ignore a replacement initializer.

## Authored definitions and rechecks

The accepted policy state retains the latest authored function forms as syntax. Replacements overwrite those entries; a rejected compilation does not commit the candidate registry. This provides source for dependency rechecking without transforming retained machine-code implementations.

Each rechecked function stages its exact authored source text with its condition. Source publication covers both submitted forms and rechecked dependencies. It preserves a newer rejected desired edit and its diagnostic when the compiled body came from accepted source; it can also accept desired source if a changed schema makes that body valid.

`syntax-rewrite.coil` is the scoped core-expression rewrite used by the upcoming schema pass. Compiled tests cover local and parameter shadowing, mutable bindings, closures, loops, match bindings, field labels, constructors, and pointer type positions. Import/qualified-name mapping, schema declaration traversal, and ownership/purity analysis remain separate required work.
