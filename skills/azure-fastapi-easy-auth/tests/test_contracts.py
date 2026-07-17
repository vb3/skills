from __future__ import annotations

import base64
import importlib.util
import json
import re
import unittest
from email.message import Message
from pathlib import Path
from unittest.mock import patch


SKILL_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = SKILL_ROOT / "fixtures"


def load_script(name: str):
    path = SKILL_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ClaimSummaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.probe = load_script("easy_auth_probe")

    def fixture(self, name: str) -> dict[str, object]:
        return json.loads((FIXTURES / "claims" / name).read_text())

    def test_v2_delegated_claims_match_guid_audience_and_azp(self) -> None:
        claims = self.fixture("v2-delegated.json")

        summary = self.probe.summarize_claims(
            claims,
            tenant_id="11111111-1111-1111-1111-111111111111",
            resource_app_id="22222222-2222-2222-2222-222222222222",
            expected_scope="access_as_user",
            allowed_client_ids=["33333333-3333-3333-3333-333333333333"],
        )

        self.assertEqual(summary["tokenKind"], "delegated")
        self.assertEqual(summary["clientClaim"], "azp")
        self.assertTrue(summary["audienceMatches"])
        self.assertTrue(summary["issuerMatches"])
        self.assertTrue(summary["tenantMatches"])
        self.assertTrue(summary["permissionMatches"])
        self.assertTrue(summary["clientApplicationMatches"])
        self.assertNotIn("aud", summary)
        self.assertNotIn("azp", summary)

    def test_v1_delegated_claims_match_app_id_uri_and_appid(self) -> None:
        claims = self.fixture("v1-delegated.json")

        summary = self.probe.summarize_claims(
            claims,
            tenant_id="11111111-1111-1111-1111-111111111111",
            resource_app_id="22222222-2222-2222-2222-222222222222",
            expected_scope="access_as_user",
            allowed_client_ids=["33333333-3333-3333-3333-333333333333"],
        )

        self.assertEqual(summary["tokenVersion"], "1.0")
        self.assertEqual(summary["clientClaim"], "appid")
        self.assertTrue(summary["audienceMatches"])
        self.assertTrue(summary["issuerMatches"])

    def test_app_only_claims_require_role_not_delegated_scope(self) -> None:
        claims = self.fixture("v2-app-only.json")

        summary = self.probe.summarize_claims(
            claims,
            tenant_id="11111111-1111-1111-1111-111111111111",
            resource_app_id="22222222-2222-2222-2222-222222222222",
            expected_role="Api.Invoke",
            allowed_client_ids=["44444444-4444-4444-4444-444444444444"],
        )

        self.assertEqual(summary["tokenKind"], "app-only")
        self.assertTrue(summary["permissionMatches"])
        self.assertFalse(summary["delegatedScopesPresent"])
        self.assertTrue(summary["applicationRolesPresent"])

    def test_wrong_audience_and_client_are_reported_as_booleans(self) -> None:
        claims = self.fixture("v2-delegated.json")

        summary = self.probe.summarize_claims(
            claims,
            tenant_id="11111111-1111-1111-1111-111111111111",
            resource_app_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            expected_scope="access_as_user",
            allowed_client_ids=["bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"],
        )

        self.assertFalse(summary["audienceMatches"])
        self.assertFalse(summary["clientApplicationMatches"])

    def test_redaction_removes_jwts_and_bearer_values(self) -> None:
        header = base64.urlsafe_b64encode(
            b'{"alg":"RS256"}'
        ).decode().rstrip("=")
        payload = base64.urlsafe_b64encode(
            b'{"aud":"22222222-2222-2222-2222-222222222222"}'
        ).decode().rstrip("=")
        value = f"Bearer {header}.{payload}.signature"

        redacted = self.probe.redact_text(value)

        self.assertNotIn("eyJ", redacted)
        self.assertEqual(redacted, "Bearer [REDACTED]")

    def test_probe_sends_the_in_memory_token_as_a_bearer_header(self) -> None:
        captured = None

        class Response:
            status = 200
            headers = Message()

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return None

            def read(self, _limit: int) -> bytes:
                return b'{"layer":"fastapi"}'

        def fake_urlopen(request, *, timeout):
            nonlocal captured
            captured = request
            self.assertEqual(timeout, 5)
            return Response()

        token = "header.payload.signature"
        with patch.object(
            self.probe.urllib.request,
            "urlopen",
            side_effect=fake_urlopen,
        ):
            result = self.probe.probe_url(
                "https://example.invalid/auth/probe",
                token=token,
                timeout=5,
            )

        self.assertIsNotNone(captured)
        self.assertEqual(
            captured.get_header("Authorization"),
            "Bear" + "er " + token,
        )
        self.assertTrue(result["fastapiProof"])


class PreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.preflight = load_script("azure_preflight")

    def test_flex_vnet_requires_web_and_app_providers(self) -> None:
        providers = self.preflight.required_providers(
            platform="functions-flex",
            use_vnet=True,
        )

        self.assertEqual(providers, ["Microsoft.Web", "Microsoft.App"])

    def test_app_service_without_vnet_requires_web_provider_only(self) -> None:
        providers = self.preflight.required_providers(
            platform="app-service",
            use_vnet=False,
        )

        self.assertEqual(providers, ["Microsoft.Web"])

    def test_non_flex_functions_require_web_provider_only(self) -> None:
        providers = self.preflight.required_providers(
            platform="functions",
            use_vnet=True,
        )

        self.assertEqual(providers, ["Microsoft.Web"])


class ArtifactContractTests(unittest.TestCase):
    def test_skill_links_the_required_progressive_disclosure_references(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text()

        self.assertIn("name: azure-fastapi-easy-auth", skill)
        for reference in (
            "architecture-and-flows.md",
            "easy-auth-configuration.md",
            "deployment-and-networking.md",
            "diagnostics.md",
            "governance.md",
            "friction-analysis.md",
            "sources.md",
        ):
            self.assertIn(f"references/{reference}", skill)

    def test_committed_artifacts_have_no_real_ids(self) -> None:
        uuid_pattern = re.compile(
            r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-"
            r"[0-9a-f]{4}-[0-9a-f]{12}\b",
            re.IGNORECASE,
        )
        synthetic_ids = {
            f"{digit * 8}-{digit * 4}-{digit * 4}-"
            f"{digit * 4}-{digit * 12}"
            for digit in "123456789"
        }
        for path in SKILL_ROOT.rglob("*"):
            if not path.is_file() or path.suffix not in {
                ".md",
                ".json",
                ".py",
                ".bicep",
                ".yaml",
                ".yml",
            }:
                continue
            if "tests" in path.parts:
                continue
            content = path.read_text()
            self.assertNotIn("\N{EM DASH}", content, str(path))
            for identifier in uuid_pattern.findall(content):
                self.assertIn(identifier.lower(), synthetic_ids, str(path))

    def test_authsettings_fixture_has_only_synthetic_ids(self) -> None:
        settings = json.loads(
            (FIXTURES / "authsettings-v2.json").read_text()
        )
        serialized = json.dumps(settings)

        self.assertIn("11111111-1111-1111-1111-111111111111", serialized)
        self.assertIn("22222222-2222-2222-2222-222222222222", serialized)

    def test_bicep_enforces_v2_issuer_audiences_and_client_policy(self) -> None:
        bicep = (
            SKILL_ROOT / "assets" / "bicep" / "easy-auth.bicep"
        ).read_text()

        self.assertIn("name: 'authsettingsV2'", bicep)
        self.assertIn("runtimeVersion: '~1'", bicep)
        self.assertIn("requireAuthentication: true", bicep)
        self.assertIn("unauthenticatedClientAction: 'Return401'", bicep)
        self.assertIn(
            "${environment().authentication.loginEndpoint}${tenantId}/v2.0",
            bicep,
        )
        self.assertIn("resourceAppClientId", bicep)
        self.assertIn("param allowedClientApplicationIds string[]", bicep)
        self.assertIn("'api://${resourceAppClientId}'", bicep)
        self.assertIn("allowedApplications: allowedClientApplicationIds", bicep)
        self.assertIn("length(allowedClientApplicationIds) > 0", bicep)
        self.assertIn("requireHttps: true", bicep)
        self.assertIn("forwardProxyConvention", bicep)
        self.assertIn("forwardProxyCustomHostHeaderName", bicep)
        self.assertIn("forwardProxyCustomProtoHeaderName", bicep)
        self.assertIn("tokenStore", bicep)
        self.assertNotRegex(
            bicep,
            re.compile(r"(clientSecret|password|credential)", re.IGNORECASE),
        )

    def test_commands_use_the_resolved_skill_directory(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text()
        deployment = (
            SKILL_ROOT / "references" / "deployment-and-networking.md"
        ).read_text()

        self.assertIn("<skill-directory>/tests", skill)
        self.assertIn("<skill-directory>/assets/bicep/easy-auth.bicep", skill)
        self.assertIn("<skill-directory>/tests", deployment)
        self.assertNotIn(
            "-s skills/azure-fastapi-easy-auth/tests",
            skill + deployment,
        )


if __name__ == "__main__":
    unittest.main()
