from __future__ import annotations
from typing import Any, Callable

import json
import os
import logging

from customer_Support_Agent.repositories.sqlite import CustomerRepository, DraftRepository, TicketRepository
from customer_Support_Agent.services.copilot_service import SupportCopilot


class DraftService:
    
    def serialize_draft(self, draft: dict[str,Any]) -> dict[str,Any]:
        context_raw = draft.get("context_used")
        context_data: dict[str,Any] | None=None
        
        if context_raw:
            try:
                context_data = json.loads(context_raw)
            except json.JSONDecodeError:
                context_data = {"raw": context_raw}
                
        return {"id": draft["id"],
                "ticket_id": draft["ticket_id"],
                "content": draft["content"],
                "context_used": context_data,
                "status": draft["status"],
                "created_at": draft["created_at"],
                }

    
    def serialize_ticket(self, ticket: dict[str,Any]) -> dict:
        return {
            "id": ticket["id"],
            "customer_id": ticket["customer_id"],
            "customer_email": ticket["customer_email"],
            "customer_name": ticket["customer_name"],
            "customer_company": ticket["customer_company"],
            "subject": ticket["subject"],
            "description": ticket["description"],
            "status": ticket["status"],
            "priority": ticket["priority"],
            "created_at": ticket["created_at"],
            "updated_at": ticket["updated_at"],   
        }
        
        
    def parse_context_used(self,raw:Any) -> dict[str,Any]:
        if isinstance(raw,dict):
            return raw
        if isinstance(raw,str):
            try:
                parsed= json.loads(raw)
                return parsed if isinstance(parsed,dict) else {"raw": raw}
            except json.JSONDecodeError:
                return {"raw": raw}
        return {}
        
        
    def generate_and_store_background(
        self,
        ticket_id: int,
        tickets_repo: TicketRepository,
        customer_repository: CustomerRepository,
        draft_repository: DraftRepository,
        copilot_factory: Callable[[], SupportCopilot],
        logger: logging.Logger,
    ) -> dict[str, Any] | None:
        ticket = tickets_repo.get_by_id(ticket_id)
        if not ticket:
            return None

        customer = customer_repository.get_by_id(ticket["customer_id"])
        if not customer:
            return None

        try:
            copilot = copilot_factory()
            result = copilot.generate_draft(ticket=ticket, customer=customer)
            draft_text, context_used = self._normalize_draft_result(result)
            return draft_repository.create(
                ticket_id=ticket_id,
                content=draft_text,
                context_used=json.dumps(context_used),
                status="pending",
            )
        except Exception as exc:
            logger.exception("Background draft generation failed for ticket_id=%s", ticket_id)
            return draft_repository.create(
                ticket_id=ticket_id,
                content=(
                    "Automatic draft generation failed. Configure AI keys and trigger "
                    "manual draft generation."
                ),
                context_used=json.dumps(self._failed_context(str(exc))),
                status="failed",
            )
    

    def generate_and_store_manual(
        self,
        ticket_id: int,
        ticket: dict[str, Any],
        customer: dict[str, Any],
        drafts_repo: DraftRepository,
        copilot: SupportCopilot,
        ) -> dict[str, Any]:
        result = copilot.generate_draft(ticket=ticket, customer=customer)
        draft_text, context_used = self._normalize_draft_result(result)
        return drafts_repo.create(
            ticket_id=ticket_id,
            content=draft_text,
            context_used=json.dumps(context_used),
            status="pending",
        )
    

    def _normalize_draft_result(self, result: dict[str,Any]) -> dict[str,Any]:
        draft_text = str(result.get("draft") or "").strip()
        context = result.get("context_used") or {}
        
        if not isinstance(context, dict):
            context = {"raw": context}
        
        if not draft_text:
            draft_text ={
                "Thanks for your message. we are reviewing your issye and will share "
                "a concrete update shortly."
            }   
            context.setdefault("errors", []).append(
                "copilot returened empty draft content. API fallback text was used."
            )
            
        return draft_text, context
    
    @staticmethod
    def _failed_context(error_text:str)-> dict[str,Any]:
        return {
            "version": 2,
            "signals":{
                "memory_hit_count":0,
                "knowledge_hit_count":0,
                "tool_call_count":0,
                "tool_error_count":0,
                "knowledge_source":[]
            },
            "highlights":{
                "memory":[],
                "knowledge":[],
                "tools":[]
            },
            "memory_hits":[],
            "knowledge_hits":[],
            "tool_calls":[],
            "errors":[error_text]
            }
        