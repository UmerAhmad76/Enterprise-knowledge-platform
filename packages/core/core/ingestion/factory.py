"""Source row ki config se connector banata hai. Naye source kinds yahin register hote hen."""
import uuid
from pathlib import Path
from typing import Any

from core.common.errors import EKPError
from core.ingestion.connectors.base import Connector
from core.ingestion.connectors.local_fs import LocalFileConnector


class UnknownSourceKind(EKPError):
    """Source ka kind kisi connector se match nahi karta."""


def build_connector(kind: str, config: dict[str, Any]) -> Connector:
    if kind == "local_fs":
        if "root" not in config:
            raise ValueError("local_fs source needs config.root")
        return LocalFileConnector(
            root=Path(config["root"]),
            allowed_group_ids=_uuid_set(config.get("allowed_group_ids", [])),
            allowed_user_ids=_uuid_set(config.get("allowed_user_ids", [])),
        )
    raise UnknownSourceKind(kind)


def _uuid_set(values: list[str]) -> frozenset[uuid.UUID]:
    return frozenset(uuid.UUID(value) for value in values)