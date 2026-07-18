from __future__ import annotations

from fastapi import FastAPI, Header


app = FastAPI(title="FastAPI Easy Auth")


@app.get("/auth/probe")
async def auth_probe(
    x_ms_client_principal: str | None = Header(default=None),
) -> dict[str, object]:
    return {
        "layer": "fastapi",
        "platformPrincipalHeaderPresent": bool(x_ms_client_principal),
    }
