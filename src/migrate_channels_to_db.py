from __future__ import annotations

from channels import CHANNELS
from channel_store import get_connection, init_db


def main() -> None:
    init_db()

    rows_to_insert: list[tuple[str, str]] = []

    for raw_channel in CHANNELS:
        channel_id = str(raw_channel.get("id", "")).strip()
        label = str(raw_channel.get("label", "")).strip()

        if not channel_id or not label:
            print(f"Skipping invalid channel entry: {raw_channel!r}")
            continue

        rows_to_insert.append((channel_id, label))

    if not rows_to_insert:
        print("No valid channels found in channels.py")
        return

    with get_connection() as conn:
        conn.executemany(
            """
            INSERT OR IGNORE INTO channels (channel_id, label)
            VALUES (?, ?)
            """,
            rows_to_insert,
        )
        conn.commit()

        count_row = conn.execute(
            """
            SELECT COUNT(*) AS channel_count
            FROM channels
            """
        ).fetchone()

    channel_count = int(count_row["channel_count"]) if count_row else 0
    print(f"Migration complete. channels table now contains {channel_count} row(s).")


if __name__ == "__main__":
    main()