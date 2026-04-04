from __future__ import annotations

import sqlite3
from pathlib import Path

import storage
import scraper
from models import ChannelConfig

DB_FILENAME = "channel_watcher.db"


def get_db_path() -> Path:
    return storage.get_data_dir() / DB_FILENAME


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS channels (
                channel_id TEXT PRIMARY KEY,
                label TEXT NOT NULL
            )
            """
        )
        conn.commit()


def list_channels() -> list[ChannelConfig]:
    init_db()

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT channel_id, label
            FROM channels
            ORDER BY label COLLATE NOCASE, channel_id
            """
        ).fetchall()

    return [
        ChannelConfig(
            channel_id=str(row["channel_id"]),
            label=str(row["label"]),
        )
        for row in rows
    ]


def add_channel(channel: ChannelConfig) -> None:
    channel_id = channel.channel_id.strip()
    label = channel.label.strip()

    if not channel_id:
        raise ValueError("Channel is missing a valid channel_id.")
    if not label:
        raise ValueError("Channel is missing a valid label.")

    init_db()

    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO channels (channel_id, label)
                VALUES (?, ?)
                """,
                (channel_id, label),
            )
            conn.commit()
    except sqlite3.IntegrityError as exc:
        raise ValueError(f"Channel already exists: {channel_id}") from exc

def add_channel_by_id(channel_id: str) -> ChannelConfig:
    resolved_channel = scraper.resolve_channel(channel_id)
    add_channel(resolved_channel)
    return resolved_channel


def remove_channel(channel_id: str) -> None:
    normalized_channel_id = channel_id.strip()
    if not normalized_channel_id:
        raise ValueError("channel_id cannot be empty.")

    init_db()

    with get_connection() as conn:
        conn.execute(
            """
            DELETE FROM channels
            WHERE channel_id = ?
            """,
            (normalized_channel_id,),
        )
        conn.commit()