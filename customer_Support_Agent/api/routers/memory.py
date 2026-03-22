from __future__ import annotations

from fastapi import FastAPI, APIRouter, Depends, HTTPException
from customer_Support_Agent.api.dependencies import get_copilot_or_503, get_customer_repository

from customer_Support_Agent.repositories.sqlite import CustomerRepository
from customer_Support_Agent.schemas.api import CustomerMemoriesResponse, CustomerMemorySearchResponse
from customer_Support_Agent.services.copilot_service import SupportCopilot

router = APIRouter()

#it will do sematic memory search on all memory
@router.get("api/customers/{customer_id}/memories", response_model=CustomerMemoriesResponse)
def customer_memory_route(
    customer_id: int,
    customers_repo: CustomerRepository = Depends(CustomerRepository),
    copilot: SupportCopilot = Depends(get_copilot_or_503),
) -> dict:
    customer = customers_repo.get_by_id(customer_id)
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
    
    
#it will do sematic memory search on particular customer based on query
@router.get("/api/customers/{customer_id}/memory-search", response_model=CustomerMemorySearchResponse)
def customer_memory_search_route(
    customer_id: int,
    query: str,
    limit : int = 10,
    customers_repo: CustomerRepository = Depends(get_customer_repository),
    copilot: SupportCopilot = Depends(get_copilot_or_503),
) -> dict:
    customer = customers_repo.get_by_id(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query is required")
    
    try:
        results = copilot.search_customer_memories(
            customer_email=customer["email"],
            customer_company=customer.get("company"),
            query=query,
            limit = max(1, min(limit, 25)),
            )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to get memories for {exc}") from exc

    return {
        "customer_id": customer_id,
        "customer_email": customer["email"],
        "query": query,
        "results": results
    }
        
        
        
    