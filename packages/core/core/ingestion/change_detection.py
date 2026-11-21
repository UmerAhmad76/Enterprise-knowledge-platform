"""Content hashing aur new/changed/unchanged decision. Incremental sync ka dil yahin hai."""
import hashlib
from enum import Enum


class ChangeKind(str, Enum):
    NEW = "new"
    CHANGED = "changed"
    UNCHANGED = "unchanged"


def content_hash(content: bytes) -> str:
    """Raw bytes ka SHA-256. Parsed text ki jagah raw bytes hash karte hen, taake har asli edit pakdi jaye."""
    return hashlib.sha256(content).hexdigest()


def classify(known_hash: str | None, new_hash: str) -> ChangeKind:
    """known_hash None ka matlab document pehli baar dikha hai. Same hash par re-embed nahi karte."""
    if known_hash is None:
        return ChangeKind.NEW
    return ChangeKind.UNCHANGED if known_hash == new_hash else ChangeKind.CHANGED