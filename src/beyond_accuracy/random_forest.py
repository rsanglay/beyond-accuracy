"""Fixed-complexity Random Forest fitted within one annual training window."""
from dataclasses import dataclass, fields
import hashlib
import json
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from beyond_accuracy.model_inputs import validate_model_inputs


@dataclass(frozen=True)
class ForestConfig:
    n_estimators: int
    max_depth: int
    min_samples_leaf: int
    max_features: str
    threshold: float
    random_seed: int

    def __post_init__(self):
        for name in ('n_estimators', 'max_depth', 'min_samples_leaf'):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f'{name} must be a positive integer')
        if self.max_features not in ('sqrt', 'log2'):
            raise ValueError('max_features must be sqrt or log2')
        if type(self.threshold) not in (int, float) or not np.isfinite(self.threshold) or not 0 < self.threshold < 1:
            raise ValueError('threshold must be finite and between 0 and 1')
        if type(self.random_seed) is not int or not 0 <= self.random_seed <= 2**32 - 1:
            raise ValueError('random_seed must be a valid nonnegative 32-bit integer')


def load_forest_config(path: Path) -> ForestConfig:
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or set(data) != {f.name for f in fields(ForestConfig)}:
        raise ValueError('Forest configuration fields do not match the required schema')
    return ForestConfig(**data)


def fit_predict_forest(train_x: pd.DataFrame, training_targets: pd.DataFrame,
                       test_x: pd.DataFrame, *, fit_after_session: pd.Timestamp,
                       config: ForestConfig) -> tuple[pd.DataFrame, dict]:
    labels = validate_model_inputs(train_x, training_targets, test_x, fit_after_session)
    model = RandomForestClassifier(
        n_estimators=config.n_estimators, max_depth=config.max_depth,
        min_samples_leaf=config.min_samples_leaf, max_features=config.max_features,
        random_state=config.random_seed, bootstrap=True, criterion='gini',
        class_weight=None, n_jobs=1, oob_score=False, warm_start=False,
    )
    start = perf_counter()
    model.fit(train_x, labels)
    fit_seconds = perf_counter() - start
    start = perf_counter()
    positive_column = list(model.classes_).index(1)
    probabilities = model.predict_proba(test_x)[:, positive_column]
    inference_seconds = perf_counter() - start
    if not np.isfinite(probabilities).all() or ((probabilities < 0) | (probabilities > 1)).any():
        raise ValueError('Invalid forest probabilities')
    predictions = pd.DataFrame({
        'forest_probability_up': probabilities,
        'forest_class': (probabilities >= config.threshold).astype(int),
    }, index=test_x.index)
    # A deterministic audit fingerprint, not a portable model serialisation.
    fingerprint = hashlib.sha256()
    minimum_leaf_counts = []
    for estimator in model.estimators_:
        tree = estimator.tree_
        for values in (tree.children_left, tree.children_right, tree.feature, tree.threshold, tree.value):
            fingerprint.update(values.tobytes())
        minimum_leaf_counts.append(int(tree.n_node_samples[tree.children_left == -1].min()))
    audit = {
        'training_rows': len(train_x), 'feature_columns': train_x.columns.tolist(),
        'classes': model.classes_.tolist(), 'preprocessing': 'None; no fitted scaling',
        'bootstrap': True, 'oob_score': False, 'criterion': 'gini', 'class_weight': None, 'n_jobs': 1,
        'tree_count': len(model.estimators_),
        'tree_depths': [int(t.get_depth()) for t in model.estimators_],
        'tree_leaf_counts': [int(t.get_n_leaves()) for t in model.estimators_],
        'tree_minimum_unique_leaf_samples': minimum_leaf_counts,
        'model_fingerprint_sha256': fingerprint.hexdigest(),
        'fit_seconds': fit_seconds, 'inference_seconds': inference_seconds,
    }
    return predictions, audit
