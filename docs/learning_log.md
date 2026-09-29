# Learning log

## Phase 1 — Software architecture

Status: UNDERSTOOD at the introductory checkpoint.

### Concept learned
Separation of responsibilities, shared implementations, reproducibility, configuration-driven experiments, and automated tests.

### Explanation in my own words
Learner response about duplicated calculations:
> the implementation is different its not a shared implementation like if we in src.

Learner response about changed historical data:
> nope it it isnt as its a different version of the historical data.

Tutor clarification: notebooks can depend on execution order and hidden state. Shared modules prevent fixes from diverging between consumers. Reproduction requires the data, code, dependencies, settings, and relevant seeds.

### Important formula
No new quantitative formula in this phase. Test invariant: with no investments, interest, or trades, ending capital equals starting capital.

### Common mistake
Treating successful execution or an impressive plot as proof that calculations are correct; copying the same calculation into multiple places.

### How we used it
Created a src package, separate tests and research folders, explicit configuration validation, a CLI, and CI. Financial calculations are deferred to their checkpoints.

### Interview question
Why test a backtest that runs without errors? What should happen to an inactive portfolio with no interest?

### My answer
> research code can show wrong calculations

> the automated test should check what investments it has and if not if its building interest. if not then the money shouldnt increase

Tutor assessment: correct. Under the stated assumptions and with no fees, value must remain exactly unchanged, including no decrease. This invariant will become a backtester test in Phase 10.
