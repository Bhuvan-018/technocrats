from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

import joblib


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "fake_news_classifier_model.joblib"
VECTORIZER_PATH = BASE_DIR / "tfidf_vectorizer.joblib"
REPORT_PATH = BASE_DIR / "realtime_sanity_metrics.json"

RSS_URLS = [
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
]

FAKE_SAMPLES = [
    "NASA confirms the Moon is made of cheese after secret probe",
    "World leaders sign treaty to abolish gravity by 2030",
    "Scientists discover unicorn fossils in the Himalayas",
    "Doctors confirm eating only chocolate guarantees a 200-year lifespan",
    "Global finance ministers ban mathematics in stock trading",
]


def _strip(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _read_rss_titles(url: str, max_items: int = 8) -> list[str]:
    with urllib.request.urlopen(url, timeout=30) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)
    titles: list[str] = []
    for item in root.findall(".//item"):
        title_el = item.find("title")
        if title_el is None or not title_el.text:
            continue
        t = _strip(title_el.text)
        if t:
            titles.append(t)
        if len(titles) >= max_items:
            break
    return titles


def _predict(texts: list[str]) -> list[str]:
    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECTORIZER_PATH)
    x = vectorizer.transform(texts)
    y = model.predict(x)
    return ["real" if int(v) == 1 else "fake" for v in y]


def main() -> None:
    real_samples: list[str] = []
    for url in RSS_URLS:
        real_samples.extend(_read_rss_titles(url))

    real_samples = real_samples[:12]

    real_pred = _predict(real_samples)
    fake_pred = _predict(FAKE_SAMPLES)

    real_correct = sum(1 for p in real_pred if p == "real")
    fake_correct = sum(1 for p in fake_pred if p == "fake")

    total = len(real_samples) + len(FAKE_SAMPLES)
    accuracy = (real_correct + fake_correct) / total if total else 0.0

    report = {
        "real_samples": len(real_samples),
        "fake_samples": len(FAKE_SAMPLES),
        "overall_accuracy": accuracy,
        "real_recall": real_correct / len(real_samples) if real_samples else 0.0,
        "fake_recall": fake_correct / len(FAKE_SAMPLES) if FAKE_SAMPLES else 0.0,
        "details": {
            "real": [
                {"text": t, "predicted": p}
                for t, p in zip(real_samples, real_pred)
            ],
            "fake": [
                {"text": t, "predicted": p}
                for t, p in zip(FAKE_SAMPLES, fake_pred)
            ],
        },
    }

    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Realtime sanity check complete. Overall accuracy: {accuracy:.4f}")
    print(f"Real recall: {report['real_recall']:.4f}")
    print(f"Fake recall: {report['fake_recall']:.4f}")
    print(f"Report saved: {REPORT_PATH}")


if __name__ == "__main__":
    main()
