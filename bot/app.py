"""
FastAPI entrypoint — Phase E (contest-ready).

Run:
    uvicorn bot.app:app --host 0.0.0.0 --port 8080
"""

from __future__ import annotations

import time
from typing import Union

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from bot import config
from bot.composer.composer import compose
from bot.demo import catalog, resolve_bundle
from bot.models import (
    ContextAcceptResponse,
    ContextPushRequest,
    ContextRejectResponse,
    HealthzResponse,
    MetadataResponse,
    ReplyRequest,
    TeardownResponse,
    TickRequest,
    TickResponse,
)
from bot.orchestrator.reply import handle_reply
from bot.orchestrator.tick import handle_tick
from bot.store.context_store import ContextStore
from bot.store.conversation_store import ConversationStore

START = time.time()
contexts = ContextStore()
conversations = ConversationStore()

app = FastAPI(
    title="magicpin Merchant AI Assistant",
    version=config.BOT_VERSION,
    description="Contest bot: adaptive 4-context compose + multi-turn reply",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DemoComposeRequest(BaseModel):
    category_slug: str
    merchant_id: str
    trigger_id: str
    customer_id: str | None = None


class DemoComposeResponse(BaseModel):
    body: str
    cta: str
    send_as: str
    suppression_key: str
    rationale: str
    template_name: str | None = None
    template_params: list = Field(default_factory=list)
    contexts: dict


@app.get("/")
async def root() -> dict:
    """Browser-friendly landing so the public URL is not a bare 404."""
    return {
        "service": "magicpin Merchant AI Assistant (Vera)",
        "status": "ok",
        "version": config.BOT_VERSION,
        "endpoints": {
            "healthz": "/v1/healthz",
            "metadata": "/v1/metadata",
            "context": "POST /v1/context",
            "tick": "POST /v1/tick",
            "reply": "POST /v1/reply",
            "teardown": "POST /v1/teardown",
            "demo_catalog": "GET /v1/demo/catalog",
            "demo_compose": "POST /v1/demo/compose",
        },
    }


@app.get("/v1/demo/catalog")
async def demo_catalog() -> dict:
    """Scenarios + seed pickers for the interactive Vera Lab frontend."""
    return catalog()


@app.post("/v1/demo/compose", response_model=DemoComposeResponse)
async def demo_compose(body: DemoComposeRequest) -> DemoComposeResponse:
    """
    Live compose(category, merchant, trigger, customer?) for the lab UI.
    Uses the same composer as the contest bot / offline bot.py.
    """
    try:
        bundle = resolve_bundle(
            category_slug=body.category_slug,
            merchant_id=body.merchant_id,
            trigger_id=body.trigger_id,
            customer_id=body.customer_id,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    result = compose(
        bundle["category"],
        bundle["merchant"],
        bundle["trigger"],
        bundle["customer"],
        force_english=True,
    )
    return DemoComposeResponse(
        body=result["body"],
        cta=result["cta"],
        send_as=result["send_as"],
        suppression_key=result["suppression_key"],
        rationale=result["rationale"],
        template_name=result.get("template_name"),
        template_params=list(result.get("template_params") or []),
        contexts={
            "category_slug": body.category_slug,
            "merchant_id": body.merchant_id,
            "trigger_id": body.trigger_id,
            "customer_id": body.customer_id,
            "trigger_kind": bundle["trigger"].get("kind"),
            "trigger_urgency": bundle["trigger"].get("urgency"),
            "merchant_name": (bundle["merchant"].get("identity") or {}).get("name"),
            "owner_first_name": (bundle["merchant"].get("identity") or {}).get(
                "owner_first_name"
            ),
            "locality": (bundle["merchant"].get("identity") or {}).get("locality"),
            "customer_name": (
                (bundle["customer"].get("identity") or {}).get("name")
                if bundle["customer"]
                else None
            ),
        },
    )


@app.get("/v1/healthz", response_model=HealthzResponse)
async def healthz() -> HealthzResponse:
    return HealthzResponse(
        status="ok",
        uptime_seconds=int(time.time() - START),
        contexts_loaded=contexts.counts(),
    )


@app.get("/v1/metadata", response_model=MetadataResponse)
async def metadata() -> MetadataResponse:
    model_label = config.LLM_MODEL or f"{config.LLM_PROVIDER}-default"
    if not config.LLM_API_KEY:
        model_label = "stub-no-llm"
    return MetadataResponse(
        team_name=config.TEAM_NAME,
        team_members=config.TEAM_MEMBERS,
        model=model_label,
        approach=config.APPROACH,
        contact_email=config.CONTACT_EMAIL,
        version=config.BOT_VERSION,
        submitted_at=config.SUBMITTED_AT,
    )


@app.post(
    "/v1/context",
    response_model=None,
    responses={
        200: {"model": ContextAcceptResponse},
        400: {"model": ContextRejectResponse},
        409: {"model": ContextRejectResponse},
    },
)
async def push_context(body: ContextPushRequest) -> Union[ContextAcceptResponse, JSONResponse]:
    if body.scope not in config.VALID_SCOPES:
        return JSONResponse(
            status_code=400,
            content={
                "accepted": False,
                "reason": "invalid_scope",
                "details": f"scope must be one of {sorted(config.VALID_SCOPES)}",
            },
        )

    accepted, current, stored_at = contexts.put(
        scope=body.scope,
        context_id=body.context_id,
        version=body.version,
        payload=body.payload,
    )
    if not accepted:
        return JSONResponse(
            status_code=409,
            content={
                "accepted": False,
                "reason": "stale_version",
                "current_version": current,
            },
        )

    return ContextAcceptResponse(
        accepted=True,
        ack_id=f"ack_{body.context_id}_v{body.version}",
        stored_at=stored_at or "",
    )


@app.post("/v1/tick", response_model=TickResponse)
async def tick(body: TickRequest) -> TickResponse:
    actions = handle_tick(
        now=body.now,
        available_triggers=body.available_triggers,
        contexts=contexts,
        conversations=conversations,
    )
    return TickResponse(actions=actions)


@app.post("/v1/reply")
async def reply(body: ReplyRequest):
    return handle_reply(
        conversation_id=body.conversation_id,
        merchant_id=body.merchant_id,
        customer_id=body.customer_id,
        from_role=body.from_role,
        message=body.message,
        received_at=body.received_at,
        turn_number=body.turn_number,
        conversations=conversations,
        contexts=contexts,
    )


@app.post("/v1/teardown", response_model=TeardownResponse)
async def teardown() -> TeardownResponse:
    n_ctx = contexts.clear()
    n_conv = conversations.clear()
    return TeardownResponse(
        wiped=True,
        cleared_contexts=n_ctx,
        cleared_conversations=n_conv,
    )
