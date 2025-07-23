from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.integration
def test_devcontainer_exists() -> None:
    # Arrange
    devcontainer_file = REPO_ROOT / ".devcontainer" / "devcontainer.json"

    # Act & Assert
    assert devcontainer_file.is_file(), "devcontainer.json should exist"


@pytest.mark.integration
def test_dev_proxy_script() -> None:
    # Arrange
    script = REPO_ROOT / "scripts" / "dev-proxy.sh"

    # Act & Assert
    assert script.is_file(), "dev-proxy.sh should exist"
    assert script.stat().st_mode & 0o111, "dev-proxy.sh should be executable"


@pytest.mark.integration
def test_docker_compose_exists() -> None:
    # Arrange
    docker_compose_file = REPO_ROOT / "docker-compose.yml"

    # Act & Assert
    assert docker_compose_file.is_file(), "docker-compose.yml should exist"
