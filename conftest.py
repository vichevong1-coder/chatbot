def pytest_addoption(parser):
    parser.addoption(
        "--dry-run",
        action="store_true",
        default=False,
        help="Replay expected responses instead of calling the live orchestrator.",
    )


import pytest


@pytest.fixture(scope="session")
def dry_run(request):
    return request.config.getoption("--dry-run")
