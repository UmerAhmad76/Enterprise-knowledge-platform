"""Local directory connector. Development ke liye, aur dusre connectors ke liye reference implementation."""
import uuid
from pathlib import Path

from core.ingestion.connectors.base import Connector
from core.ingestion.types import RawDocument

CONTENT_TYPES = {".md": "text/markdown", ".txt": "text/plain"}


class LocalFileConnector(Connector):
    """Ek root folder ke supported files padhta hai. ACL source level par set hota hai, file level par nahi."""

    kind = "local_fs"

    def __init__(
        self,
        root: Path,
        allowed_group_ids: frozenset[uuid.UUID] = frozenset(),
        allowed_user_ids: frozenset[uuid.UUID] = frozenset(),
    ) -> None:
        self.root = root.resolve()
        if not self.root.is_dir():
            raise ValueError(f"root is not a directory: {root}")
        self.allowed_group_ids = allowed_group_ids
        self.allowed_user_ids = allowed_user_ids

    def list_document_ids(self) -> list[str]:
        ids = []
        for path in self.root.rglob("*"):
            if not path.is_file() or path.suffix not in CONTENT_TYPES:
                continue
            relative = path.relative_to(self.root)
            if _is_hidden(relative):
                continue
            ids.append(relative.as_posix())
        return sorted(ids)

    def fetch(self, external_id: str) -> RawDocument:
        path = (self.root / external_id).resolve()
        # Path traversal guard: "../../etc/passwd" jaisi ID root ke bahar nahi jani chahiye
        if not path.is_relative_to(self.root) or _is_hidden(path.relative_to(self.root)):
            raise ValueError(f"document not found in source: {external_id}")
        if not path.is_file() or path.suffix not in CONTENT_TYPES:
            raise ValueError(f"unsupported or missing file: {external_id}")
        return RawDocument(
            external_id=external_id,
            title=path.stem,
            content=path.read_bytes(),
            content_type=CONTENT_TYPES[path.suffix],
            allowed_group_ids=self.allowed_group_ids,
            allowed_user_ids=self.allowed_user_ids,
        )


def _is_hidden(relative: Path) -> bool:
    """Dotfiles aur dot-folders (jaise .git) skip karo, unka content index nahi hona chahiye."""
    return any(part.startswith(".") for part in relative.parts)