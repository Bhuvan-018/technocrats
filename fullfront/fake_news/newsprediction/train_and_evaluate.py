from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import urllib.request
from xml.etree import ElementTree as ET

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "fake_news_classifier_model.joblib"
VECTORIZER_PATH = BASE_DIR / "tfidf_vectorizer.joblib"
METRICS_PATH = BASE_DIR / "training_metrics.json"
LIVE_NEWS_DATASET_PATH = BASE_DIR / "live_news_real.csv"

FAKE_CSV_URL = "https://huggingface.co/datasets/genesisqu/fake-real-news/resolve/main/Fake.csv"
REAL_CSV_URL = "https://huggingface.co/datasets/genesisqu/fake-real-news/resolve/main/True.csv"

LIVE_RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "https://feeds.reuters.com/reuters/topNews",
    "https://feeds.reuters.com/reuters/worldNews",
    "https://rss.dw.com/rdf/rss-en-top",
    "https://www.aljazeera.com/xml/rss/all.xml",
]


def _as_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _build_text(df: pd.DataFrame) -> pd.Series:
    title = df.get("title", "").fillna("").astype(str)
    text = df.get("text", "").fillna("").astype(str)
    combined = (title + " " + text).str.replace(r"\s+", " ", regex=True).str.strip()
    return combined


def _normalize_ws(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "")).strip()


def _collect_live_news(per_feed: int) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for feed_url in LIVE_RSS_FEEDS:
        try:
            with urllib.request.urlopen(feed_url, timeout=30) as response:
                xml_data = response.read()
            root = ET.fromstring(xml_data)
        except Exception:
            continue

        count = 0
        for item in root.findall(".//item"):
            title = _normalize_ws(item.findtext("title") or "")
            description = _normalize_ws(item.findtext("description") or "")
            link = _normalize_ws(item.findtext("link") or "")

            if not title and not description:
                continue

            rows.append(
                {
                    "title": title,
                    "text": description,
                    "source": feed_url,
                    "url": link,
                    "label": 1,
                }
            )
            count += 1
            if count >= per_feed:
                break

    if not rows:
        return pd.DataFrame(columns=["title", "text", "source", "url", "label"])

    live_df = pd.DataFrame(rows)
    live_df["combined_text"] = _build_text(live_df)
    live_df = live_df[live_df["combined_text"].str.len() > 0].copy()
    live_df = live_df.drop_duplicates(subset=["combined_text"], keep="first")
    live_df = live_df.drop(columns=["combined_text"])
    return live_df


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and evaluate fake-news model")
    parser.add_argument("--test-size", type=float, default=0.2, help="Test split ratio")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--live-news-per-feed",
        type=int,
        default=40,
        help="Max live RSS items to ingest per feed",
    )
    args = parser.parse_args()

    print("Loading labeled fake/real datasets")
    fake_df = pd.read_csv(FAKE_CSV_URL)
    real_df = pd.read_csv(REAL_CSV_URL)

    fake_df["label"] = 0
    real_df["label"] = 1

    print("Collecting live news from RSS feeds")
    live_real_df = _collect_live_news(args.live_news_per_feed)
    if not live_real_df.empty:
        live_real_df.to_csv(LIVE_NEWS_DATASET_PATH, index=False)
        real_df = pd.concat([real_df, live_real_df], ignore_index=True)
        print(f"Added live real samples: {len(live_real_df)}")
    else:
        print("No live news rows collected; training with base dataset only")

    merged = pd.concat([fake_df, real_df], ignore_index=True)
    merged["combined_text"] = _build_text(merged)
    merged = merged[merged["combined_text"].str.len() > 0].copy()

    if merged.empty:
        raise RuntimeError("No valid rows found in dataset after preprocessing.")

    x = merged["combined_text"].tolist()
    y = merged["label"].astype(int).tolist()

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=args.test_size,
        random_state=args.random_state,
        stratify=y,
    )

    vectorizer = TfidfVectorizer(
        max_features=80000,
        ngram_range=(1, 2),
        min_df=2,
        sublinear_tf=True,
        strip_accents="unicode",
    )

    x_train_vec = vectorizer.fit_transform(x_train)
    x_test_vec = vectorizer.transform(x_test)

    model = LogisticRegression(
        max_iter=4000,
        class_weight="balanced",
        solver="liblinear",
    )
    model.fit(x_train_vec, y_train)

    y_pred = model.predict(x_test_vec)

    acc = accuracy_score(y_test, y_pred)
    report = classification_report(
        y_test,
        y_pred,
        target_names=["fake", "real"],
        output_dict=True,
        zero_division=0,
    )
    cm = confusion_matrix(y_test, y_pred).tolist()

    joblib.dump(model, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)

    metrics = {
        "dataset": "genesisqu/fake-real-news (Fake.csv + True.csv)",
        "live_news_dataset": str(LIVE_NEWS_DATASET_PATH.name),
        "live_real_samples_added": int(len(live_real_df)),
        "train_samples": len(x_train),
        "test_samples": len(x_test),
        "accuracy": acc,
        "classification_report": report,
        "confusion_matrix": {
            "labels": ["fake", "real"],
            "matrix": cm,
        },
        "artifacts": {
            "model": str(MODEL_PATH.name),
            "vectorizer": str(VECTORIZER_PATH.name),
        },
    }

    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print("Training complete")
    print(f"Train samples: {len(x_train)}")
    print(f"Test samples: {len(x_test)}")
    print(f"Accuracy: {acc:.4f}")
    print(f"Metrics saved: {METRICS_PATH}")


if __name__ == "__main__":
    main()
