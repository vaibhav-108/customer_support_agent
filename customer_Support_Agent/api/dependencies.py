from __future__ import annotations
from typing import Any
from functools import lru_cache

from fastapi import Depends, HTTPException, status

from customer_Support_Agent.core.settings import get_settings, Settings
from customer_Support_Agent.repositories.sqlite import CustomerRepository
from customer_Support_Agent.repositories.sqlite import TicketRepository
from customer_Support_Agent.repositories.sqlite import DraftRepository
from customer_Support_Agent.services.copilot_service import SupportCopilot
from customer_Support_Agent.services.draft_service import DraftService
from customer_Support_Agent.services.knowledge_service import KnowledgeService

@lru_cache
def get_copilot() -> SupportCopilot:
    return SupportCopilot(settings=get_settings())

def get_copilot_or_503() -> SupportCopilot:
    try:
        return get_copilot()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Copliot Service Unavailable: {e}")
    
def get_settings_dep() -> Settings:
    return get_settings

def get_customer_repository() -> CustomerRepository:
    return CustomerRepository

def get_ticket_repository() -> TicketRepository:
    return TicketRepository

def get_draft_repository() -> DraftRepository:
    return DraftRepository

def get_draft_service() -> DraftService:
    return DraftService

def get_knowledge_service(settings: Settings= get_settings()) -> KnowledgeService:
    return KnowledgeService(settings=settings)

