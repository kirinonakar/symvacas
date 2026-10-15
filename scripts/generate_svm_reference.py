"""Regenerate portable SVM reference predictions; sklearn is fixture-only."""
import json
import math
from pathlib import Path
import random

import sklearn
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC, SVR
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error


def build():
    cases = []
    rng = random.Random(812)
    xs = [[rng.uniform(-3, 3), rng.uniform(-2, 2), 7] for _ in range(32)]
    test = [[-.7, .4, 7], [1.5, -1.1, 7], [0, 0, 7], [4, 3, 7]]
    for mode in ("svc", "svr"):
        for kernel in ("linear", "rbf"):
            ys = [int(a*b+.3*a > 0) if mode == "svc" else math.sin(a)+b*b-.2*a
                  for a, b, _ in xs]
            options = [kernel, 2, .7, .15]
            scaler = StandardScaler().fit(xs)
            model = (SVC if mode == "svc" else SVR)(
                kernel=kernel, C=2, gamma=.7, tol=1e-10,
                **({"epsilon": .15} if mode == "svr" else {}))
            model.fit(scaler.transform(xs), ys)
            predict = model.decision_function if mode == "svc" else model.predict
            cases.append({"mode": mode, "options": options,
                          "rows": [row+[y] for row, y in zip(xs, ys)],
                          "training": predict(scaler.transform(xs)).tolist(),
                          "test": test, "predictions": predict(scaler.transform(test)).tolist()})
            if mode == 'svc':
                assignment = [0]*len(xs)
                split_rng = random.Random(0)
                offset = 0
                for label in (0, 1):
                    indices = [i for i, y in enumerate(ys) if y == label]
                    split_rng.shuffle(indices)
                    for j, i in enumerate(indices): assignment[i] = (offset+j) % 5
                    offset = (offset+len(indices)) % 5
                held_out = [0]*len(xs)
                for fold in range(5):
                    train = [i for i in range(len(xs)) if assignment[i] != fold]
                    test_indices = [i for i in range(len(xs)) if assignment[i] == fold]
                    fold_scaler = StandardScaler().fit([xs[i] for i in train])
                    fold_model = SVC(kernel=kernel, C=2, gamma=.7, tol=1e-5, max_iter=100000).fit(
                        fold_scaler.transform([xs[i] for i in train]), [ys[i] for i in train])
                    assert fold_model.fit_status_ == 0, 'Reference CV fit did not converge'
                    predictions = fold_model.predict(fold_scaler.transform([xs[i] for i in test_indices]))
                    for i, prediction in zip(test_indices, predictions): held_out[i] = int(prediction)
                cases[-1]['crossValidation'] = {'predictions': held_out, 'folds': [i+1 for i in assignment]}
            else:
                order = list(range(len(xs)))
                random.Random(0).shuffle(order)
                assignment = [0]*len(xs)
                for position, index in enumerate(order): assignment[index] = position % 5
                held_out = [0.0]*len(xs)
                for fold in range(5):
                    train = [i for i in range(len(xs)) if assignment[i] != fold]
                    test_indices = [i for i in range(len(xs)) if assignment[i] == fold]
                    fold_scaler = StandardScaler().fit([xs[i] for i in train])
                    fold_model = SVR(kernel=kernel, C=2, gamma=.7, epsilon=.15, tol=1e-5, max_iter=100000).fit(
                        fold_scaler.transform([xs[i] for i in train]), [ys[i] for i in train])
                    assert fold_model.fit_status_ == 0, 'Reference regression CV fit did not converge'
                    predictions = fold_model.predict(fold_scaler.transform([xs[i] for i in test_indices]))
                    for i, prediction in zip(test_indices, predictions): held_out[i] = float(prediction)
                cases[-1]['crossValidation'] = {'predictions': held_out, 'folds': [i+1 for i in assignment],
                    'rSquared': r2_score(ys,held_out), 'rmse': math.sqrt(mean_squared_error(ys,held_out)),
                    'mae': mean_absolute_error(ys,held_out)}
    return {"source": "sklearn.svm.SVC/SVR with StandardScaler (population SD)",
            "version": sklearn.__version__, "tolerance": 3e-5, "cases": cases}


if __name__ == "__main__":
    path = Path(__file__).resolve().parents[1]/"tests/fixtures/svm_reference.json"
    path.write_text(json.dumps(build(), indent=2)+"\n", encoding="utf-8")
