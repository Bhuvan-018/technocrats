import argparse
import json
import os
import sys
from typing import Dict, List

import numpy as np
from keras.models import load_model
from tensorflow.keras.callbacks import CSVLogger, EarlyStopping, ModelCheckpoint, ReduceLROnPlateau, TerminateOnNaN

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.config import CHECKPOINTS_DIR, GROUP_LOOKBACK_WINDOW, MODEL_ARCHIVE_DIR, SECTOR_MODELS_DIR, TRAINING_LOGS_DIR
from src.model_multi_head import build_multi_head_transformer, compile_multi_head_model
from src.sector_dataset import build_sector_company_datasets
from src.sectors import SECTOR_BANKING, SECTOR_COMPANIES, SECTOR_ENERGY, SECTOR_IT, get_sector_model_filename
from src.train_utils import (
    adjust_batch_size,
    atomic_write_model_and_metadata,
    ensure_min_samples,
    set_global_seed,
    timestamp_tag,
    validate_training_payload,
)


def _sector_checkpoint_paths(sector_key: str):
    base = os.path.join(CHECKPOINTS_DIR, f"sector_{sector_key}")
    os.makedirs(base, exist_ok=True)
    return {
        "dir": base,
        "best": os.path.join(base, "best.keras"),
        "last": os.path.join(base, "last.keras"),
    }


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


def _balanced_stack_train_splits(
    train_splits: Dict[str, Dict[str, np.ndarray]],
    seed: int,
) -> Dict[str, np.ndarray]:
    """Downsample each ticker to the same size to reduce ticker dominance."""
    if not train_splits:
        raise ValueError("No train splits provided for balancing")

    min_samples = min(len(parts["X"]) for parts in train_splits.values())
    if min_samples <= 0:
        raise ValueError("Balanced sampling failed due to empty ticker split")

    rng = np.random.default_rng(seed)
    x_parts: List[np.ndarray] = []
    y10_parts: List[np.ndarray] = []
    y30_parts: List[np.ndarray] = []
    y1h_parts: List[np.ndarray] = []

    for ticker in sorted(train_splits.keys()):
        parts = train_splits[ticker]
        idx = rng.choice(len(parts["X"]), size=min_samples, replace=False)
        x_parts.append(parts["X"][idx])
        y10_parts.append(parts["y_10m"][idx])
        y30_parts.append(parts["y_30m"][idx])
        y1h_parts.append(parts["y_1h"][idx])

    return {
        "X": _concat(x_parts),
        "y_10m": _concat(y10_parts),
        "y_30m": _concat(y30_parts),
        "y_1h": _concat(y1h_parts),
        "per_ticker_samples": int(min_samples),
    }


def train_sector_model(
    sector_key: str,
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
    save_checkpoints: bool = True,
    resume_from: str = "none",
    resume_path: str = "",
    balance_train_samples: bool = False,
    early_stopping_patience: int = 10,
    lr_plateau_patience: int = 4,
    learning_rate: float = 0.001,
    dropout_rate: float = 0.1,
):
    if sector_key not in {SECTOR_BANKING, SECTOR_ENERGY, SECTOR_IT}:
        raise ValueError(f"Unknown sector key: {sector_key}")

    set_global_seed(seed)
    print(f"Training sector multi-horizon model for {sector_key}...")
    sector_datasets = build_sector_company_datasets(
        sector_key=sector_key,
        lookback=lookback,
        refresh=refresh_data,
        interval=interval,
        period=period,
    )
    if not sector_datasets:
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
    train_splits_by_ticker: Dict[str, Dict[str, np.ndarray]] = {}

    for ticker, arrays in sector_datasets.items():
        split = _split_company_timewise(arrays, test_split=test_split)
        samples_by_ticker[ticker] = len(arrays["X"])

        x_train_parts.append(split["X_train"])
        y10_train_parts.append(split["y_10m_train"])
        y30_train_parts.append(split["y_30m_train"])
        y1h_train_parts.append(split["y_1h_train"])
        train_splits_by_ticker[ticker] = {
            "X": split["X_train"],
            "y_10m": split["y_10m_train"],
            "y_30m": split["y_30m_train"],
            "y_1h": split["y_1h_train"],
        }

        x_test_parts.append(split["X_test"])
        y10_test_parts.append(split["y_10m_test"])
        y30_test_parts.append(split["y_30m_test"])
        y1h_test_parts.append(split["y_1h_test"])

    X_train = _concat(x_train_parts)
    y_train_10m = _concat(y10_train_parts)
    y_train_30m = _concat(y30_train_parts)
    y_train_1h = _concat(y1h_train_parts)

    balanced_per_ticker = None
    if balance_train_samples:
        balanced = _balanced_stack_train_splits(train_splits_by_ticker, seed=seed)
        X_train = balanced["X"]
        y_train_10m = balanced["y_10m"]
        y_train_30m = balanced["y_30m"]
        y_train_1h = balanced["y_1h"]
        balanced_per_ticker = int(balanced["per_ticker_samples"])
        print(
            "Balanced ticker sampling enabled: "
            f"{len(train_splits_by_ticker)} tickers x {balanced_per_ticker} samples each"
        )

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
    ckpt_paths = _sector_checkpoint_paths(sector_key)
    model_resume_source = None
    if resume_from == "best":
        model_resume_source = ckpt_paths["best"]
    elif resume_from == "last":
        model_resume_source = ckpt_paths["last"]
    elif resume_from == "path":
        model_resume_source = resume_path.strip()

    if model_resume_source and os.path.exists(model_resume_source):
        print(f"Resuming from checkpoint: {model_resume_source}")
        model = load_model(model_resume_source, compile=False)
        resume_input_features = None
        try:
            resume_input_features = int(model.input_shape[-1])
        except Exception:
            resume_input_features = None

        if resume_input_features is not None and resume_input_features != int(input_shape[-1]):
            print(
                "Checkpoint input shape mismatch "
                f"(checkpoint={resume_input_features}, current={input_shape[-1]}). "
                "Starting fresh model for this run."
            )
            model = build_multi_head_transformer(
                input_shape=input_shape,
                output_units=5,
                learning_rate=learning_rate,
                dropout_rate=dropout_rate,
                horizon_loss_weights={"forecast_10m": 1.0, "forecast_30m": 1.0, "forecast_1h": 1.0},
                mse_weight=mse_weight,
                mae_weight=mae_weight,
                directional_weight=directional_weight,
            )
            model_resume_source = None
        else:
            model = compile_multi_head_model(
                model=model,
                learning_rate=learning_rate,
                horizon_loss_weights={"forecast_10m": 1.0, "forecast_30m": 1.0, "forecast_1h": 1.0},
                mse_weight=mse_weight,
                mae_weight=mae_weight,
                directional_weight=directional_weight,
            )
    else:
        if resume_from != "none":
            print(f"Checkpoint not found for resume mode '{resume_from}'. Starting fresh training.")
        model = build_multi_head_transformer(
            input_shape=input_shape,
            output_units=5,
            learning_rate=learning_rate,
            dropout_rate=dropout_rate,
            horizon_loss_weights={"forecast_10m": 1.0, "forecast_30m": 1.0, "forecast_1h": 1.0},
            mse_weight=mse_weight,
            mae_weight=mae_weight,
            directional_weight=directional_weight,
        )

    run_tag = f"{sector_key}_{timestamp_tag()}"
    train_log_path = os.path.join(TRAINING_LOGS_DIR, f"train_{run_tag}.csv")
    callbacks = [
        EarlyStopping(monitor="val_loss", patience=early_stopping_patience, min_delta=1e-5, restore_best_weights=True),
        ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=lr_plateau_patience, min_lr=1e-6),
        TerminateOnNaN(),
        CSVLogger(train_log_path, append=False),
    ]
    if save_checkpoints:
        callbacks.extend(
            [
                ModelCheckpoint(
                    filepath=ckpt_paths["best"],
                    monitor="val_loss",
                    save_best_only=True,
                    save_weights_only=False,
                    verbose=1,
                ),
                ModelCheckpoint(
                    filepath=ckpt_paths["last"],
                    monitor="val_loss",
                    save_best_only=False,
                    save_weights_only=False,
                    verbose=0,
                ),
            ]
        )

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

    model_filename = get_sector_model_filename(sector_key)
    model_path = os.path.join(SECTOR_MODELS_DIR, model_filename)
    model.save(model_path)

    metadata = {
        "sector": sector_key,
        "lookback": lookback,
        "interval": interval,
        "period": period,
        "test_split": test_split,
        "seed": seed,
        "mse_weight": mse_weight,
        "mae_weight": mae_weight,
        "directional_weight": directional_weight,
        "companies_requested": [c.ticker for c in SECTOR_COMPANIES[sector_key]],
        "companies_used": sorted(sector_datasets.keys()),
        "samples_by_ticker": samples_by_ticker,
        "train_samples": int(len(X_train)),
        "test_samples": int(len(X_test)),
        "train_log_file": train_log_path,
        "model_file": model_path,
        "checkpoint_dir": ckpt_paths["dir"],
        "best_checkpoint": ckpt_paths["best"] if save_checkpoints else None,
        "last_checkpoint": ckpt_paths["last"] if save_checkpoints else None,
        "resumed_from": model_resume_source if (model_resume_source and os.path.exists(model_resume_source)) else None,
        "balance_train_samples": balance_train_samples,
        "balanced_per_ticker_train_samples": balanced_per_ticker,
        "early_stopping_patience": early_stopping_patience,
        "lr_plateau_patience": lr_plateau_patience,
        "learning_rate": learning_rate,
        "dropout_rate": dropout_rate,
        "metrics": results,
        "best_val_loss": float(min(history.history.get("val_loss", [np.nan]))),
    }

    meta_path = os.path.join(SECTOR_MODELS_DIR, model_filename.replace(".keras", "_meta.json"))
    archive_dir, _ = atomic_write_model_and_metadata(
        model=model,
        model_path=model_path,
        metadata=metadata,
        meta_path=meta_path,
        archive_root=MODEL_ARCHIVE_DIR,
        archive_bucket=f"sector_{sector_key}",
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
    parser = argparse.ArgumentParser(description="Train sector multi-horizon transformer")
    parser.add_argument("--group", type=str, default=SECTOR_BANKING, choices=[SECTOR_BANKING, SECTOR_ENERGY, SECTOR_IT])
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
    parser.add_argument("--resume-from", type=str, default="none", choices=["none", "best", "last", "path"])
    parser.add_argument("--resume-path", type=str, default="")
    parser.add_argument("--no-checkpoints", action="store_true")
    parser.add_argument("--no-refresh", action="store_true")
    parser.add_argument("--balance-train-samples", action="store_true")
    parser.add_argument("--early-stopping-patience", type=int, default=10)
    parser.add_argument("--lr-plateau-patience", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=0.001)
    parser.add_argument("--dropout-rate", type=float, default=0.1)
    args = parser.parse_args()

    train_sector_model(
        sector_key=args.group,
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
        save_checkpoints=not args.no_checkpoints,
        resume_from=args.resume_from,
        resume_path=args.resume_path,
        balance_train_samples=args.balance_train_samples,
        early_stopping_patience=args.early_stopping_patience,
        lr_plateau_patience=args.lr_plateau_patience,
        learning_rate=args.learning_rate,
        dropout_rate=args.dropout_rate,
    )
