# Phase 4 — Next-session target alignment

## Definition

At feature session t, predict whether adjusted close-to-close return P[t+1]/P[t]-1 is strictly positive. Class 1 means positive; class 0 means zero or negative. The last row has no observed subsequent session and remains missing in all target columns. These definitions are recorded in every artifact; the horizon is fixed at one session rather than exposing unimplemented horizon settings.

`next_return` on Tuesday's row describes Tuesday close to Wednesday close. `target_up` is its nullable integer class. `outcome_session` identifies Wednesday. The label becomes available only after that session closes and its final data is available. Session dates are not exact publication timestamps: a future walk-forward splitter must explicitly apply the after-close timing contract and cannot assume midnight availability.

## Separate inputs and outcomes

Targets are written to `targets.csv`, never appended to feature outputs. Metadata lists all target columns as forbidden prediction inputs. Tests confirm disjoint schemas and show that changing tomorrow's price can change today's target without changing today's features. This is evidence of correct transformations, not a complete model-training leakage guarantee. The model pipeline will need explicit feature selection and training-admission rules.

```bash
beyond-accuracy build-targets --snapshot data/snapshots/<snapshot-id>
```

Uses the verified local Phase 2 snapshot, without network access. Creates a unique directory under `results/targets` with target CSV and provenance metadata. Match source snapshot hashes before combining with features in later phases. Keep all rows; feature warm-up and unknown labels must be handled explicitly later.

When reading targets back, use pandas nullable `Int64` for `target_up` and parse `Date` and `outcome_session` as dates. Missing outcomes must not be filled with zero. The CLI validates session completeness through the snapshot verifier; direct callers must provide consecutive validated sessions.

## Checks and limits

Tests cover positive, flat, negative, final unknown, single-row inputs, Friday-to-Monday alignment, chronological dates, source tampering, CSV round-trip, and future-input separation. Adding a new session resolves the previously final target while preserving earlier known targets.

These are historical adjusted close-to-close classification outcomes. They are not a strategy's tradable return: after-close features cannot justify execution at that same close. Execution timing and the relationship between the prediction horizon and later trading returns must be resolved at the execution checkpoint. No train/test split, model fitting, or strategy performance is implemented here. Provider-vintage limitations from Phase 2 still apply.
