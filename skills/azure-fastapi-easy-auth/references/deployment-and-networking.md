# Deployment and networking

## Local gate

Run before Azure mutation:

```bash
python3 -m unittest discover \
  -s "<skill-directory>/tests" -v

az bicep build \
  --file "<skill-directory>/assets/bicep/easy-auth.bicep" \
  --stdout >/dev/null
```

## Read-only preflight

Azure Functions Flex with VNet integration:

```bash
python3 "<skill-directory>/scripts/azure_preflight.py" \
  --platform functions-flex \
  --use-vnet \
  --region "$AZURE_LOCATION"
```

App Service:

```bash
python3 "<skill-directory>/scripts/azure_preflight.py" \
  --platform app-service \
  --region "$AZURE_LOCATION"
```

The script does not register providers or create resources. A nonzero status for
an unregistered provider or unsupported Flex region is a deployment blocker,
not an auth failure.

## Azure Developer CLI sequence

Use the repository's `azure.yaml` and Bicep structure. The common sequence is:

```bash
azd auth login
azd env new
azd env set ENTRA_TENANT_ID "$ENTRA_TENANT_ID"
azd env set ENTRA_RESOURCE_APP_ID "$ENTRA_RESOURCE_APP_ID"
azd provision
azd deploy
```

`azd up` combines provision and deploy when the project supports it. Keep
directory-object bootstrap outside disposable `azd` cleanup unless the
registration is explicitly marked transient.

Recommended gate order:

1. tool, provider, region, quota, and network preflight;
2. read-only registration and consent verification;
3. local tests and Bicep compilation;
4. infrastructure provision;
5. package deployment;
6. deployed settings readback;
7. no-token and wrong-audience controls;
8. expected-token platform and FastAPI proof;
9. business and database proof;
10. owned transient cleanup.

This sequence is an operational recommendation, not a single documented Azure
guarantee.

## Azure Functions Flex

Check:

- Linux runtime and supported region;
- Azure CLI version supported by the Flex commands;
- `Microsoft.Web` registration;
- `Microsoft.App` registration when using VNet integration;
- subnet delegation to `Microsoft.App/environments`;
- storage and deployment package access;
- regional memory quota;
- private DNS and data-plane routes independently from public API ingress.

Flex deployment stores a package in blob storage and the app retrieves it.
Diagnose package upload and startup before HTTP auth. Flex does not use
deployment slots.

Use the documented region discovery command when needed:

```bash
az functionapp list-flexconsumption-locations \
  --query "sort_by(@, &name)[].{Region:name}" \
  --output table
```

## Other Azure Functions plans

For Consumption, Premium, or Dedicated plans, run the generic Functions
preflight:

```bash
python3 "<skill-directory>/scripts/azure_preflight.py" \
  --platform functions
```

These plans use `Microsoft.Web` but do not inherit Flex-specific requirements
such as `Microsoft.App/environments` subnet delegation. Check the selected
plan's deployment slots, package deployment, networking, and scaling behavior
in its current hosting documentation.

## App Service

Check:

- plan and OS support for the FastAPI deployment method;
- startup command and health endpoint;
- HTTPS and proxy settings;
- source IP and private endpoint reachability;
- whether Front Door or Application Gateway requires forward-proxy headers.

Package deployment failures, startup failures, and reverse-proxy routing can all
prevent a FastAPI response while Easy Auth remains healthy.

## Apply the module

See
[`assets/bicep/main.example.bicep`](../assets/bicep/main.example.bicep) and its
synthetic parameter file. In a real deployment, pass values from the azd
environment or the parent Bicep template. Do not commit tenant-specific values.

## Minimal FastAPI proof

Mount the DB-free route from
[`examples/fastapi_probe.py`](../examples/fastapi_probe.py). The route should:

- perform no database, storage, or model call;
- return a stable `layer: fastapi` marker;
- report only whether the platform principal header is present;
- remain behind the same Easy Auth ingress as protected routes.

This separates platform forwarding from downstream dependency health.

## Deployment failure classification

| Evidence | Classification |
| --- | --- |
| ARM deployment error | Provisioning |
| Package upload or OneDeploy error | Code deployment |
| Function host never starts | Runtime startup |
| Endpoint unreachable | Network or ingress |
| No token gets 401 | Easy Auth authentication control |
| Valid caller gets 403 | Easy Auth authorization or app authorization |
| Probe gets 200, DB route fails | Business or dependency |

Do not call a deployment green when only token acquisition succeeded.
