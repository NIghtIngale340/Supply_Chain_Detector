import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture(scope="session", autouse=True)
def _test_env() -> None:
    os.environ.setdefault("LLM_PROVIDER", "stub")


@pytest.fixture()
def api_client() -> Iterator[TestClient]:
    with TestClient(app) as client:
        yield client
