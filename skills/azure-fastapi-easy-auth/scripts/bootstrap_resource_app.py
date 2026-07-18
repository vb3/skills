#!/usr/bin/env python3
"""Create once or verify a durable Microsoft Entra resource API app."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from collections.abc import Sequence
from typing import Any


GRAPH_ROOT = "https://graph.microsoft.com/v1.0"
DEFAULT_TIMEOUT_SECONDS = 60.0


def _guid(value: str, name: str) -> str:
    try:
        return str(uuid.UUID(value))
    except ValueError as error:
        raise ValueError(f"{name} must be a UUID") from error


def build_resource_app_contract(
    *,
    app_id: str,
    scope_id: str,
    scope_value: str,
    caller_client_ids: Sequence[str],
) -> dict[str, object]:
    resource_app_id = _guid(app_id, "app_id")
    permission_id = _guid(scope_id, "scope_id")
    callers = sorted(
        {_guid(value, "caller_client_id") for value in caller_client_ids}
    )
    scope_text = f"Access this API as the signed-in user ({scope_value})."
    return {
        "identifierUris": [f"api://{resource_app_id}"],
        "requiredResourceAccess": [],
        "appRoles": [],
        "keyCredentials": [],
        "passwordCredentials": [],
        "api": {
            "requestedAccessTokenVersion": 2,
            "oauth2PermissionScopes": [
                {
                    "id": permission_id,
                    "adminConsentDescription": scope_text,
                    "adminConsentDisplayName": scope_text,
                    "isEnabled": True,
                    "type": "User",
                    "userConsentDescription": scope_text,
                    "userConsentDisplayName": scope_text,
                    "value": scope_value,
                }
            ],
            "preAuthorizedApplications": [
                {
                    "appId": caller,
                    "delegatedPermissionIds": [permission_id],
                }
                for caller in callers
            ],
        },
    }


def _run_az(arguments: list[str], timeout: float) -> Any:
    completed = subprocess.run(
        ["az", *arguments, "--output", "json"],
        check=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError("Azure CLI returned invalid JSON") from error


def _exact_app_matches(
    display_name: str,
    timeout: float,
) -> list[dict[str, object]]:
    result = _run_az(
        ["ad", "app", "list", "--display-name", display_name],
        timeout,
    )
    if not isinstance(result, list):
        raise RuntimeError("Azure CLI returned an invalid application list")
    return [
        item
        for item in result
        if isinstance(item, dict) and item.get("displayName") == display_name
    ]


def _read_application(object_id: str, timeout: float) -> dict[str, object]:
    result = _run_az(
        [
            "rest",
            "--method",
            "GET",
            "--url",
            (
                f"{GRAPH_ROOT}/applications/{object_id}"
                "?$select=id,appId,displayName,identifierUris,"
                "requiredResourceAccess,appRoles,keyCredentials,"
                "passwordCredentials,api"
            ),
        ],
        timeout,
    )
    if not isinstance(result, dict):
        raise RuntimeError("Microsoft Graph returned an invalid application")
    return result


def _scope_id(
    *,
    tenant_id: str,
    app_id: str,
    scope_value: str,
) -> str:
    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"entra-resource-api:{tenant_id}:{app_id}:{scope_value}",
        )
    )


def _validate_existing(
    application: dict[str, object],
    *,
    tenant_id: str,
    scope_value: str,
    caller_client_ids: Sequence[str],
) -> str:
    app_id_value = application.get("appId")
    if not isinstance(app_id_value, str):
        raise RuntimeError("Existing application has no appId")
    app_id = _guid(app_id_value, "existing appId")
    scope_id = _scope_id(
        tenant_id=tenant_id,
        app_id=app_id,
        scope_value=scope_value,
    )
    expected = build_resource_app_contract(
        app_id=app_id,
        scope_id=scope_id,
        scope_value=scope_value,
        caller_client_ids=caller_client_ids,
    )
    for field in (
        "identifierUris",
        "requiredResourceAccess",
        "appRoles",
        "keyCredentials",
        "passwordCredentials",
    ):
        actual = application.get(field) or []
        if actual != expected[field]:
            raise RuntimeError(
                f"Existing resource application drifted at {field}; "
                "refusing to mutate it"
            )
    api = application.get("api")
    if not isinstance(api, dict):
        raise RuntimeError("Existing resource application has no API contract")
    for field in ("requestedAccessTokenVersion", "oauth2PermissionScopes"):
        actual = api.get(field)
        if actual != expected["api"][field]:
            raise RuntimeError(
                f"Existing resource application drifted at api.{field}; "
                "refusing to mutate it"
            )
    actual_preauthorized = api.get("preAuthorizedApplications")
    if not isinstance(actual_preauthorized, list):
        raise RuntimeError(
            "Existing resource application drifted at "
            "api.preAuthorizedApplications; refusing to mutate it"
        )
    expected_preauthorized = expected["api"]["preAuthorizedApplications"]
    normalized_actual = sorted(
        actual_preauthorized,
        key=lambda item: str(item.get("appId"))
        if isinstance(item, dict)
        else "",
    )
    normalized_expected = sorted(
        expected_preauthorized,
        key=lambda item: str(item.get("appId")),
    )
    if normalized_actual != normalized_expected:
        raise RuntimeError(
            "Existing resource application drifted at "
            "api.preAuthorizedApplications; refusing to mutate it"
        )
    return scope_id


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--tenant-id", required=True)
    parser.add_argument(
        "--caller-client-id",
        action="append",
        required=True,
        help="Approved delegated caller client ID; repeat for multiple clients",
    )
    parser.add_argument("--scope-value", default="access_as_user")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--confirm-owner",
        action="store_true",
        help="Confirm authority to create the durable app registration",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
    )
    args = parser.parse_args(argv)
    if not args.display_name.strip():
        parser.error("--display-name must not be empty")
    if not args.scope_value.replace("_", "").isalnum():
        parser.error("--scope-value must contain letters, digits, or underscores")
    if not 1 <= args.timeout <= 120:
        parser.error("--timeout must be between 1 and 120 seconds")
    if args.apply and not args.confirm_owner:
        parser.error("--apply requires --confirm-owner")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    try:
        tenant_id = _guid(args.tenant_id, "tenant_id")
        callers = [
            _guid(value, "caller_client_id")
            for value in args.caller_client_id
        ]
        account = _run_az(["account", "show"], args.timeout)
        if not isinstance(account, dict) or account.get("tenantId") != tenant_id:
            raise RuntimeError(
                "Azure CLI is not signed in to the requested tenant"
            )

        matches = _exact_app_matches(args.display_name, args.timeout)
        if len(matches) > 1:
            raise RuntimeError(
                "Multiple applications have the exact display name; "
                "refusing ambiguous selection"
            )
        if matches:
            object_id_value = matches[0].get("id")
            if not isinstance(object_id_value, str):
                raise RuntimeError("Existing application has no object ID")
            application = _read_application(object_id_value, args.timeout)
            scope_id = _validate_existing(
                application,
                tenant_id=tenant_id,
                scope_value=args.scope_value,
                caller_client_ids=callers,
            )
            result = {
                "status": "verified",
                "created": False,
                "appId": application["appId"],
                "objectId": application["id"],
                "scope": (
                    f"api://{application['appId']}/{args.scope_value}"
                ),
                "scopeId": scope_id,
                "tenantConsentAssumed": False,
            }
        elif not args.apply:
            result = {
                "status": "absent",
                "created": False,
                "nextAction": (
                    "Rerun with --apply --confirm-owner after ownership approval"
                ),
                "tenantConsentAssumed": False,
            }
        else:
            created = _run_az(
                [
                    "ad",
                    "app",
                    "create",
                    "--display-name",
                    args.display_name,
                    "--sign-in-audience",
                    "AzureADMyOrg",
                ],
                args.timeout,
            )
            if not isinstance(created, dict):
                raise RuntimeError("Azure CLI returned an invalid new application")
            app_id = _guid(str(created.get("appId")), "new appId")
            object_id = _guid(str(created.get("id")), "new object ID")
            scope_id = _scope_id(
                tenant_id=tenant_id,
                app_id=app_id,
                scope_value=args.scope_value,
            )
            contract = build_resource_app_contract(
                app_id=app_id,
                scope_id=scope_id,
                scope_value=args.scope_value,
                caller_client_ids=callers,
            )
            _run_az(
                [
                    "rest",
                    "--method",
                    "PATCH",
                    "--url",
                    f"{GRAPH_ROOT}/applications/{object_id}",
                    "--headers",
                    "Content-Type=application/json",
                    "--body",
                    json.dumps(contract, separators=(",", ":")),
                ],
                args.timeout,
            )
            _run_az(["ad", "sp", "create", "--id", app_id], args.timeout)
            result = {
                "status": "created",
                "created": True,
                "appId": app_id,
                "objectId": object_id,
                "scope": f"api://{app_id}/{args.scope_value}",
                "scopeId": scope_id,
                "tenantConsentAssumed": False,
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
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
