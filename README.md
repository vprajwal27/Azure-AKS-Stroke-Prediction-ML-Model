# Azure AKS — At-Risk Prediction (ML on Kubernetes, end to end)

A containerized machine-learning prediction service deployed to **Azure Kubernetes Service (AKS)**, provisioned with **Terraform**, shipped through an **Azure DevOps CI/CD pipeline**, exposed via an **NGINX ingress**, and monitored with **Prometheus and Grafana**.

The model predicts an `at_risk` flag from a patient's age, gender, and a set of symptom indicators. The ML piece is intentionally simple — the focus of this project is the **infrastructure, automation, and operations** around a model, not the model itself.

> **Two planes, one repo.** Terraform owns the Azure layer (VNet, AKS, ACR). kubectl/Helm own everything inside the cluster (app, ingress, monitoring). The two never overlap in state, so in-cluster changes can't cause Terraform drift.

---


**Runtime request path:** User -> Azure Load Balancer (public IP) -> NGINX ingress controller -> ClusterIP service -> FastAPI pods (load the LightGBM model) -> response. Prometheus scrapes the app's `/metrics`; Grafana visualizes it. The cluster pulls its image from ACR using a managed identity with the `AcrPull` role (no image pull secrets).

**Delivery path:** Git push -> Azure DevOps pipeline -> Terraform apply (infra) -> build & push image to ACR -> deploy to staging -> manual approval gate -> provision & deploy a separate production environment.

---

## Tech stack

| Layer | Technology |
|---|---|
| Model | LightGBM (scikit-learn pipeline, serialized with joblib) |
| App | FastAPI + Uvicorn |
| Container | Docker (`python:3.12-slim`) |
| Registry | Azure Container Registry (ACR) |
| Orchestration | Azure Kubernetes Service (AKS), Azure CNI |
| Ingress | NGINX ingress controller (Helm) |
| Monitoring | Prometheus + Grafana (kube-prometheus-stack, Helm) |
| IaC | Terraform (azurerm provider), remote state in Azure Blob with locking |
| CI/CD | Azure DevOps pipeline (multi-stage, gated promotion) |

---

## The model

The dataset is the **Stroke Risk Prediction Dataset** on Kaggle:
https://www.kaggle.com/datasets/mahatiratusher/stroke-risk-prediction-dataset

The target is `at_risk`; features are `age`, `gender`, and a set of binary symptom flags. A scikit-learn pipeline (one-hot encoding for `gender` + a tuned LightGBM classifier) was trained and serialized to `app/artifacts/at_risk_lgbm_model.joblib`, which is committed to the repo so the image builds without a separate model-fetch step.

Full training and validation results — metrics, and the leakage checks done to confirm they're trustworthy — are in **[`model_performance_result.md`](model_performance_result.md)**.

---

## The app

A single-container FastAPI service. Routes:

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | HTML form UI with a probability gauge |
| `/predict` | POST | Pydantic-validated input -> `{prediction, probability}` |
| `/health` | GET | `{"status":"ok","model_loaded":true}` — used by k8s probes |
| `/metrics` | GET | Prometheus metrics (via `prometheus-fastapi-instrumentator`) |

The model is loaded once at startup and kept in memory. `/metrics` is exposed at app-creation time so Prometheus can scrape per-endpoint request counts and latencies.

### Run locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000, or call the API directly:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
        "age": 67, "gender": "Male", "chest_pain": 1, "high_blood_pressure": 1,
        "irregular_heartbeat": 1, "shortness_of_breath": 1, "fatigue_weakness": 1,
        "dizziness": 0, "swelling_edema": 0, "neck_jaw_pain": 0,
        "excessive_sweating": 1, "persistent_cough": 0, "nausea_vomiting": 0,
        "chest_discomfort": 1, "cold_hands_feet": 0, "snoring_sleep_apnea": 1,
        "anxiety_doom": 0
      }'
# -> {"prediction":"at_risk","probability":0.999...}
```

Interactive Swagger docs are at `/docs`.

---

## Infrastructure (Terraform)

Located in `Terraform/`. Provisions: resource group, custom VNet + subnet, ACR, and an AKS cluster (system-assigned managed identity, Azure CNI). The cluster is granted `AcrPull` on the registry so it pulls images without a secret.

State is stored remotely in an Azure Storage Account (blob) with automatic state locking. Staging and production are separated with **Terraform workspaces** — one config, isolated state per environment.

```bash
cd Terraform

# one-time: create the state storage account by hand (see Terraform/README.md),
# then uncomment + fill the backend block in 01-main.tf

terraform init
terraform workspace new staging        # first time
terraform apply -var="environment=staging"
```

There are **no Kubernetes or Helm providers in the Terraform** — this is deliberate. Terraform stops at the Azure resources; everything inside the cluster is managed by kubectl/Helm. That keeps the two management planes from colliding.

---

## Container

The Dockerfile uses a `python:3.12-slim` base with a non-root user. It installs `libgomp1` (LightGBM dynamically links libgomp, which the slim image lacks), and uses exec-form `uvicorn` as the entrypoint for correct signal handling as PID 1.

Build and push to ACR (server-side, no local Docker needed):

```bash
az acr build --registry <acr-name> --image at-risk-api:<tag> --platform linux/amd64 .
```

---

## Kubernetes manifests

In `kube-manifests/`:

- `deployment.yml` — the app Deployment, with readiness/liveness probes on `/health`
- `ClusterIP-service.yml` — internal service (the ingress controller holds the public IP, not the app)
- `Ingress.yml` — NGINX ingress routing `/` -> the service
- `prometheus.yml` — a ServiceMonitor that tells Prometheus to scrape the app's `/metrics`

---

## CI/CD (Azure DevOps)

`azure-pipelines.yml` defines a multi-stage pipeline triggered on push to `main`:

1. **Infra (staging)** — `terraform apply` for the staging workspace
2. **Build** — `az acr build` -> push image to ACR, tagged with the build ID
3. **Deploy (staging)** — `az aks get-credentials`, Helm-install ingress + monitoring (idempotent), inject the real image into the manifest, `kubectl apply`
4. **Deploy (production)** — gated behind a **manual approval** on an Azure DevOps `production` environment; provisions a separate prod stack (own workspace) and deploys

The image reference is substituted at deploy time (correct registry + unique build-ID tag), so deploys are repeatable and never depend on hand-edited YAML.

---

## Monitoring

The kube-prometheus-stack provides cluster-level dashboards out of the box (node/pod health). Application-level metrics come from the app's `/metrics` endpoint, scraped via a ServiceMonitor, giving per-endpoint request rate, latency, and error counts in Grafana.

```bash
# reach Grafana (internal service)
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80
# query in Grafana / Prometheus:
#   http_request_duration_seconds_count           (requests per endpoint)
#   rate(http_request_duration_seconds_count[5m]) (request rate)
```

---

## Repo layout

```
app/                  FastAPI app + model artifact (goes into the image)
kube-manifests/       Deployment, Service, Ingress, ServiceMonitor (kubectl)
Terraform/            VNet, AKS, ACR (terraform)
Dockerfile
azure-pipelines.yml   Azure DevOps CI/CD definition
model_performance_result.md
README.md
```

---

## Notes

- The app makes no external network calls (UI assets are inlined), so it behaves the same in a locked-down cluster as it does locally.
- The model artifact lives in `app/artifacts/`, so the Dockerfile just copies it in — no separate fetch step.
- This is a portfolio project: it's designed to be stood up, demonstrated, and torn down (`terraform destroy`) rather than run continuously.
