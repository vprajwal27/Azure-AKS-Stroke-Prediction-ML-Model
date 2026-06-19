"""FastAPI app: serves the prediction UI and the /predict + /health endpoints."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from prometheus_fastapi_instrumentator import Instrumentator

from app.model_service import model_service
from app.schemas import HealthResponse, PatientFeatures, PredictionResponse

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the model once, before the app starts accepting traffic.
    model_service.load()
    yield
    # (no teardown needed; nothing to release)


app = FastAPI(
    title="At-Risk Prediction Service",
    description="Predicts at_risk from patient age, gender, and symptom flags.",
    version="1.0.0",
    lifespan=lifespan,
)

# Add Prometheus instrumentation and the /metrics endpoint at app-creation
# time (not inside lifespan, where route registration runs too late).
# include_in_schema=False keeps /metrics out of the Swagger docs.
Instrumentator().instrument(app).expose(app, include_in_schema=False)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


@app.post("/predict", response_model=PredictionResponse)
async def predict(features: PatientFeatures) -> PredictionResponse:
    return model_service.predict(features)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    loaded = model_service.is_loaded
    return HealthResponse(status="ok" if loaded else "unavailable", model_loaded=loaded)