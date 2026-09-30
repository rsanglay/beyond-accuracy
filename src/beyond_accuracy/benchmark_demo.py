"""Synthetic teaching example, not a market evaluation or train/test splitter."""
import pandas as pd

from beyond_accuracy.benchmarks import MajorityBenchmark, predict_momentum, predict_previous_direction


def benchmark_demo() -> dict:
    dates = pd.bdate_range("2020-01-02", periods=11)
    training = pd.DataFrame({
        "target_up": [1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
        "outcome_session": dates[1:],
    }, index=dates[:-1])
    model = MajorityBenchmark.fit(training, fit_after_session=dates[-1])
    sessions = pd.bdate_range(dates[-1], periods=3)
    features = pd.DataFrame({
        "return_current": [.02, -.01, 0.],
        "momentum_5": [.05, .04, -.02],
    }, index=sessions)
    predictions = pd.DataFrame({
        "majority": model.predict(sessions),
        "previous_direction": predict_previous_direction(features),
        "momentum_5": predict_momentum(features, window=5),
    })
    return {
        "kind": "Synthetic illustration only; no SPY performance results",
        "training_positive": 6, "training_nonpositive": 4,
        "tie_policy": "0 (nonpositive)",
        "rows": [dict(session=str(date.date()), **{k: int(v) for k, v in row.items()})
                 for date, row in predictions.iterrows()],
    }
