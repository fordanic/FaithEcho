from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.integration
def test_devcontainer_exists() -> None:
    assert (REPO_ROOT / ".devcontainer" / "devcontainer.json").is_file()


@pytest.mark.integration
def test_dev_proxy_script() -> None:
    script = REPO_ROOT / "scripts" / "dev-proxy.sh"
    assert script.is_file() and script.stat().st_mode & 0o111


@pytest.mark.integration
def test_docker_compose_exists() -> None:
    assert (REPO_ROOT / "docker-compose.yml").is_file()
