"""Local benchmark predictions on chronological development folds; no final-period evaluation."""
from dataclasses import asdict
from datetime import datetime, timezone
from importlib.metadata import distributions
import json
from pathlib import Path
import platform
import tempfile
import uuid

import pandas as pd

from beyond_accuracy.benchmarks import MajorityBenchmark, predict_momentum, predict_previous_direction
from beyond_accuracy.features import FeatureConfig, build_features
from beyond_accuracy.logistic import LogisticConfig, fit_predict_logistic
from beyond_accuracy.snapshots import git_state, sha256, verify_snapshot
from beyond_accuracy.targets import build_targets
from beyond_accuracy.walk_forward import WalkForwardConfig, expanding_folds


def run_walk_forward(snapshot: Path, feature_config: FeatureConfig,
                     config: WalkForwardConfig, output: Path,
                     logistic_config: LogisticConfig | None = None) -> Path:
    source = verify_snapshot(snapshot)
    if config.momentum_window not in feature_config.momentum_windows:
        raise ValueError('Benchmark momentum window must exist in feature configuration')
    if source['config']['start'] > config.training_start or source['config']['end'] < f'{config.last_test_year + 1}-01-01':
        raise ValueError('Snapshot does not cover the requested development schedule')
    bars = pd.read_csv(snapshot / 'provider.csv', index_col='Date', parse_dates=True)
    # Remove reserved prices BEFORE creating targets, including the year-boundary target.
    bars = bars.loc[(bars.index >= config.training_start) & (bars.index < config.reserved_start)]
    features = build_features(bars, feature_config)
    features = features[[c for c in features if not c.endswith('_diagnostic')]]
    targets = build_targets(bars['Adj Close'])
    folds = expanding_folds(features, targets, config)
    predictions, manifest = [], []
    for fold in folds:
        training = targets.loc[fold.training_sessions]
        model = MajorityBenchmark.fit(training, fit_after_session=fold.fit_after_session)
        test_features = features.loc[fold.test_sessions]
        predicted = pd.DataFrame({
            'majority': model.predict(fold.test_sessions),
            'previous_direction': predict_previous_direction(test_features),
            f'momentum_{config.momentum_window}': predict_momentum(test_features, window=config.momentum_window),
        })
        if predicted.isna().any().any():
            raise ValueError('A benchmark did not predict all common test dates')
        logistic_audit = None
        if logistic_config is not None:
            logistic_predictions, logistic_audit = fit_predict_logistic(
                features.loc[fold.training_sessions], training, test_features,
                fit_after_session=fold.fit_after_session, config=logistic_config)
            predicted = predicted.join(logistic_predictions)
        predicted['test_year'] = fold.test_year
        predictions.append(predicted)
        manifest.append({
            'test_year': fold.test_year, 'fit_after_session': str(fold.fit_after_session.date()),
            'training_first': str(fold.training_sessions[0].date()),
            'training_last': str(fold.training_sessions[-1].date()),
            'training_rows': len(fold.training_sessions), 'prediction_rows': len(fold.test_sessions),
            'unavailable_training_labels': fold.unavailable_training_labels,
            'majority_class': model.predicted_class,
            'logistic': logistic_audit,
            'training_sessions': fold.training_sessions.strftime('%Y-%m-%d').tolist(),
            'test_sessions': fold.test_sessions.strftime('%Y-%m-%d').tolist(),
        })
    combined = pd.concat(predictions)
    outcomes = targets.loc[combined.index].copy()
    outcomes['eligible_for_scoring'] = outcomes.target_up.notna()
    created = datetime.now(timezone.utc)
    output.mkdir(parents=True, exist_ok=True)
    destination = output / (created.strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:12])
    with tempfile.TemporaryDirectory(prefix='.pending-', dir=output) as directory:
        staging = Path(directory)
        combined.to_csv(staging / 'predictions.csv', index_label='Date')
        outcomes.to_csv(staging / 'outcomes.csv', index_label='Date', date_format='%Y-%m-%d')
        (staging / 'folds.json').write_text(json.dumps(manifest, indent=2) + '\n')
        metadata = {
            'schema_version': 1, 'created_at_utc': created.isoformat(),
            'config': asdict(config), 'feature_config': asdict(feature_config),
            'candidate_columns': features.columns.tolist(),
            'logistic_config': asdict(logistic_config) if logistic_config is not None else None,
            'source_snapshot_id': snapshot.name, 'source_metadata_sha256': sha256(snapshot / 'metadata.json'),
            'source_file_sha256': source['sha256'],
            'prediction_rows': len(combined), 'scorable_rows': int(outcomes.eligible_for_scoring.sum()),
            'preprocessing': 'Benchmarks unscaled; optional Logistic Regression uses a fresh StandardScaler fitted on each training fold only.',
            'timing': 'Fit once after the final session before each test year; predict after each test session closes. Not an execution model.',
            'limitations': 'Development predictions only; no accuracy/financial metrics or tuning. Reserved period excluded before feature/target construction. Snapshot validation reads full history for integrity, not model fitting.',
            'git': git_state(), 'python': platform.python_version(), 'platform': platform.platform(),
            'packages': dict(sorted((d.metadata['Name'], d.version) for d in distributions())),
            'sha256': {name: sha256(staging / name) for name in ['predictions.csv', 'outcomes.csv', 'folds.json']},
        }
        (staging / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
        staging.rename(destination)
    return destination
