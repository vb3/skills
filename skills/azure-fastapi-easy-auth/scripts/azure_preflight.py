#!/usr/bin/env python3
"""Run a read-only Azure hosting preflight for Easy Auth deployments."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Sequence
from typing import Any


DEFAULT_TIMEOUT_SECONDS = 30.0


def required_providers(*, platform: str, use_vnet: bool) -> list[str]:
    providers = ["Microsoft.Web"]
    if platform == "functions-flex" and use_vnet:
        providers.append("Microsoft.App")
    return providers


def run_az(arguments: list[str], timeout: float) -> Any:
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


def provider_status(namespace: str, timeout: float) -> dict[str, object]:
    result = run_az(
        ["provider", "show", "--namespace", namespace],
        timeout,
    )
    if not isinstance(result, dict):
        raise RuntimeError(f"Unexpected provider response for {namespace}")
    state = result.get("registrationState")
    return {
        "namespace": namespace,
        "registered": state == "Registered",
        "registrationState": state,
    }


def flex_regions(timeout: float) -> list[str]:
    result = run_az(
        ["functionapp", "list-flexconsumption-locations"],
        timeout,
    )
    if not isinstance(result, list):
        raise RuntimeError("Unexpected Flex location response")
    return sorted(
        value["name"]
        for value in result
        if isinstance(value, dict) and isinstance(value.get("name"), str)
    )


def tool_version(command: list[str], timeout: float) -> dict[str, object]:
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        return {"available": False}
    return {
        "available": True,
        "versionOutput": completed.stdout.strip().splitlines()[0],
    }


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--platform",
        choices=("functions", "functions-flex", "app-service"),
        required=True,
    )
    parser.add_argument("--use-vnet", action="store_true")
    parser.add_argument("--region")
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
    )
    args = parser.parse_args(argv)
    if not 1 <= args.timeout <= 120:
        parser.error("--timeout must be between 1 and 120 seconds")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    try:
        providers = [
            provider_status(namespace, args.timeout)
            for namespace in required_providers(
                platform=args.platform,
                use_vnet=args.use_vnet,
            )
        ]
        result: dict[str, object] = {
            "readOnly": True,
            "platform": args.platform,
            "providers": providers,
            "tools": {
                "azureCli": tool_version(
                    ["az", "version", "--output", "json"],
                    args.timeout,
                ),
                "azureDeveloperCli": tool_version(
                    ["azd", "version"],
                    args.timeout,
                ),
            },
        }
        if args.platform == "functions-flex":
            regions = flex_regions(args.timeout)
            result["flex"] = {
                "requestedRegion": args.region,
                "requestedRegionSupported": (
                    args.region in regions if args.region else None
                ),
                "supportedRegions": regions,
            }
        json.dump(result, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        registered = all(
            item["registered"]
            for item in providers
            if isinstance(item, dict)
        )
        region_ok = (
            args.platform != "functions-flex"
            or not args.region
            or bool(result["flex"]["requestedRegionSupported"])
        )
        return 0 if registered and region_ok else 3
    except (
        RuntimeError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
