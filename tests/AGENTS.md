# AGENTS.md – Testing Conventions & Expectations

> **Audience:** Autonomous coding agents (and humans!) contributing tests to this service
> **Goal:** Ensure every test is placed in the right spot, named predictably, and written to be **fast, deterministic, and readable**.

---

## How to Run Tests

The recommended way to run tests is using the `Makefile` targets:

*   **Run all tests (with coverage):**
    ```bash
    make tests
    ```
*   **Run unit tests only:**
    ```bash
    make unit-tests
    ```
*   **Run integration tests only:**
    ```bash
    make integration-tests
    ```

You can also invoke `pytest` directly for more control:

*   **Run tests in parallel:**
    ```bash
    poetry run pytest -n auto
    ```
*   **Run a specific suite by marker:**
    ```bash
    poetry run pytest -m integration
    ```

---

## Directory Layout (📁 `tests/`)

```
tests/
├── unit/          # fine‑grained, isolated tests (mock all I/O)
│   └── test_*.py
├── integration/   # real deps: DBs, queues, external services, etc.
│   └── test_*.py
├── contracts/     # API/consumer‑driven contract checks
│   └── test_*.py
├── e2e/           # black‑box flows against running containers
│   └── test_*.py
├── smoke/         # ultra‑quick “does it start?” probes
│   └── test_*.py
├── docker/        # Dockerfile and image‑level assertions
│   └── test_*.py
├── conftest.py    # **shared fixtures only** (no tests here)
└── data/          # Static test data (e.g., JSON payloads, mock API responses).
                   # Load via a fixture or `pathlib`.
```

---

## File & Test Naming

* **Files:** `test_<feature>.py`
  e.g., `test_user_auth.py`, `test_docker_labels.py`
* **Functions / methods:** `test_<behavior>_<expected>()`.
  Descriptive > terse: `test_login_returns_401_for_bad_creds` beats `test_bad_login`.

---

## Fixtures — `tests/conftest.py`

1. **Scope matters**

   * Use `@pytest.fixture(scope="function")` by default (isolated).
   * Broader scopes (`session`, `module`) allowed only for expensive setup (e.g., one Postgres container for all integration tests).
2. **No hidden side‑effects**

   * Every fixture cleans up after itself (context managers or `yield` style).
   * Data created in one test **must not** leak to another.

```python
@pytest.fixture
def user(db_session):
    """Create and return a sample user."""
    u = models.User(email="test@example.org")
    db_session.add(u)
    db_session.commit()
    return u
```

---

## Writing Tests: the **Arrange → Act → Assert** pattern

```python
def test_calculate_discount_handles_rounding():
    # Arrange
    price = Decimal("19.99")
    discount = Decimal("0.25")

    # Act
    result = calculate_discount(price, discount)

    # Assert
    assert result == Decimal("14.99")
```

* Keep each stage visually distinct (blank lines or comments).
* Extract repeated setup into fixtures to avoid duplication.

---

## Quality Rules

| Rule                             | Why it matters                                                                   |
| -------------------------------- | -------------------------------------------------------------------------------- |
| **Fast** (<100 ms per unit test) | Keeps CI feedback tight.                                                         |
| **Deterministic**                | No date/time drift (`freezegun`), no network randomness, no reliance on order.   |
| **Isolated**                     | Failing test pinpoints one root cause; enables parallel runs (`pytest -n auto`). |
| **Explicit**                     | Assertions state *why* they fail (`assert x == y, "price mismatch"`).            |
| **Minimal mocks**                | Mock external boundaries—not the code under test.                                |
| **No sleeps**                    | Use polling with a timeout if you *must* wait.                                   |

---

## Category‑Specific Guidance

* **Unit tests (`tests/unit/`)**

  * Mock ALL I/O: databases, HTTP, file system, environment.
  * Target a single function/class.

* **Integration tests (`tests/integration/`)**

  * Spin up real services via Docker Compose, Testcontainers, or `pytest-docker`.
  * Mark with `@pytest.mark.integration`.

* **Contract tests (`tests/contracts/`)**

  * Validate schemas (OpenAPI, Protobuf).
  * Fail fast if an endpoint contract breaks.

* **End‑to‑End tests (`tests/e2e/`)**

  * Build the Docker image first, then run workflows against live endpoints.
  * Use environment vars to point at the running container(s).

* **Smoke tests (`tests/smoke/`)**

  * One‑liner health checks (`/healthz` returns 200, version string is non‑empty).
  * Executed right after the image is built—before heavier suites.

* **Docker tests (`tests/docker/`)**

  * Use `container‑structure‑test`, `dockle`, or plain Python + Docker SDK.
  * Check for: non‑root user, required labels, exposed ports, slim image size.

---

## Markers & Selectors

* Register custom markers in `pytest.ini`:

  ```ini
  [pytest]
  markers =
      integration: slow, uses real services
      e2e: full‑stack, slowest
      smoke: quick health probes
  ```
* Example: run all fast suites in CI:
  `pytest -m "not (integration or e2e)"`

---

## Test Dependencies

All test-related dependencies (e.g., `pytest`, `pytest-mock`, `freezegun`) MUST be defined in `pyproject.toml` under the `[tool.poetry.group.dev.dependencies]` section. This ensures a reproducible test environment.

```toml
# pyproject.toml
[tool.poetry.group.dev.dependencies]
pytest = "^8.4.1"
pytest-cov = "^6.2.1"
freezegun = "^1.5.1"
# ... etc.
```

---

## TL;DR Checklist

* [ ] File lives in the correct subfolder.
* [ ] Named `test_<something>.py`; functions start with `test_`.
* [ ] Uses AAA pattern and clear fixture names.
* [ ] Runs in <1 s locally; no random failures.
* [ ] Leaves the system exactly as it found it.

*Happy testing!* 🎉
