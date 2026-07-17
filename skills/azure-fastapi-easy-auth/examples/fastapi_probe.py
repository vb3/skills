"""DB-free FastAPI ingress proof for an app protected by Easy Auth."""

from __future__ import annotations

from fastapi import APIRouter, Header


router = APIRouter()


@router.get("/auth/probe")
async def auth_probe(
    x_ms_client_principal: str | None = Header(default=None),
) -> dict[str, object]:
    return {
        "layer": "fastapi",
        "platformPrincipalHeaderPresent": bool(x_ms_client_principal),
    }
