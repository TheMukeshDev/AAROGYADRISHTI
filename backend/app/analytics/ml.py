"""Optional personal-wellbeing model (Phase 2, section 13).

This module is deliberately GATED: it only runs once a user has enough of their
OWN time-series data (``ml_min_samples``), and it is strictly described as a
"personal wellbeing pattern model" - it is never a disease-prediction model.

Implementation notes:

- Target: ``next_day_energy`` (energy at day N+1).
- Features: habit variables recorded at day N (sleep, steps, activity, screen
  time, hydration, stress, food quality, caffeine, exercise, late screen).
- Chronological train/test split (train = earlier days, test = later days).
  No shuffling, no random leakage - target and features are always separated by
  at least one day.
- Model: XGBoost when available, else scikit-learn GradientBoosting, else the
  module reports "unavailable" rather than inventing results.
- Explainability: feature importances always; SHAP summary included when the
  ``shap`` package is importable (some locked-down environments block its DLLs).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from app.analytics.config import AnalyticsConfig

ML_FEATURES = [
    "sleep_hours",
    "steps",
    "active_minutes",
    "exercise_minutes",
    "screen_time_minutes",
    "water_liters",
    "stress",
    "mood",
    "caffeine",
    "meal_quality",
    "late_night_screen",
]

ML_DISCLAIMER = (
    "This model describes patterns in your own checked-in data. It is a "
    "personal wellbeing pattern model, not a medical or disease-prediction model."
)


@dataclass
class MLResult:
    status: str = "insufficient_data"  # trained | insufficient_data | unavailable | error
    message: str = ""
    model_name: str | None = None
    n_samples: int = 0
    n_features: int = 0
    metrics: dict = field(default_factory=dict)
    importances: list[dict] = field(default_factory=list)
    shap_summary: list[dict] = field(default_factory=list)
    target: str = "next_day_energy"
    disclaimer: str = ML_DISCLAIMER

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "message": self.message,
            "model_name": self.model_name,
            "n_samples": self.n_samples,
            "target": self.target,
            "metrics": {k: round(v, 4) for k, v in self.metrics.items()},
            "importances": self.importances,
            "shap_summary": self.shap_summary,
            "disclaimer": self.disclaimer,
        }


def _import_model():
    """Return ``(model_factory, name)`` preferring XGBoost over sklearn.

    Raises ``ImportError`` if neither is importable.
    """
    try:
        from xgboost import XGBRegressor

        return (lambda: XGBRegressor(n_estimators=120, max_depth=3, learning_rate=0.05,
                                      subsample=0.9, colsample_bytree=0.9, verbosity=0)), "xgboost"
    except ImportError:
        pass
    try:
        from sklearn.ensemble import GradientBoostingRegressor

        return (lambda: GradientBoostingRegressor(n_estimators=120, max_depth=3, learning_rate=0.05)), "sklearn.gradient_boosting"
    except ImportError:
        pass
    raise ImportError("No gradient-boosting backend available (xgboost / scikit-learn).")


class PersonalWellbeingModel:
    def __init__(self, config: AnalyticsConfig | None = None) -> None:
        self.config = config or AnalyticsConfig.default()

    def run(self, features_df) -> MLResult:
        if features_df.empty or self.config.ml_min_samples <= 0:
            return MLResult(status="insufficient_data",
                            message="Not enough data to build a personalised model.")

        present = [f for f in ML_FEATURES if f in features_df.columns]
        if "energy" not in features_df.columns:
            return MLResult(status="insufficient_data", message="Energy check-ins are needed.")

        df = features_df.reset_index(drop=True)
        y = df["energy"].shift(-1)  # next-day energy
        mask = y.notna()
        if int(mask.sum()) < self.config.ml_min_samples:
            return MLResult(
                status="insufficient_data",
                message=f"A personal wellbeing model needs at least {self.config.ml_min_samples} days "
                        "with a next-day energy reading. Keep checking in.",
            )

        X = df.loc[mask, present].copy()
        Y = y[mask].to_numpy(dtype=float)
        # Mean-impute missing feature values (feature-only imputation; the
        # target is never imputed).
        X = X.apply(lambda col: col.fillna(col.mean()), axis=0).to_numpy(dtype=float)

        n = len(Y)
        split = max(int(n * 0.7), 10)
        if n - split < 3:
            return MLResult(status="insufficient_data", message="Not enough data for a hold-out split.")

        X_train, X_test = X[:split], X[split:]
        y_train, y_test = Y[:split], Y[split:]

        try:
            factory, model_name = _import_model()
        except ImportError:
            return MLResult(status="unavailable",
                            message="ML backend not installed in this environment; statistics-only mode.")

        try:
            model = factory()
            model.fit(X_train, y_train)
        except Exception as exc:  # pragma: no cover - defensive
            return MLResult(status="error", message=f"Model failed to fit: {type(exc).__name__}.")

        pred = model.predict(X_test)
        rmse = float(np.sqrt(np.mean((pred - y_test) ** 2)))
        ss_res = float(np.sum((y_test - pred) ** 2))
        ss_tot = float(np.sum((y_test - np.mean(y_test)) ** 2))
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

        raw_importances = getattr(model, "feature_importances_", None)
        importances: list[dict] = []
        if raw_importances is not None:
            order = np.argsort(raw_importances)[::-1]
            importances = [
                {"feature": present[i], "importance": round(float(raw_importances[i]), 4)}
                for i in order
            ]

        return MLResult(
            status="trained",
            message="Personal wellbeing pattern model trained on your own data.",
            model_name=model_name,
            n_samples=len(X_test),
            n_features=len(present),
            metrics={"rmse": rmse, "r2": r2},
            importances=importances,
            shap_summary=self._shap_summary(model, X_test, present),
            disclaimer=ML_DISCLAIMER,
        )

    def _shap_summary(self, model: Any, X_test: np.ndarray, feature_names: list[str]) -> list[dict]:
        try:
            import shap  # optional - blocked on some locked-down machines

            explainer = shap.TreeExplainer(model)
            values = explainer.shap_values(X_test[: min(len(X_test), 50)])
            means = np.abs(values).mean(axis=0)
            order = np.argsort(means)[::-1]
            return [
                {"feature": feature_names[i], "mean_abs_shap": round(float(means[i]), 4)}
                for i in order
            ]
        except Exception:
            return []