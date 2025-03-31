from fastapi import FastAPI
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from auth.users import auth_backend, fastapi_users
from auth.schemas import UserCreate, UserRead
from auth.db import create_db_and_tables
from redis import asyncio as aioredis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from links.links import router as links_router
from links.tasks import delete_expired_links, delete_unused_links
import asyncio
import uvicorn


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    
    await create_db_and_tables()
    task = asyncio.create_task(delete_expired_links())
    task2 = asyncio.create_task(delete_unused_links())
    
    yield
    
    task.cancel()
    task2.cancel()
    try:
        await task
        await task2
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan)

app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(links_router)

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, host="0.0.0.0", log_level="info")