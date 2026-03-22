"""Router registration."""

from customer_Support_Agent.api.routers.drafts import router as drafts_router
from customer_Support_Agent.api.routers.health import router as health_router
from customer_Support_Agent.api.routers.tickets import router as tickets_router
from customer_Support_Agent.api.routers.knowledge import router as knowledge_router
from customer_Support_Agent.api.routers.memory import router as memory_router

_all_ = ["drafts_router",
        "health_router",
        "tickets_router",
        "knowledge_router",
        "memory_router",
    ]   