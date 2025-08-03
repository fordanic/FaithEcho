import pytest
from pathlib import Path


def pytest_collection_modifyitems(config, items):
    e2e_dir = Path(__file__).parent
    for item in items:
        if e2e_dir in Path(item.fspath).parents:
            item.add_marker(
                pytest.mark.skip(reason="requires running language services")
            )
