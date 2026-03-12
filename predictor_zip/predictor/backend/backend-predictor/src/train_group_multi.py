import argparse
import json
import os
import sys
from typing import Dict, List

import numpy as np
from tensorflow.keras.callbacks import CSVLogger, EarlyStopping, ReduceLROnPlateau, TerminateOnNaN

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.config import GROUP_LOOKBACK_WINDOW, GROUP_MODELS_DIR, MODEL_ARCHIVE_DIR, TRAINING_LOGS_DIR
from src.group_dataset import build_group_company_datasets
from src.groups import GROUP_A, GROUP_B, GROUP_COMPANIES, get_group_model_filename
from src.model_multi_head import build_multi_head_transformer
from src.train_utils import (
    adjust_batch_size,
    atomic_write_model_and_metadata,
    ensure_min_samples,
    set_global_seed,
    timestamp_tag,
    validate_training_payload,
)


def _split_company_timewise(
    data: Dict[str, np.ndarray], test_split: float = 0.2
) -> Dict[str, np.ndarray]:
    size = len(data["X"])
    split_idx = int(size * (1 - test_split))
    if split_idx <= 0 or split_idx >= size:
        raise ValueError(f"Invalid split for sample size {size}")

    return {
        "X_train": data["X"][:split_idx],
        "X_test": data["X"][split_idx:],
        "y_10m_train": data["y_10m"][:split_idx],
        "y_10m_test": data["y_10m"][split_idx:],
        "y_30m_train": data["y_30m"][:split_idx],
        "y_30m_test": data["y_30m"][split_idx:],
        "y_1h_train": data["y_1h"][:split_idx],
        "y_1h_test": data["y_1h"][split_idx:],
    }


def _concat(parts: List[np.ndarray]) -> np.ndarray:
    if not parts:
        raise ValueError("No arrays to concatenate")
    return np.concatenate(parts, axis=0)


def _shuffle_training(
    X: np.ndarray, y_10m: np.ndarray, y_30m: np.ndarray, y_1h: np.ndarray
) -> Dict[str, np.ndarray]:
    idx = np.random.permutation(len(X))
    return {
        "X": X[idx],
        "y_10m": y_10m[idx],
        "y_30m": y_30m[idx],
        "y_1h": y_1h[idx],
    }


def train_group_model(
    group_key: str,
    epochs: int = 50,
    batch_size: int = 64,
    lookback: int = GROUP_LOOKBACK_WINDOW,
    test_split: float = 0.2,
    refresh_data: bool = True,
    interval: str = "5m",
    period: str = "59d",
    mse_weight: float = 0.5,
    mae_weight: float = 0.5,
    directional_weight: float = 0.2,
    seed: int = 42,
    min_train_samples: int = 1000,
    min_test_samples: int = 200,
):
    if group_key not in {GROUP_A, GROUP_B}:
        raise ValueError(f"group_key must be one of {[GROUP_A, GROUP_B]}")

    set_global_seed(seed)
    print(f"Training grouped multi-horizon model for {group_key}...")
    group_datasets = build_group_company_datasets(
        group_key=group_key,
        lookback=lookback,
        refresh=refresh_data,
        interval=interval,
        period=period,
    )
    if not group_datasets:
        raise RuntimeError("No company dataset available for training")

    x_train_parts: List[np.ndarray] = []
    y10_train_parts: List[np.ndarray] = []
    y30_train_parts: List[np.ndarray] = []
    y1h_train_parts: List[np.ndarray] = []
    x_test_parts: List[np.ndarray] = []
    y10_test_parts: List[np.ndarray] = []
    y30_test_parts: List[np.ndarray] = []
    y1h_test_parts: List[np.ndarray] = []
    samples_by_ticker: Dict[str, int] = {}

    for ticker, arrays in group_datasets.items():
        split = _split_company_timewise(arrays, test_split=test_split)
        samples_by_ticker[ticker] = len(arrays["X"])

        x_train_parts.append(split["X_train"])
        y10_train_parts.append(split["y_10m_train"])
        y30_train_parts.append(split["y_30m_train"])
        y1h_train_parts.append(split["y_1h_train"])

        x_test_parts.append(split["X_test"])
        y10_test_parts.append(split["y_10m_test"])
        y30_test_parts.append(split["y_30m_test"])
        y1h_test_parts.append(split["y_1h_test"])

    X_train = _concat(x_train_parts)
    y_train_10m = _concat(y10_train_parts)
    y_train_30m = _concat(y30_train_parts)
    y_train_1h = _concat(y1h_train_parts)

    X_test = _concat(x_test_parts)
    y_test_10m = _concat(y10_test_parts)
    y_test_30m = _concat(y30_test_parts)
    y_test_1h = _concat(y1h_test_parts)

    shuffled = _shuffle_training(X_train, y_train_10m, y_train_30m, y_train_1h)
    X_train = shuffled["X"]
    y_train_10m = shuffled["y_10m"]
    y_train_30m = shuffled["y_30m"]
    y_train_1h = shuffled["y_1h"]

    ensure_min_samples(
        train_samples=len(X_train),
        test_samples=len(X_test),
        min_train_samples=min_train_samples,
        min_test_samples=min_test_samples,
    )
    validate_training_payload(
        {
            "X_train": X_train,
            "y_train_10m": y_train_10m,
            "y_train_30m": y_train_30m,
            "y_train_1h": y_train_1h,
            "X_test": X_test,
            "y_test_10m": y_test_10m,
            "y_test_30m": y_test_30m,
            "y_test_1h": y_test_1h,
        }
    )
    effective_batch_size = adjust_batch_size(batch_size, len(X_train))
    if effective_batch_size != batch_size:
        print(f"Adjusted batch size from {batch_size} to {effective_batch_size} due to dataset size.")

    input_shape = (X_train.shape[1], X_train.shape[2])
    model = build_multi_head_transformer(
        input_shape=input_shape,
        output_units=5,
        horizon_loss_weights={"forecast_10m": 1.0, "forecast_30m": 1.0, "forecast_1h": 1.0},
        mse_weight=mse_weight,
        mae_weight=mae_weight,
        directional_weight=directional_weight,
    )

    run_tag = f"{group_key}_{timestamp_tag()}"
    train_log_path = os.path.join(TRAINING_LOGS_DIR, f"train_{run_tag}.csv")
    callbacks = [
        EarlyStopping(monitor="val_loss", patience=10, min_delta=1e-5, restore_best_weights=True),
        ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=4, min_lr=1e-6),
        TerminateOnNaN(),
        CSVLogger(train_log_path, append=False),
    ]

    train_targets = {
        "forecast_10m": y_train_10m,
        "forecast_30m": y_train_30m,
        "forecast_1h": y_train_1h,
    }
    test_targets = {
        "forecast_10m": y_test_10m,
        "forecast_30m": y_test_30m,
        "forecast_1h": y_test_1h,
    }

    history = model.fit(
        X_train,
        train_targets,
        epochs=epochs,
        batch_size=effective_batch_size,
        validation_data=(X_test, test_targets),
        callbacks=callbacks,
        verbose=1,
    )

    results = model.evaluate(X_test, test_targets, return_dict=True, verbose=1)
    model_filename = get_group_model_filename(group_key)
    model_path = os.path.join(GROUP_MODELS_DIR, model_filename)
    model.save(model_path)

    metadata = {
        "group": group_key,
        "lookback": lookback,
        "interval": interval,
        "period": period,
        "test_split": test_split,
        "seed": seed,
        "mse_weight": mse_weight,
        "mae_weight": mae_weight,
        "directional_weight": directional_weight,
        "companies_requested": [c.ticker for c in GROUP_COMPANIES[group_key]],
        "companies_used": sorted(group_datasets.keys()),
        "samples_by_ticker": samples_by_ticker,
        "train_samples": int(len(X_train)),
        "test_samples": int(len(X_test)),
        "train_log_file": train_log_path,
        "model_file": model_path,
        "metrics": results,
        "best_val_loss": float(min(history.history.get("val_loss", [np.nan]))),
    }

    meta_path = os.path.join(GROUP_MODELS_DIR, model_filename.replace(".keras", "_meta.json"))
    archive_dir, _ = atomic_write_model_and_metadata(
        model=model,
        model_path=model_path,
        metadata=metadata,
        meta_path=meta_path,
        archive_root=MODEL_ARCHIVE_DIR,
        archive_bucket=f"group_{group_key}",
    )
    if archive_dir:
        metadata["archived_previous_to"] = archive_dir
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    print(f"Saved model: {model_path}")
    print(f"Saved metadata: {meta_path}")
    print(f"Training log: {train_log_path}")
    if archive_dir:
        print(f"Archived previous artifacts to: {archive_dir}")
    return model, metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train grouped multi-horizon transformer")
    parser.add_argument("--group", type=str, default=GROUP_A, choices=[GROUP_A, GROUP_B])
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lookback", type=int, default=GROUP_LOOKBACK_WINDOW)
    parser.add_argument("--test-split", type=float, default=0.2)
    parser.add_argument("--interval", type=str, default="5m")
    parser.add_argument("--period", type=str, default="59d")
    parser.add_argument("--mse-weight", type=float, default=0.5)
    parser.add_argument("--mae-weight", type=float, default=0.5)
    parser.add_argument("--directional-weight", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--min-train-samples", type=int, default=1000)
    parser.add_argument("--min-test-samples", type=int, default=200)
    parser.add_argument(
        "--no-refresh",
        action="store_true",
        help="Use cached intraday CSVs and skip API refresh",
    )

    args = parser.parse_args()

    train_group_model(
        group_key=args.group,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lookback=args.lookback,
        test_split=args.test_split,
        refresh_data=not args.no_refresh,
        interval=args.interval,
        period=args.period,
        mse_weight=args.mse_weight,
        mae_weight=args.mae_weight,
        directional_weight=args.directional_weight,
        seed=args.seed,
        min_train_samples=args.min_train_samples,
        min_test_samples=args.min_test_samples,
    )
