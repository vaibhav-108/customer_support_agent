from __future__ import annotations
from typing import Any
from fastapi import FastAPI
from contextlib import asynccontextmanager

from customer_Support_Agent.api.routers import (
    drafts_router,
    health_router,
    tickets_router,
    customer_router
)

from customer_Support_Agent.core.settings import Settings,ensure_directories, get_settings
from customer_Support_Agent.repositories.sqlite import init_db

def create_app(settings: Settings | None=None) -> FastAPI:
    resolve_setting = settings or get_settings()
    
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> Any:
        ensure_directories(resolve_setting)
        init_db()
        yield

    app = FastAPI(title=resolve_setting.app_name,lifespan=lifespan)
    
    app.include_router(health_router)
    app.include_router(drafts_router)
    app.include_router(tickets_router)
    app.include_router(customer_router)

    return app
    