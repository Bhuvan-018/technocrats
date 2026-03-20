from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from train_and_evaluate import _collect_live_news
from news_db import upsert_articles


def main() -> None:
    live_df = _collect_live_news(per_feed=40)
    if live_df.empty:
        print("No live news collected.")
        return

    records = []
    now = datetime.now(timezone.utc).isoformat()
    for _, row in live_df.iterrows():
        records.append(
            {
                "source": str(row.get("source", "")).strip(),
                "title": str(row.get("title", "")).strip(),
                "summary": str(row.get("text", "")).strip(),
                "url": str(row.get("url", "")).strip(),
                "published_at": now,
            }
        )

    inserted = upsert_articles(records)
    print(f"Inserted {inserted} live articles into DB.")


if __name__ == "__main__":
    main()
