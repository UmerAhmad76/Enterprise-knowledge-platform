"""Connector tests: sirf supported aur visible files list hon, aur path traversal block ho."""
import os

import pytest

from core.ingestion.connectors.local_fs import LocalFileConnector


@pytest.fixture
def root(tmp_path):
    (tmp_path / "policies").mkdir()
    (tmp_path / "policies" / "leave.md").write_text("# Leave\n\nText", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("hi", encoding="utf-8")
    (tmp_path / "image.png").write_bytes(b"\x89PNG")
    (tmp_path / ".secret.md").write_text("hidden", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config.md").write_text("x", encoding="utf-8")
    return tmp_path


def test_lists_only_supported_visible_files(root):
    assert LocalFileConnector(root).list_document_ids() == ["notes.txt", "policies/leave.md"]


def test_fetch_returns_raw_document(root):
    doc = LocalFileConnector(root).fetch("policies/leave.md")
    assert doc.title == "leave"
    assert doc.content_type == "text/markdown"


def test_path_traversal_and_hidden_files_are_blocked(root, tmp_path_factory):
    outside = tmp_path_factory.mktemp("outside") / "secret.md"
    outside.write_text("top secret", encoding="utf-8")
    connector = LocalFileConnector(root)

    with pytest.raises(ValueError):
        connector.fetch(os.path.relpath(outside, root))
    with pytest.raises(ValueError):
        connector.fetch(".secret.md")