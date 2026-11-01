"""Offline network-flow classification. No packet capture or network access."""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.inspection import permutation_importance

FEATURES = ['duration_s', 'packets', 'bytes', 'syn_count', 'rst_count', 'destination_port', 'mean_packet_size', 'interarrival_ms']
LABELS = ['BENIGN', 'DOS', 'PORT_SCAN']

def demo(n=2400, seed=42):
    """Illustrative overlapping distributions; NOT captured attack traffic."""
    rng = np.random.default_rng(seed)
    y = rng.choice(LABELS, n, p=[.65, .20, .15])
    severity = np.select([y == 'DOS', y == 'PORT_SCAN'], [2.0, 1.0], default=0.)
    packets = rng.lognormal(3.5 + (y == 'DOS') * 1.8, 1., n).astype(int) + 1
    size = rng.uniform(60, 1400, n)
    frame = pd.DataFrame({
        'duration_s': rng.lognormal(1, 1.2, n), 'packets': packets,
        'bytes': packets * size, 'syn_count': rng.poisson(2 + severity * 7),
        'rst_count': rng.poisson(1 + (y == 'PORT_SCAN') * 5),
        'destination_port': rng.choice([22, 53, 80, 443, 3389, 8080], n),
        'mean_packet_size': size,
        'interarrival_ms': rng.lognormal(4 - severity, 1.2, n), 'label': y})
    return frame

def validate(frame, labeled=False):
    if frame.empty or len(frame) > 100000:
        raise ValueError('Provide 1–100,000 rows.')
    missing = set(FEATURES + (['label'] if labeled else [])) - set(frame.columns)
    if missing:
        raise ValueError('Missing columns: ' + ', '.join(sorted(missing)))
    x = frame[FEATURES].apply(pd.to_numeric, errors='raise')
    if np.isinf(x.to_numpy()).any() or (x < 0).any().any():
        raise ValueError('Features must be nonnegative and finite; blank cells are imputed.')
    if x.isna().all().any():
        raise ValueError('A feature cannot be entirely missing.')
    if (x.destination_port.dropna() > 65535).any():
        raise ValueError('Destination ports must be at most 65535.')
    if labeled:
        if frame.label.isna().any() or not set(frame.label).issubset(LABELS):
            raise ValueError('Labels must be BENIGN, DOS, or PORT_SCAN.')
        if set(frame.label) != set(LABELS) or frame.label.value_counts().min() < 10:
            raise ValueError('Training requires at least 10 examples of every class.')
    return x

def train(frame, algorithm='Random Forest'):
    frame = frame.drop_duplicates(subset=FEATURES + ['label']).reset_index(drop=True)
    x = validate(frame, True)
    # Validation selects the model externally; test partition is reserved for reporting.
    xdev, xtest, ydev, ytest = train_test_split(x, frame.label, test_size=.2, stratify=frame.label, random_state=42)
    xtrain, xval, ytrain, yval = train_test_split(xdev, ydev, test_size=.25, stratify=ydev, random_state=43)
    cls = RandomForestClassifier if algorithm == 'Random Forest' else ExtraTreesClassifier
    model = make_pipeline(SimpleImputer(strategy='median'), cls(n_estimators=120, max_depth=14, min_samples_leaf=2, class_weight='balanced', random_state=42, n_jobs=-1))
    model.fit(xtrain, ytrain)
    predictions = model.predict(xtest)
    report = classification_report(ytest, predictions, labels=LABELS, output_dict=True, zero_division=0)
    cm = confusion_matrix(ytest, predictions, labels=LABELS)
    importance = permutation_importance(model, xval, yval, scoring='f1_macro', n_repeats=3, random_state=42, n_jobs=1)
    return model, report, cm, pd.Series(importance.importances_mean, index=FEATURES), {'train': len(xtrain), 'validation': len(xval), 'test': len(xtest)}

def predict(model, frame, threshold=.5):
    x = validate(frame)
    probabilities = model.predict_proba(x)
    classes = list(model.classes_)
    attack = 1 - probabilities[:, classes.index('BENIGN')]
    out = frame.copy()
    out['prediction'] = model.predict(x)
    out['attack_score'] = attack
    out['alert'] = attack >= threshold
    out['review_priority'] = np.select([attack >= .85, attack >= threshold], ['High', 'Review'], default='Low')
    return out
