import asyncio

from fastapi import (
    APIRouter,
    Request,
    status
)
from fastapi.responses import JSONResponse

from app.infra.kafka import check_kafka
from app.infra.mongo import check_mongo
from app.infra.postgres import check_postgres, check_schema
from app.infra.redis import check_redis
from app.infra.temporal import check_temporal

CHECK_TIMEOUT_S = 2

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/live")
async def live():
    return {
        "status": "ok"
    }

async def _run_check(coro) -> dict:
    try:
        return await asyncio.wait_for(coro, timeout=CHECK_TIMEOUT_S)
    except TimeoutError:
        return {
            "status": "error",
            "error": f"timeout after {CHECK_TIMEOUT_S}s"
        }
    except Exception as exc:
        return {
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}"[:200]
        }

@router.get("/ready")
async def ready(request: Request):
    state = request.app.state
    names = ["postgres", "schema", "redis", "mongo", "temporal", "kafka"]

    results = await asyncio.gather(
        _run_check(check_postgres(state.pg_pool)),
        _run_check(check_schema(state.pg_pool, state.alembic_head)),
        _run_check(check_redis(state.redis)),
        _run_check(check_mongo(state.mongo)),
        _run_check(check_temporal(state.temporal)),
        _run_check(check_kafka(state.kafka_admin)),
    )
    components = dict(zip(names, results, strict=True))

    all_ok = all(c["status"] == "ok" for c in components.values())
    return JSONResponse(
        status_code=status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "ok" if all_ok else "error", "components": components},
    )
