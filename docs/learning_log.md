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

## Phase 1 follow-up — Configuration

### Concept learned
Results need their exact settings attached.

### Explanation in my own words
> because there are 2 different transaction costs so if you have one you cant get the same result as you are missing information

### Important formula
None introduced.

### Common mistake
Saving a chart without the settings that produced it. Saving settings aids traceability but does not itself prevent leakage.

### How we used it
The Phase 2 snapshot includes the data request settings.

### Interview question
Why preserve configuration alongside results?

### My answer
The quotation above explains the need to identify the correct assumptions to reproduce a result. Checkpoint passed.

## Phase 2 — Market data and introductory returns

### Concept learned
OHLCV; corporate actions; simple versus log returns; percentage scaling; information availability. Introductory checkpoint passed, with percentage arithmetic needing continued practice.

### Explanation in my own words
On comparable returns:
> because if the amount is different the percentage gain is different

On split-related artificial losses:
> because it would think you lost money because it went to 50 not knowing you split it

On log versus simple return labels:
> keep rreturn types clearly so its acurate

### Important formula
Simple return: `P[t] / P[t-1] - 1`.
Log return: `ln(P[t] / P[t-1])`.
Percentage display: decimal simple return multiplied by 100.

### Common mistake
Confusing dollars, decimals, and percentages. A $5 gain on $50 is 10%; on $500 it is 1%. Initially treated a split as diversification; clarified that both shares remain exposed to the same company. A split alone does not change wealth. Saving an adjusted series does not automatically prevent every form of leakage.

### How we used it
Separate return columns; no filling; an undefined first return; explicit provider adjustments; session validation; local snapshots and checksums. Financial/model phases remain unimplemented.

### Interview question
At Tuesday's open, can Wednesday's opening price be used merely because it appears in historical data?

### My answer
> no because its lookahead bias

Other correct answers included $100 to $103 = 3%; unchanged prices give zero simple and log returns; two $45 shares total $90; $6 on $200 = 3%; $5 on $500 = 1% after guided practice. Log-return additivity was introduced, not demonstrated independently. OHLCV meanings were introduced but not individually tested.
