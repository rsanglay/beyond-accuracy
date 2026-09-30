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

## Phase 2 output check

### Concept learned
First-return availability and decimal-to-percentage conversion.

### Explanation in my own words
> its undefined as we couldnt get a value and 0.2647%

### Important formula
0.002647 * 100 = 0.2647%.

### Common mistake
Calling the first return zero. The first price exists, but the snapshot lacks a preceding price.

### How we used it
Preserved the first missing return and inspected real snapshot output.

### Interview question
Why is the first return undefined?

### My answer
The learner's quotation above was clarified: specifically, the previous price is unavailable within the snapshot. The percentage conversion was correct independently.

## Phase 3 — Features and information timing

### Concept learned
Lagged returns, momentum, moving averages, trailing windows, sample volatility, Wilder RSI, relative volume, warm-up periods, and future-data leakage. Teaching checkpoint passed with arithmetic reinforcement still needed. Code/output review is next.

### Explanation in my own words
On higher volatility:
> the one that swings as its not identical.

On why distances are squared:
> to prevent cancelation

On RSI meaning:
> recent balance of gains and losses

For the baseline on row 6:
> 1-5

### Important formula
- Momentum: P[t]/P[t-n] - 1. The learner calculated 108/102 - 1 as approximately 5.88%.
- Moving average: sum of n closing prices divided by n; 100, 102, 104 gives 102.
- Sample volatility: sqrt(sum((r-mean(r))^2)/(n-1)); -3%, +1%, +5% yields 4 percentage points.
- RSI: 100 - 100/(1 + average_gain/average_loss), with Wilder smoothing after the initial mean of n changes.
- Relative volume: current volume / prior n-session mean volume; 20/10 = 2.
- n prices contain n-1 consecutive changes.

### Common mistake
Initially confused cancellation with no variation and zero standard deviation with zero average return. After simpler examples, correctly identified identical returns as zero volatility and swings as higher volatility. Initially placed an inclusive five-price average on row 6; corrected to row 5. Prior-five volume baseline first appears on row 6. Initially attributed invalid future imputation to missingness rather than availability; clarified that future-inclusive averages leak even without missing data. Initially interpreted high RSI as nearly guaranteeing reversal; corrected that prices could keep rising. RSI arithmetic and n versus n-1 needed guided practice.

### How we used it
Implemented explicit trailing functions and configuration, complete-window NaNs, exact Wilder initialisation, and local artifact provenance. Tests compare hand-worked examples and ensure changing/adding future data does not alter past features. Moving-average levels are diagnostic only; model input selection is deferred. No targets, models, or trading execution are implemented.

### Interview question
Can a Tuesday feature use an average calculated with later years? What if the average uses only earlier completed sessions?

### My answer
The learner confirmed the future-inclusive average is look-ahead bias, then answered:
> no
when asked whether an average using only completed sessions before Tuesday contains future information. This establishes introductory timing understanding, with independent explanations to revisit.

## Phase 3 output check — Prior-volume baseline

### Concept learned
`shift(1)` excludes the current observation from the prior-volume comparison baseline.

### Explanation in my own words
> it moves the baseline back

### Important formula
relative_volume[t] = V[t] / mean(V[t-5], ..., V[t-1]).

### Common mistake
Initially attributed the shift to undefined early rows. Clarified that warm-up and exclusion of today's volume are different concerns. Including today's volume after its session ends would not itself be look-ahead bias, but would change the intended baseline.

### How we used it
Shift volume before calculating its rolling mean. Phase 3 PR approved and merged.

### Interview question
Why shift before calculating the volume baseline?

### My answer
The learner's quotation above was accepted after confirming that the unshifted rows 2–6 include today (row 6).

## Phase 4 — Target alignment

### Concept learned
Today's features pair with the next session's outcome; unknown outcomes are missing; training must wait for label availability.

### Explanation in my own words
> wednesday comes after tuesday

> wait for wednesday close

### Important formula
next_return[t] = P[t+1]/P[t] - 1.
Known target = 1 if next_return > 0, otherwise 0. Unknown next_return has no class.

### Common mistake
Initially selected Monday for Tuesday's next outcome and class 0 for an unobserved final outcome. Corrected through smaller timing examples: Tuesday features pair with Tuesday-to-Wednesday return, and an unknown final label is undefined. Putting tomorrow's actual outcome in today's features is look-ahead bias.

### How we used it
Separate target artifact with nullable integer labels, next-session dates, and source hashes. Tests check alignment and that future changes affect targets without changing earlier features. Walk-forward training-admission enforcement remains Phase 6 work.

### Interview question
Can Tuesday's labelled example train a model on Tuesday evening?

### My answer
> wait for wednesday close

Introductory checkpoint passed. Independent code/output explanation remains to be checked.

## Phase 4 output check — Label availability

### Concept learned
An outcome visible in historical data was not necessarily available at prediction time.

### Explanation in my own words
> wait for 31

### Important formula
No new formula; the 30 December row's outcome requires 31 December's closing data.

### Common mistake
Confusing an unknown outcome at the time with its later-known label in a completed historical table.

### How we used it
Confirmed label availability before approving and merging PR #4.

### Interview question
When may the 30 December example be used for training?

### My answer
The learner's quotation above correctly identifies waiting for 31 December's closing data.

## Phase 5 — Simple benchmarks

### Concept learned
Majority classification, latest-return direction, momentum, fair comparisons, and buy-and-hold as a separate financial reference. Introductory checkpoint passed; code/output review next.

### Explanation in my own words
On choosing the majority class and comparing 55% versus 56% accuracy:
> positive, it hast bevause the accuracy is 1% lower

Tutor clarification: the absolute difference is one percentage point. The learner correctly identified no accuracy improvement.

### Important formula
Accuracy = correct predictions / total predictions. The learner correctly answered 40% for 40 positive outcomes when every prediction is positive.

### Common mistake
Initially proposed using test outcomes to choose the majority class. Corrected after considering whether January's majority was knowable before January. Initially thought predicting Wednesday required Wednesday's actual price; clarified that it is needed to score the prediction afterward. Initially thought buy and hold would sell after five losses; clarified that selling in response to losses breaks its fixed holding rule.

### How we used it
Implemented a frozen training-majority rule with known-outcome checks, two explicit feature-based direction rules, and local known-answer tests. Missing inputs remain missing. Buy-and-hold financial calculations and chronological evaluation are deferred to their checkpoints. No empirical benchmark performance is claimed.

### Interview question
If training is 60% positive but test outcomes are 40% positive, what does the already-trained majority classifier predict and what accuracy results?

### My answer
> positive

> 40%

The learner also correctly predicted positive momentum despite a negative latest session and acknowledged that loss-triggered selling violates buy and hold. Independent explanations will be revisited.

## Phase 5 output check — Different benchmark horizons

### Concept learned
The latest session and multi-session momentum can imply different predictions without an implementation error.

### Explanation in my own words
> nonpositive

This correctly answered the latest-direction rule for a fall from $106 to $105 after the learner correctly identified positive five-session momentum from $100 to $105.

### Important formula
Single-session direction uses the latest return; multi-session momentum uses the whole window return, not a majority vote over daily directions.

### Common mistake
Initially described momentum as a majority. Clarified that it measures total price change across the window.

### How we used it
Inspected benchmark disagreement, then approved and merged PR #5.

### Interview question
Can a negative last session coexist with positive five-session momentum?

### My answer
The learner identified positive momentum and nonpositive latest-direction predictions after a guided example.

## Phase 6 — Walk-forward validation

### Concept learned
Expanding versus rolling windows, chronological out-of-sample evaluation, label availability, and training-only preprocessing. Introductory checkpoint passed; implementation walkthrough next.

### Explanation in my own words
> so we dont get look ahead bias and leakage as it could be beyond the models prediciton date

### Important formula
Training starts at a fixed date and expands; labels require outcome_session <= fit_after_session under the after-close availability contract. Test feature dates follow the fitting session.

### Common mistake
Initially said an expanding window discards earlier years; corrected to retaining 2010 as the start. Initially allowed 2020 outcomes before making 2020 predictions; corrected by considering 31 December 2019. Initially waited until after 2021 to use known 2020 outcomes; clarified that already-known 2020 outcomes can train the 2021 model. A final 2020 row with a January outcome must still wait. Initially answered only 2018 for preprocessing; clarified the entire 2010–2018 training period.

### How we used it
Built annual development folds with explicit date manifests and label checks. Benchmarks share complete-feature dates. Reserved 2024–2025 is removed before development features/targets. No learned preprocessing is needed for these rules; training-only model preprocessing is deferred to the model phase. No performance metrics or model tuning were introduced.

### Interview question
Why must a model predicting 2020 avoid outcomes beyond its prediction date?

### My answer
The learner's quotation above correctly explains look-ahead bias. They also correctly selected 2010–2019 training for the 2020 test year and waiting for January to finish before using a December row's January outcome.
