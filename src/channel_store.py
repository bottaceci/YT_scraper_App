from __future__ import annotations

from typing import Any

from channels import CHANNELS
from models import ChannelConfig


def list_channels() -> list[ChannelConfig]:
    result: list[ChannelConfig] = []

    for raw_channel in CHANNELS:
        channel_id = str(raw_channel.get("id", "")).strip()
        label = str(raw_channel.get("label", "")).strip()

        if not channel_id or not label:
            continue

        result.append(ChannelConfig(channel_id=channel_id, label=label))

    return result