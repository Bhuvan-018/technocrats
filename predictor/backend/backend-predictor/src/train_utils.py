import json
import os
import random
import shutil
from datetime import datetime
from typing import Dict, Iterable, Optional, Tuple

import numpy as np
import tensorflow as tf


def timestamp_tag() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def set_global_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)


def validate_array(name: str, arr: np.ndarray) -> None:
    if arr is None or arr.size == 0:
        raise ValueError(f"{name} is empty")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} contains NaN/Inf values")


def validate_training_payload(payload: Dict[str, np.ndarray]) -> None:
    for key, value in payload.items():
        validate_array(key, value)


def ensure_min_samples(
    train_samples: int,
    test_samples: int,
    min_train_samples: int,
    min_test_samples: int,
) -> None:
    if train_samples < min_train_samples:
        raise ValueError(f"Not enough train samples: {train_samples} < {min_train_samples}")
    if test_samples < min_test_samples:
        raise ValueError(f"Not enough test samples: {test_samples} < {min_test_samples}")


def adjust_batch_size(requested: int, train_samples: int) -> int:
    if train_samples <= 0:
        raise ValueError("train_samples must be > 0")
    return max(8, min(requested, train_samples))


def archive_existing_files(paths: Iterable[str], archive_root: str, bucket: str) -> Optional[str]:
    existing = [p for p in paths if os.path.exists(p)]
    if not existing:
        return None

    archive_dir = os.path.join(archive_root, bucket, timestamp_tag())
    os.makedirs(archive_dir, exist_ok=True)
    for src in existing:
        dst = os.path.join(archive_dir, os.path.basename(src))
        shutil.move(src, dst)
    return archive_dir


def atomic_write_model_and_metadata(
    model,
    model_path: str,
    metadata: dict,
    meta_path: str,
    archive_root: str,
    archive_bucket: str,
) -> Tuple[Optional[str], str]:
    model_root, model_ext = os.path.splitext(model_path)
    if model_ext:
        tmp_model_path = f"{model_root}.tmp{model_ext}"
    else:
        tmp_model_path = f"{model_path}.tmp.keras"
    tmp_meta_path = f"{meta_path}.tmp"
    model.save(tmp_model_path)
    with open(tmp_meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    archive_dir = archive_existing_files(
        paths=[model_path, meta_path],
        archive_root=archive_root,
        bucket=archive_bucket,
    )

    os.replace(tmp_model_path, model_path)
    os.replace(tmp_meta_path, meta_path)
    return archive_dir, model_path
