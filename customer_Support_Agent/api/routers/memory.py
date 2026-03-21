from __future__ import annotations

from fastapi import FastAPI, APIRouter, Depends, HTTPException
from customer_Support_Agent.api.dependencies import get_copilot_or_503, get_customer_repository

from customer_Support_Agent.repositories.sqlite import CustomerRepository
from customer_Support_Agent.schemas.api import CustomerMemoriesResponse, CustomerMemorySearchResponse
from customer_Support_Agent.services.copilot_service import SupportCopilot

router = APIRouter()

@router.get("api/customers/{customer_id}/memories", response_model=CustomerMemoriesResponse)
def customer_memory_route(
    customer_id: int,
    customer_repo: CustomerRepository = Depends(CustomerRepository),
    copilot: SupportCopilot = Depends(get_copilot_or_503),
) -> dict:
    customer = customer_repo.get_by_id(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    try:
        memories = copilot.list_customer_memories(
            customer_email=customer["email"],
            customer_company=customer.get("company"),
            )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to get memories for {exc}") from exc

    return {
        "customer_id": customer_id,
        "customer_email": customer["email"],
        "memories": memories
    }