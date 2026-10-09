"""Model definition: the whole preprocessing + estimator lives in a single
scikit-learn Pipeline, so the exact same transformations run at training and
at serving time (no training/serving skew)."""
from typing import Any

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src.features.schema import CATEGORICAL_FEATURES, NUMERIC_FEATURES

DEFAULT_HYPERPARAMETERS = {
    "learning_rate": 0.05,
    "max_iter": 300,
    "max_depth": 4,
    "max_leaf_nodes": 31,
    "min_samples_leaf": 20,
    "l2_regularization": 1.0,
    "class_weight": "balanced",
    "random_state": 42,
}


def build_pipeline(hyperparameters: dict[str, Any] | None = None) -> Pipeline:
    params = {
        **DEFAULT_HYPERPARAMETERS,
        **(hyperparameters or {})
    }
    class_weight = params["class_weight"]
    if class_weight in ("none", "None", ""):
        class_weight = None

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                SimpleImputer(strategy="median"),
                NUMERIC_FEATURES,
            ),
            (
                "categorical",
                Pipeline(steps=[
                    (
                        "impute",
                        SimpleImputer(
                            strategy="constant",
                            fill_value="unknown",
                        ),
                    ),
                    (
                        "encode",
                        OneHotEncoder(
                            handle_unknown="ignore",
                            sparse_output=False,
                        ),
                    ),
                ]),
                CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )

    classifier = HistGradientBoostingClassifier(
        learning_rate=float(params["learning_rate"]),
        max_iter=int(params["max_iter"]),
        max_depth=int(params["max_depth"]),
        max_leaf_nodes=int(params["max_leaf_nodes"]),
        min_samples_leaf=int(params["min_samples_leaf"]),
        l2_regularization=float(params["l2_regularization"]),
        class_weight=class_weight,
        early_stopping=True,
        validation_fraction=0.1,
        random_state=int(params["random_state"]),
    )

    return Pipeline(steps=[
        ("preprocess", preprocessor),
        ("classifier", classifier),
    ])
