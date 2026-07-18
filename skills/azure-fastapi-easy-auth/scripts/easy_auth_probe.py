#!/usr/bin/env python3
"""Probe Easy Auth without printing or persisting bearer tokens."""

from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections.abc import Sequence
from typing import Any


DEFAULT_TIMEOUT_SECONDS = 20.0
DEFAULT_DEVICE_CODE_TIMEOUT_SECONDS = 600.0
MAX_RESPONSE_BYTES = 65_536
JWT_PATTERN = re.compile(
    r"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]+"
)
BEARER_PATTERN = re.compile(r"(?i)(Bearer\s+)[^\s,;]+")


def redact_text(value: str) -> str:
    redacted = JWT_PATTERN.sub("[REDACTED]", value)
    return BEARER_PATTERN.sub(r"\1[REDACTED]", redacted)


def _guid(value: str, name: str) -> str:
    try:
        return str(uuid.UUID(value))
    except ValueError as error:
        raise ValueError(f"{name} must be a UUID") from error


def _decode_segment(segment: str) -> bytes:
    padding = "=" * (-len(segment) % 4)
    try:
        return base64.urlsafe_b64decode(segment + padding)
    except (ValueError, TypeError) as error:
        raise ValueError("Token payload is not valid base64url") from error


def parse_jwt_claims(token: str) -> dict[str, object]:
    parts = token.split(".")
    if len(parts) != 3 or not all(parts):
        raise ValueError("Input is not a three-segment JWT")
    try:
        claims = json.loads(_decode_segment(parts[1]))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError("Token payload is not valid JSON") from error
    if not isinstance(claims, dict):
        raise ValueError("Token payload must be a JSON object")
    return claims


def summarize_claims(
    claims: dict[str, object],
    *,
    tenant_id: str,
    resource_app_id: str,
    expected_scope: str | None = None,
    expected_role: str | None = None,
    allowed_client_ids: Sequence[str] = (),
    additional_audiences: Sequence[str] = (),
    expected_issuer: str | None = None,
) -> dict[str, object]:
    tenant = _guid(tenant_id, "tenant_id")
    resource = _guid(resource_app_id, "resource_app_id")
    allowed_clients = {
        _guid(value, "allowed_client_id") for value in allowed_client_ids
    }
    version = claims.get("ver")
    version_text = version if isinstance(version, str) else None

    expected_audiences = {
        resource,
        f"api://{resource}",
        *additional_audiences,
    }
    audience = claims.get("aud")
    audience_matches = (
        isinstance(audience, str) and audience in expected_audiences
    )

    if expected_issuer is None:
        if version_text == "1.0":
            issuer = f"https://sts.windows.net/{tenant}/"
        else:
            issuer = f"https://login.microsoftonline.com/{tenant}/v2.0"
    else:
        issuer = expected_issuer.rstrip("/")
    actual_issuer = claims.get("iss")
    issuer_matches = (
        isinstance(actual_issuer, str)
        and actual_issuer.rstrip("/") == issuer.rstrip("/")
    )

    tenant_matches = claims.get("tid") == tenant
    delegated_scopes = {
        value
        for value in str(claims.get("scp") or "").split()
        if value
    }
    raw_roles = claims.get("roles")
    application_roles = (
        {str(value) for value in raw_roles}
        if isinstance(raw_roles, list)
        else set()
    )
    if delegated_scopes:
        token_kind = "delegated"
    elif application_roles:
        token_kind = "app-only"
    else:
        token_kind = "unknown"

    if expected_scope is not None:
        permission_matches = expected_scope in delegated_scopes
    elif expected_role is not None:
        permission_matches = expected_role in application_roles
    else:
        permission_matches = None

    client_claim = "azp" if version_text == "2.0" else "appid"
    client_id = claims.get(client_claim)
    client_matches = (
        client_id in allowed_clients if allowed_clients else None
    )
    auth_method_claim = "azpacr" if version_text == "2.0" else "appidacr"
    auth_method = {
        "0": "public-client",
        "1": "client-secret",
        "2": "certificate",
    }.get(str(claims.get(auth_method_claim)), "unknown")

    return {
        "tokenVersion": version_text,
        "tokenKind": token_kind,
        "audienceMatches": audience_matches,
        "issuerMatches": issuer_matches,
        "tenantMatches": tenant_matches,
        "delegatedScopesPresent": bool(delegated_scopes),
        "applicationRolesPresent": bool(application_roles),
        "permissionMatches": permission_matches,
        "clientClaim": client_claim,
        "clientApplicationMatches": client_matches,
        "clientAuthenticationMethod": auth_method,
        "claimsChallengeCapable": claims.get("xms_cc") == ["cp1"],
    }


def _run_az(command: list[str], timeout: float) -> Any:
    completed = subprocess.run(
        ["az", *command, "--output", "json"],
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError("Azure CLI returned invalid JSON") from error


def acquire_cli_token(
    *,
    tenant_id: str,
    scope: str,
    timeout: float,
) -> str:
    result = _run_az(
        [
            "account",
            "get-access-token",
            "--tenant",
            tenant_id,
            "--scope",
            scope,
        ],
        timeout,
    )
    token = result.get("accessToken") if isinstance(result, dict) else None
    if not isinstance(token, str) or not token:
        raise RuntimeError("Azure CLI response did not contain an access token")
    return token


def acquire_device_code_token(
    *,
    tenant_id: str,
    client_id: str,
    scope: str,
    authority_host: str,
    timeout: float,
) -> str:
    try:
        import msal
    except ImportError as error:
        raise RuntimeError(
            "MSAL is required for device-code acquisition; install package msal"
        ) from error

    client = msal.PublicClientApplication(
        client_id,
        authority=f"{authority_host.rstrip('/')}/{tenant_id}",
    )
    flow = client.initiate_device_flow(scopes=[scope])
    if not isinstance(flow, dict) or "user_code" not in flow:
        raise RuntimeError("Microsoft Entra did not start a device-code flow")
    message = flow.get("message")
    if isinstance(message, str) and message:
        print(message, file=sys.stderr, flush=True)
    flow["expires_at"] = min(
        float(flow.get("expires_at", time.time() + timeout)),
        time.time() + timeout,
    )
    result = client.acquire_token_by_device_flow(flow)
    token = result.get("access_token") if isinstance(result, dict) else None
    if not isinstance(token, str) or not token:
        error_code = (
            result.get("error", "unknown_error")
            if isinstance(result, dict)
            else "invalid_response"
        )
        raise RuntimeError(f"Device-code token acquisition failed: {error_code}")
    return token


def acquire_wrong_audience_token(
    *,
    tenant_id: str,
    timeout: float,
) -> str:
    result = _run_az(
        [
            "account",
            "get-access-token",
            "--tenant",
            tenant_id,
            "--resource",
            "https://management.azure.com/",
        ],
        timeout,
    )
    token = result.get("accessToken") if isinstance(result, dict) else None
    if not isinstance(token, str) or not token:
        raise RuntimeError("Azure CLI response did not contain a control token")
    return token


def normalize_endpoint(value: str) -> str:
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("endpoint must be an absolute HTTP or HTTPS URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError(
            "endpoint must not contain credentials, a query, or a fragment"
        )
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", "")
    )


def probe_url(
    url: str,
    *,
    token: str | None,
    timeout: float,
) -> dict[str, object]:
    headers = {"Accept": "application/json"}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(MAX_RESPONSE_BYTES)
            status = response.status
            response_headers = response.headers
    except urllib.error.HTTPError as error:
        body = error.read(MAX_RESPONSE_BYTES)
        status = error.code
        response_headers = error.headers
    except urllib.error.URLError as error:
        reason = redact_text(str(error.reason))
        raise RuntimeError(f"HTTP probe failed: {reason}") from error

    fastapi_proof = False
    if status == 200 and body:
        try:
            document = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            document = None
        fastapi_proof = (
            isinstance(document, dict) and document.get("layer") == "fastapi"
        )

    return {
        "status": status,
        "bodyBytesRead": len(body),
        "contentType": response_headers.get_content_type(),
        "hasClaimsChallenge": bool(
            response_headers.get("WWW-Authenticate", "").find("claims=") >= 0
        ),
        "fastapiProof": fastapi_proof,
    }


def _matrix(
    endpoint: str,
    probe_path: str,
    *,
    valid_token: str,
    wrong_audience_token: str | None,
    timeout: float,
) -> list[dict[str, object]]:
    urls = {
        "authMe": f"{endpoint}/.auth/me",
        "fastapi": f"{endpoint}/{probe_path.lstrip('/')}",
    }
    cases: list[tuple[str, str | None]] = [("no-token", None)]
    if wrong_audience_token is not None:
        cases.append(("wrong-audience", wrong_audience_token))
    cases.append(("presented-token", valid_token))

    rows: list[dict[str, object]] = []
    for case, token in cases:
        for target, url in urls.items():
            rows.append(
                {
                    "case": case,
                    "target": target,
                    **probe_url(url, token=token, timeout=timeout),
                }
            )
    return rows


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument("--resource-app-id", required=True)
    parser.add_argument("--allowed-client-id", action="append", default=[])
    parser.add_argument("--additional-audience", action="append", default=[])
    parser.add_argument("--expected-issuer")
    permission = parser.add_mutually_exclusive_group(required=True)
    permission.add_argument("--expected-scope")
    permission.add_argument("--expected-role")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--token-stdin", action="store_true")
    source.add_argument("--azure-cli-scope")
    source.add_argument("--device-code-client-id")
    parser.add_argument(
        "--authority-host",
        default="https://login.microsoftonline.com",
    )
    parser.add_argument("--include-wrong-audience-control", action="store_true")
    parser.add_argument("--probe-path", default="/auth/probe")
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
    )
    parser.add_argument(
        "--device-code-timeout",
        type=float,
        default=DEFAULT_DEVICE_CODE_TIMEOUT_SECONDS,
    )
    args = parser.parse_args(argv)
    if not 1 <= args.timeout <= 120:
        parser.error("--timeout must be between 1 and 120 seconds")
    if not 60 <= args.device_code_timeout <= 1800:
        parser.error(
            "--device-code-timeout must be between 60 and 1800 seconds"
        )
    if (
        args.include_wrong_audience_control
        and not args.azure_cli_scope
        and not args.device_code_client_id
    ):
        parser.error(
            "--include-wrong-audience-control requires Azure CLI or "
            "device-code acquisition"
        )
    if args.device_code_client_id and not args.expected_scope:
        parser.error("--device-code-client-id requires --expected-scope")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    try:
        endpoint = normalize_endpoint(args.endpoint)
        tenant_id = _guid(args.tenant_id, "tenant_id")
        resource_app_id = _guid(args.resource_app_id, "resource_app_id")
        if args.token_stdin:
            token = sys.stdin.read().strip()
            if not token:
                raise ValueError("No token was received on standard input")
            source = "stdin"
        elif args.azure_cli_scope:
            token = acquire_cli_token(
                tenant_id=tenant_id,
                scope=args.azure_cli_scope,
                timeout=args.timeout,
            )
            source = "azure-cli"
        else:
            caller_client_id = _guid(
                args.device_code_client_id,
                "device_code_client_id",
            )
            allowed_clients = {
                _guid(value, "allowed_client_id")
                for value in args.allowed_client_id
            }
            if allowed_clients and caller_client_id not in allowed_clients:
                raise ValueError(
                    "device-code client must be included in "
                    "--allowed-client-id"
                )
            token = acquire_device_code_token(
                tenant_id=tenant_id,
                client_id=caller_client_id,
                scope=(
                    f"api://{resource_app_id}/{args.expected_scope}"
                ),
                authority_host=normalize_endpoint(args.authority_host),
                timeout=args.device_code_timeout,
            )
            source = "msal-device-code"

        claims = parse_jwt_claims(token)
        claim_summary = summarize_claims(
            claims,
            tenant_id=tenant_id,
            resource_app_id=resource_app_id,
            expected_scope=args.expected_scope,
            expected_role=args.expected_role,
            allowed_client_ids=args.allowed_client_id,
            additional_audiences=args.additional_audience,
            expected_issuer=args.expected_issuer,
        )
        wrong_token = (
            acquire_wrong_audience_token(
                tenant_id=tenant_id,
                timeout=args.timeout,
            )
            if args.include_wrong_audience_control
            else None
        )
        result = {
            "tokenSource": source,
            "tokenPrinted": False,
            "tokenPersisted": False,
            "claims": claim_summary,
            "matrix": _matrix(
                endpoint,
                args.probe_path,
                valid_token=token,
                wrong_audience_token=wrong_token,
                timeout=args.timeout,
            ),
        }
        json.dump(result, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0
    except (
        ValueError,
        RuntimeError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
    ) as error:
        print(f"error: {redact_text(str(error))}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
