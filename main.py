from __future__ import annotations
import uvicorn

from customer_Support_Agent.api.app_factory import create_app
from customer_Support_Agent.core.settings import Settings, get_settings

app= create_app()

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run("main:app", host=settings.api_host, port=settings.api_port, reload=False)
