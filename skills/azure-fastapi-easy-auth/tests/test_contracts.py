from __future__ import annotations

import base64
import importlib.util
import json
import re
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from types import SimpleNamespace
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

    def test_device_code_flow_uses_the_approved_client_and_bounds_expiry(
        self,
    ) -> None:
        captured: dict[str, object] = {}

        class PublicClientApplication:
            def __init__(self, client_id: str, *, authority: str) -> None:
                captured["client_id"] = client_id
                captured["authority"] = authority

            def initiate_device_flow(self, *, scopes):
                captured["scopes"] = scopes
                return {
                    "user_code": "ABCD-EFGH",
                    "message": "Use the code to sign in.",
                    "expires_at": 9_999_999_999,
                }

            def acquire_token_by_device_flow(self, flow):
                captured["expires_at"] = flow["expires_at"]
                return {"access_token": "header.payload.signature"}

        fake_msal = SimpleNamespace(
            PublicClientApplication=PublicClientApplication
        )
        with patch.dict(
            __import__("sys").modules,
            {"msal": fake_msal},
        ):
            token = self.probe.acquire_device_code_token(
                tenant_id="11111111-1111-1111-1111-111111111111",
                client_id="33333333-3333-3333-3333-333333333333",
                scope=(
                    "api://22222222-2222-2222-2222-222222222222/"
                    "access_as_user"
                ),
                authority_host="https://login.microsoftonline.com",
                timeout=30,
            )

        self.assertEqual(token, "header.payload.signature")
        self.assertEqual(
            captured["client_id"],
            "33333333-3333-3333-3333-333333333333",
        )
        self.assertEqual(
            captured["scopes"],
            [
                "api://22222222-2222-2222-2222-222222222222/"
                "access_as_user"
            ],
        )
        self.assertLessEqual(
            captured["expires_at"],
            self.probe.time.time() + 30,
        )


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


class ResourceAppBootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bootstrap = load_script("bootstrap_resource_app")

    def test_contract_is_v2_delegated_and_has_no_credentials_or_graph_access(
        self,
    ) -> None:
        contract = self.bootstrap.build_resource_app_contract(
            app_id="22222222-2222-2222-2222-222222222222",
            scope_id="55555555-5555-5555-5555-555555555555",
            scope_value="access_as_user",
            caller_client_ids=[
                "33333333-3333-3333-3333-333333333333"
            ],
        )
        self.assertEqual(
            contract["identifierUris"],
            ["api://22222222-2222-2222-2222-222222222222"],
        )
        self.assertEqual(contract["requiredResourceAccess"], [])
        self.assertEqual(contract["appRoles"], [])
        self.assertEqual(contract["keyCredentials"], [])
        self.assertEqual(contract["passwordCredentials"], [])
        self.assertEqual(contract["api"]["requestedAccessTokenVersion"], 2)
        scopes = contract["api"]["oauth2PermissionScopes"]
        self.assertEqual(len(scopes), 1)
        self.assertEqual(scopes[0]["value"], "access_as_user")
        self.assertEqual(
            contract["api"]["preAuthorizedApplications"],
            [
                {
                    "appId": "33333333-3333-3333-3333-333333333333",
                    "delegatedPermissionIds": [
                        "55555555-5555-5555-5555-555555555555"
                    ],
                }
            ],
        )

    def test_existing_contract_accepts_graph_caller_ordering(self) -> None:
        tenant_id = "11111111-1111-1111-1111-111111111111"
        app_id = "22222222-2222-2222-2222-222222222222"
        callers = [
            "33333333-3333-3333-3333-333333333333",
            "44444444-4444-4444-4444-444444444444",
        ]
        scope_id = self.bootstrap._scope_id(
            tenant_id=tenant_id,
            app_id=app_id,
            scope_value="access_as_user",
        )
        application = self.bootstrap.build_resource_app_contract(
            app_id=app_id,
            scope_id=scope_id,
            scope_value="access_as_user",
            caller_client_ids=callers,
        )
        application["appId"] = app_id
        application["api"]["preAuthorizedApplications"].reverse()

        actual_scope_id = self.bootstrap._validate_existing(
            application,
            tenant_id=tenant_id,
            scope_value="access_as_user",
            caller_client_ids=callers,
        )

        self.assertEqual(actual_scope_id, scope_id)


class ArtifactContractTests(unittest.TestCase):
    def test_fresh_setup_fast_path_is_the_primary_workflow(self) -> None:
        skill = (SKILL_ROOT / "SKILL.md").read_text()

        fast_path = skill.index("## Fresh setup fast path")
        detailed = skill.index("## Detailed workflow")
        debug_path = skill.index("## Debug path")
        self.assertLess(fast_path, detailed)
        self.assertLess(detailed, debug_path)
        self.assertIn(
            "Do not load debugging references during a clean setup",
            skill,
        )
        self.assertIn("scripts/scaffold_fastapi_flex.py", skill)
        self.assertIn("references/fresh-setup.md", skill)

    def test_fresh_setup_uses_the_approved_caller_for_the_200_probe(
        self,
    ) -> None:
        fresh_setup = (
            SKILL_ROOT / "references" / "fresh-setup.md"
        ).read_text()

        self.assertIn("--device-code-client-id", fresh_setup)
        self.assertIn("--device-code-timeout 600", fresh_setup)
        self.assertIn('"$ENTRA_CALLER_CLIENT_ID"', fresh_setup)
        first_200 = fresh_setup.split(
            "## 7. Prove the first authenticated 200",
            1,
        )[1]
        self.assertNotIn("--azure-cli-scope", first_200)

    def test_scaffold_script_creates_a_complete_fastapi_flex_project(
        self,
    ) -> None:
        scaffold = load_script("scaffold_fastapi_flex")
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory).resolve()

            created = scaffold.scaffold_project(target)

            expected = {
                "azure.yaml",
                "function_app.py",
                "host.json",
                "local.settings.json",
                "requirements.txt",
                "app/__init__.py",
                "app/main.py",
                "infra/main.bicep",
                "infra/app.bicep",
                "infra/easy-auth.bicep",
                "infra/main.parameters.json",
            }
            self.assertEqual(
                {str(path.relative_to(target)) for path in created},
                expected,
            )
            self.assertIn(
                "func.AsgiFunctionApp",
                (target / "function_app.py").read_text(),
            )
            self.assertIn(
                "host: function",
                (target / "azure.yaml").read_text(),
            )
            local_settings = json.loads(
                (target / "local.settings.json").read_text()
            )
            self.assertEqual(
                local_settings["Values"]["FUNCTIONS_WORKER_RUNTIME"],
                "python",
            )

            with self.assertRaises(FileExistsError):
                scaffold.scaffold_project(target)

    def test_fresh_flex_bicep_creates_hosting_and_easy_auth(self) -> None:
        app_bicep = (
            SKILL_ROOT / "assets" / "scaffold" / "infra" / "app.bicep"
        ).read_text()
        main_bicep = (
            SKILL_ROOT / "assets" / "scaffold" / "infra" / "main.bicep"
        ).read_text()

        self.assertIn("name: 'FC1'", app_bicep)
        self.assertIn("tier: 'FlexConsumption'", app_bicep)
        self.assertIn("functionAppConfig", app_bicep)
        self.assertIn("param runtimeName string = 'python'", app_bicep)
        self.assertIn("'azd-service-name': 'api'", app_bicep)
        self.assertIn("module easyAuth './easy-auth.bicep'", app_bicep)
        self.assertIn("targetScope = 'subscription'", main_bicep)
        self.assertIn("Microsoft.Resources/resourceGroups", main_bicep)

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
        documented_role_ids = {
            "b7e6dc6d-f1e8-4753-8033-0f276bb0955b",
            "ba92f5b4-2d11-453d-a403-e96b0029c9fe",
            "974c5e8b-45b9-4653-ba55-5f855dd0fb88",
            "0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3",
            "3913510d-42f4-4e42-8a64-420c390055eb",
        }
        allowed_ids = synthetic_ids | documented_role_ids
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
                self.assertIn(identifier.lower(), allowed_ids, str(path))

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
