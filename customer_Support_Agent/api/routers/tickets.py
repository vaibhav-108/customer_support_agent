from __future__ import annotations
from typing import Any

import logging

from fastapi import FastAPI, APIRouter, Depends, HTTPException, BackgroundTasks

from customer_Support_Agent.api.dependencies import (get_copilot,
                                                    get_ticket_repository,
                                                    get_draft_service,
                                                    get_draft_repository,
                                                    get_customer_repository,
                                                    get_copilot_or_503)

from customer_Support_Agent.repositories.sqlite import TicketRepository, DraftRepository, CustomerRepository
from customer_Support_Agent.schemas.api import TicketCreateRequest, TicketResponse, GenerateDraftResponse
from customer_Support_Agent.services.copilot_service import SupportCopilot
from customer_Support_Agent.services.draft_service import DraftService

logger = logging.getLogger(__name__)

router = APIRouter()

def _generate_and_store_draft_background(
    ticket_id: int,
    tickets_repo: TicketRepository,
    draft_service: DraftService,
    draft_repository: DraftRepository,
    customer_repository: CustomerRepository,
)-> dict[str, Any] | None:
    
    return draft_service.generate_and_store_background(
        ticket_id=ticket_id,
        tickets_repo=tickets_repo,
        draft_repository=draft_repository,
        customer_repository=customer_repository,
        copilot_factory=get_copilot,
        logger=logger,
    )
    
    
@router.post("/api/tickets", response_model=TicketResponse)
def create_ticket_route(
    payload: TicketCreateRequest,
    background_tasks: BackgroundTasks,
    tickets_repo: TicketRepository = Depends(get_ticket_repository),
    draft_service: DraftService = Depends(get_draft_service),
    draft_repository: DraftRepository = Depends(get_draft_repository),
    customer_repository: CustomerRepository = Depends(get_customer_repository),
    ) -> dict[str, Any]:
    
    customer = customer_repository.create_or_get(
        email=payload.customer_email,
        name=payload.customer_name,
        company=payload.customer_company
    )
    
    ticket = tickets_repo.create(
        customer_id=customer["id"],
        subject=payload.subject,
        description=payload.description,
        priority=payload.priority,
    
    )
    
    merged ={
        **ticket,
        "customer_email": customer["email"],
        "customer_name": customer.get("name"),
        "customer_company": customer.get("company"),
    }
    
    if payload.auto_generate:
        background_tasks.add_task(
            _generate_and_store_draft_background,
            ticket["id"],
            tickets_repo,
            draft_service,
            draft_repository,
            customer_repository)

    return draft_service.serialize_ticket(merged)

#will return all tickets
@router.get("/api/tickets", response_model=list[TicketResponse])
def list_tickets_route(
    tickets_repo: TicketRepository = Depends(get_ticket_repository),
    draft_service: DraftService = Depends(get_draft_service),
) -> list[dict[str, Any]]:
    return [draft_service.serialize_ticket(ticket) for ticket in tickets_repo.list()]


@router.get("/api/tickets/{ticket_id}", response_model=TicketResponse)
def get_ticket_route(
    ticket_id: int,
    tickets_repo: TicketRepository = Depends(get_ticket_repository),
    draft_service: DraftService = Depends(get_draft_service),
) -> dict[str, Any]:
    ticket = tickets_repo.get_by_id(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return draft_service.serialize_ticket(ticket)


@router.post("/api/tickets/{ticket_id}/generate-draft", response_model=GenerateDraftResponse)
def generate_draft_route(
    ticket_id: int,
    tickets_repo: TicketRepository = Depends(get_ticket_repository),
    customers_repo: CustomerRepository = Depends(get_customer_repository),
    drafts_repo: DraftRepository = Depends(get_draft_repository),
    draft_service: DraftService = Depends(get_draft_service),
    copilot: SupportCopilot = Depends(get_copilot_or_503),
) -> dict[str, Any]:
    ticket = tickets_repo.get_by_id(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    customer = customers_repo.get_by_id(ticket["customer_id"])
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    try:
        draft = draft_service.generate_and_store_manual(
            ticket_id=ticket_id,
            ticket=ticket,
            customer=customer,
            drafts_repo=drafts_repo,
            copilot=copilot,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate draft: {exc}") from exc

    return {
        "ticket_id": ticket_id,
        "draft": draft_service.serialize_draft(draft),
    }


