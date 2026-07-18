# Fresh setup fast path

Use this path for an empty or minimal Python repository. It is designed to
reach one authenticated FastAPI response before adding databases, private data
services, or application-specific authorization.

## Inputs

Collect:

- Azure subscription and a Flex-supported region;
- Microsoft Entra workforce tenant ID;
- durable resource API display name;
- one approved delegated caller client ID for the first smoke test;
- confirmation that the operator may create and own the resource app.

Do not assume tenant-wide consent is required. Evaluate it only if token
issuance or tenant policy requires escalation.

Sign Azure CLI in to the exact tenant and subscription before directory
bootstrap:

```bash
az login --tenant "$ENTRA_TENANT_ID"
az account set --subscription "$AZURE_SUBSCRIPTION_ID"
```

## 1. Scaffold the project

From the target project directory:

```bash
python3 "<skill-directory>/scripts/scaffold_fastapi_flex.py" \
  --target .
```

The command refuses to overwrite:

- `function_app.py` using `func.AsgiFunctionApp`;
- `app/main.py` with a DB-free `/auth/probe`;
- `host.json` with no Functions route prefix;
- `local.settings.json` selecting the Python worker for `func start`;
- `requirements.txt`;
- `azure.yaml`;
- subscription and resource-group Bicep for Flex hosting;
- the canonical Easy Auth Bicep module.

If one of these files already exists, merge deliberately instead of forcing an
overwrite.

## 2. Prove the local FastAPI/Functions adapter

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
func start
```

In another terminal:

```bash
curl --fail --silent http://localhost:7071/auth/probe
```

Require `{"layer":"fastapi"}` before provisioning Azure.

`AuthLevel.ANONYMOUS` is intentional. Easy Auth enforces the Azure ingress;
requiring a Function key would add a second, unrelated authentication scheme.

## 3. Create or verify the durable resource API

First run read-only:

```bash
python3 "<skill-directory>/scripts/bootstrap_resource_app.py" \
  --display-name "<durable-resource-api-name>" \
  --tenant-id "$ENTRA_TENANT_ID" \
  --caller-client-id "$ENTRA_CALLER_CLIENT_ID"
```

If the exact app is absent and the operator confirms ownership, create it once:

```bash
python3 "<skill-directory>/scripts/bootstrap_resource_app.py" \
  --display-name "<durable-resource-api-name>" \
  --tenant-id "$ENTRA_TENANT_ID" \
  --caller-client-id "$ENTRA_CALLER_CLIENT_ID" \
  --apply \
  --confirm-owner
```

The script creates no credentials and requests no Microsoft Graph permissions.
It configures one v2 delegated `access_as_user` scope, preauthorizes only the
supplied caller, creates the service principal, and never deletes the app. On
later runs it verifies the exact contract read-only and refuses drift.

Record the returned `appId` as `ENTRA_RESOURCE_APP_ID`. Resource-app
preauthorization and Easy Auth caller authorization remain separate controls.

## 4. Configure azd

```bash
azd auth login
azd env new
azd env set AZURE_LOCATION "<flex-supported-region>"
azd env set ENTRA_TENANT_ID "$ENTRA_TENANT_ID"
azd env set ENTRA_RESOURCE_APP_ID "$ENTRA_RESOURCE_APP_ID"
azd env set ENTRA_ALLOWED_CLIENT_IDS "$ENTRA_CALLER_CLIENT_ID"
```

The Flex Bicep uses the resource API GUID as the v2 audience and puts the
approved caller client ID in `allowedApplications`. It also retains the
`api://<resource-client-id>` form for the same API.

## 5. Run the local and Azure preflight gates

```bash
python3 -m unittest discover -s "<skill-directory>/tests" -v

az bicep build --file infra/main.bicep --stdout >/dev/null

python3 "<skill-directory>/scripts/azure_preflight.py" \
  --platform functions-flex \
  --region "<flex-supported-region>"
```

Add `--use-vnet` only when the fresh deployment includes VNet integration.
That branch checks the additional `Microsoft.App` provider requirement.

## 6. Provision and deploy

```bash
azd provision
azd deploy
```

Do not proceed to auth diagnosis unless both commands succeed and the Function
host starts. A provider, region, role-assignment, package, or host-startup
failure is not an Easy Auth failure.

## 7. Prove the first authenticated 200

Use the resource scope returned by the bootstrap script:

```bash
uv run --with msal python \
  "<skill-directory>/scripts/easy_auth_probe.py" \
  --endpoint "$API_ENDPOINT" \
  --tenant-id "$ENTRA_TENANT_ID" \
  --resource-app-id "$ENTRA_RESOURCE_APP_ID" \
  --allowed-client-id "$ENTRA_CALLER_CLIENT_ID" \
  --expected-scope access_as_user \
  --device-code-client-id "$ENTRA_CALLER_CLIENT_ID" \
  --device-code-timeout 600 \
  --include-wrong-audience-control
```

The interactive device-code flow uses the approved caller registration, so the
token's v2 `azp` matches Easy Auth `allowedApplications`. The wrong-audience
control may use the existing Azure CLI session, but the approved-token control
does not.

Require:

| Control | Expected |
| --- | ---: |
| No token | 401 |
| Wrong audience | 401, empirical control |
| Approved token | 200 |
| FastAPI marker | true |

If all controls pass, stop. Add business dependencies afterward.

If a gate fails, load only the matching reference:

- token issuance or consent:
  [governance.md](governance.md);
- provisioning, deployment, or networking:
  [deployment-and-networking.md](deployment-and-networking.md);
- HTTP 401 or 403:
  [diagnostics.md](diagnostics.md), then
  [friction-analysis.md](friction-analysis.md) only if needed.
