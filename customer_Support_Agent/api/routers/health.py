from __future__ import annotations

from fastapi import FastAPI, APIRouter, Depends, HTTPException

router = APIRouter()

#jsut to check our server is up and running
@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

