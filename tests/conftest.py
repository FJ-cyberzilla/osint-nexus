import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from osint_nexus.api.deps import get_db

# Import your FastAPI app and get_db dependency
from osint_nexus.api.main import app


# -----------------------------------------------------------------------------
# 1. Environment Detection (Docker availability)
# -----------------------------------------------------------------------------
def has_docker() -> bool:
    """Check if Docker is available."""
    try:
        import docker

        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


# -----------------------------------------------------------------------------
# 2. Worker Identification
# -----------------------------------------------------------------------------
@pytest.fixture(scope="session")
def worker_id(request) -> str:
    """Returns 'master' or 'gwX' for xdist."""
    config = getattr(request, "config", None)
    if config is not None and hasattr(config, "workerinput"):
        return config.workerinput["workerid"]
    return "master"


# -----------------------------------------------------------------------------
# 3. Database URL Selection (Postgres or SQLite fallback)
# -----------------------------------------------------------------------------
@pytest.fixture(scope="session")
def worker_db_url(worker_id, tmp_path_factory) -> str:
    """Provides an isolated database URL for the worker."""
    if has_docker():
        # Implementation for PostgreSQL via Testcontainers
        pass

    # SQLite is utilized for isolated test runs in resource-constrained
    # environments, ensuring consistent test structure across deployments.
    db_dir = tmp_path_factory.getbasetemp() / "db"
    db_dir.mkdir(exist_ok=True)
    db_path = db_dir / f"test_{worker_id}.db"
    return f"sqlite+aiosqlite:///{db_path}"


# -----------------------------------------------------------------------------
# 4. Async Engine & Transaction Rollback
# -----------------------------------------------------------------------------
@pytest_asyncio.fixture(scope="session")
async def async_engine(worker_db_url):
    """Creates an AsyncEngine."""
    engine = create_async_engine(worker_db_url, echo=False)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(async_engine):
    """Savepoint Transaction Rollback Pattern."""
    async with async_engine.connect() as connection:
        transaction = await connection.begin()

        # We need a session factory that handles SQLite properly
        from sqlalchemy.orm import sessionmaker

        async_session = sessionmaker(
            bind=connection,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        session = async_session()

        await connection.begin_nested()

        @event.listens_for(session.sync_session, "after_transaction_end")
        def restart_savepoint(sync_session, trans):
            if trans.nested and not trans._parent.nested:
                sync_session.begin_nested()

        yield session

        await session.close()
        await transaction.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncClient:
    """FastAPI AsyncClient overriding get_db dependency."""

    async def _override_get_db():
        # In a real app, you'd yield the session here
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as async_client:
        yield async_client

    app.dependency_overrides.clear()
