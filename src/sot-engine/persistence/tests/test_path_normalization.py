from pathlib import Path

from shared.path_utils import normalize_file_path
from persistence.adapters.lizard_adapter import LizardAdapter
from persistence.adapters.scc_adapter import SccAdapter


def test_adapter_normalizes_private_tmp_prefix() -> None:
    repo_root = Path("/private/tmp/keepass2android")
    raw_path = "tmp/keepass2android/.github/PULL_REQUEST_TEMPLATE.md"

    scc_adapter = SccAdapter(object(), object(), object(), repo_root)
    lizard_adapter = LizardAdapter(object(), object(), object(), repo_root)

    assert (
        scc_adapter._normalize_path(raw_path)
        == ".github/PULL_REQUEST_TEMPLATE.md"
    )
    assert (
        lizard_adapter._normalize_path(raw_path)
        == ".github/PULL_REQUEST_TEMPLATE.md"
    )


def test_adapter_preserves_dot_directories() -> None:
    repo_root = Path("/tmp/keepass2android")
    raw_path = ".github/PULL_REQUEST_TEMPLATE.md"
    scc_adapter = SccAdapter(object(), object(), object(), repo_root)
    lizard_adapter = LizardAdapter(object(), object(), object(), repo_root)

    assert scc_adapter._normalize_path(raw_path) == ".github/PULL_REQUEST_TEMPLATE.md"
    assert lizard_adapter._normalize_path(raw_path) == ".github/PULL_REQUEST_TEMPLATE.md"
    assert normalize_file_path(raw_path, repo_root) == ".github/PULL_REQUEST_TEMPLATE.md"
