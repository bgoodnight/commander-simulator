# Typed physical zone batches (first pass)

This introduces a small prevalidated, source-ID-based resolver for later
mass-zone cards such as Living Death. Every movement captures the original
owner, controller, zone, name, types, subtypes and token state before any
zone mutation. New IDs are returned by the existing physical kernel; they
must be used in later phases rather than reusing stale pre-transition IDs.

This is **not yet full Living Death support**. The physical kernel still
applies moves sequentially after prevalidation, and this helper does not
resolve replacement choices, simultaneous triggers, APNAP ordering, stack
priority or commander replacement decisions. Card-specific activation,
legal player scopes and post-batch trigger collection belong in the host.

No production batch has been regenerated, and no card is marked as fully
supported solely from this primitive. Tests cover multi-owner exile,
return, sacrifice provenance and fail-closed validation.
