from pact import Consumer, Provider  # type: ignore
import requests  # type: ignore


def test_health_contract(tmp_path):
    pact = Consumer("health-client").has_pact_with(
        Provider("stt-service"), pact_dir=str(tmp_path), port=12345
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
    assert (tmp_path / "health-client-stt-service.json").exists()
