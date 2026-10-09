"""Binary classification metrics in the JSON layout SageMaker Model Registry
understands (`binary_classification_metrics.<metric>.value`), so they show up
in the model package's "Model quality" tab."""
import math
from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def _metric(value: float) -> dict[str, Any]:
    return {
        "value": float(value),
        "standard_deviation": "NaN",
    }


def compute_metrics(
    y_true: np.ndarray,
    y_score: np.ndarray,
    threshold: float = 0.5,
) -> dict[str, Any]:
    y_pred = (y_score >= threshold).astype(int)
    (tn, fp), (fn, tp) = confusion_matrix(y_true, y_pred, labels=[0, 1])
    return {
        "binary_classification_metrics": {
            "auc":
                _metric(roc_auc_score(y_true, y_score)),
            "average_precision":
                _metric(average_precision_score(y_true, y_score)),
            "accuracy":
                _metric(accuracy_score(y_true, y_pred)),
            "precision":
                _metric(precision_score(y_true, y_pred, zero_division=0)),
            "recall":
                _metric(recall_score(y_true, y_pred, zero_division=0)),
            "f1":
                _metric(f1_score(y_true, y_pred, zero_division=0)),
            "confusion_matrix": {
                "0": {
                    "0": int(tn),
                    "1": int(fp),
                },
                "1": {
                    "0": int(fn),
                    "1": int(tp),
                },
            },
        },
        "threshold": threshold,
        "samples": int(len(y_true)),
        "positive_rate": float(np.mean(y_true)) if len(y_true) else math.nan,
    }
