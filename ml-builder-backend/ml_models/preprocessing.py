# ml_models/preprocessing.py
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline


@dataclass
class PreprocessConfig:
    method: str  # "normalization" or "onehot"
    target_column: str
    feature_columns: List[str]
    numeric_columns: List[str]
    categorical_columns: List[str]


class PreprocessorFactory:
    """
    Builds a ColumnTransformer according to the selected method.

    - "normalization": scale numeric features + one-hot encode categoricals
    - "onehot":        leave numeric as-is (with imputation) + one-hot categoricals
    """

    @staticmethod
    def analyze_dataframe(df: pd.DataFrame, target_column: str) -> PreprocessConfig:
        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' not found in dataset.")

        feature_columns = [c for c in df.columns if c != target_column]

        numeric_columns = df[feature_columns].select_dtypes(include=[np.number]).columns.tolist()
        categorical_columns = [c for c in feature_columns if c not in numeric_columns]

        return PreprocessConfig(
            method="",
            target_column=target_column,
            feature_columns=feature_columns,
            numeric_columns=numeric_columns,
            categorical_columns=categorical_columns,
        )

    @staticmethod
    def build(config: PreprocessConfig, method: str) -> Tuple[ColumnTransformer, PreprocessConfig]:
        method = method.lower()
        if method not in ("normalization", "onehot"):
            raise ValueError("method must be 'normalization' or 'onehot'")

        config.method = method

        # Pipelines for numeric and categorical features
        if method == "normalization":
            # numeric: impute + scale
            num_pipeline = Pipeline(
                steps=[
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler()),
                ]
            )
        else:  # "onehot"
            # numeric: impute only (no scaling)
            num_pipeline = Pipeline(
                steps=[
                    ("imputer", SimpleImputer(strategy="median")),
                ]
            )

        cat_pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OneHotEncoder(handle_unknown="ignore")),
            ]
        )

        transformers = []
        if config.numeric_columns:
            transformers.append(("num", num_pipeline, config.numeric_columns))
        if config.categorical_columns:
            transformers.append(("cat", cat_pipeline, config.categorical_columns))

        if not transformers:
            raise ValueError("No usable features found (no numeric or categorical columns).")

        preprocessor = ColumnTransformer(transformers=transformers)

        return preprocessor, config
