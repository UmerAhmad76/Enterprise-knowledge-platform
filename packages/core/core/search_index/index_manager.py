"""Creates versioned OpenSearch indexes and switches the live alias without downtime."""
import re

from opensearchpy import OpenSearch

from core.search_index.mappings.chunks_v1 import chunks_index_body

ACTIVE_ALIAS = "chunks_active"  # queries hamesha is alias se hon gi, index ke naam se nahi


def build_index_name(model_name: str, model_version: str) -> str:
    """OpenSearch index names lowercase hone chahiye, aur special characters allowed nahi hen."""
    safe = re.sub(r"[^a-z0-9_-]", "-", f"{model_name}-{model_version}".lower())
    return f"chunks-{safe}"


def create_versioned_index(client: OpenSearch, index_name: str, dimension: int) -> None:
    """Index sirf tab banata hai jab woh pehle se na ho, taake dobara chalana safe ho (idempotent)."""
    if not client.indices.exists(index=index_name):
        client.indices.create(index=index_name, body=chunks_index_body(dimension))


def switch_active_alias(client: OpenSearch, new_index: str) -> None:
    """Purana alias hatata hai aur naya add karta hai, ek hi atomic request mein."""
    actions: list[dict] = []
    if client.indices.exists_alias(name=ACTIVE_ALIAS):
        for old_index in client.indices.get_alias(name=ACTIVE_ALIAS):
            actions.append({"remove": {"index": old_index, "alias": ACTIVE_ALIAS}})
    actions.append({"add": {"index": new_index, "alias": ACTIVE_ALIAS}})
    client.indices.update_aliases(body={"actions": actions})