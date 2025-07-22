from pact import Consumer, Provider  # type: ignore
import pytest
import requests  # type: ignore


@pytest.mark.parametrize(
    "service_name",
    [
        "stt-service",
        "translate-service",
        "tts-service",
    ],
)
def test_health_contract(tmp_path, service_name: str) -> None:
    pact = Consumer("health-client").has_pact_with(
        Provider(service_name), pact_dir=str(tmp_path), port=12345
    )
    pact.start_service()
    pact.given("service running").upon_receiving("health check").with_request(
        "get", "/health"
    ).will_respond_with(200, body={"status": "ok"})

    with pact:
        resp = requests.get(f"http://localhost:{pact.port}/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    pact.stop_service()
    assert (tmp_path / f"health-client-{service_name}.json").exists()
