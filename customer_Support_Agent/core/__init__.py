"""core configuration and utilities for the customer support agent project"""

from pydantic_settings import __all__

from customer_Support_Agent.core.settings import Settings, ensure_directories, get_settings

__all__ = ["Settings", "ensure_directories", "get_settings"]