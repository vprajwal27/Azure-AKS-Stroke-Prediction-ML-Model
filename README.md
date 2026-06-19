# at-risk-api

FastAPI service that serves the `at_risk` LightGBM model: a single page with a
form for manual checks (`GET /`), the prediction endpoint it calls
(`POST /predict`), and a health check for orchestration (`GET /health`).
Model is loaded once at startup and kept in memory.

## Run locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then open http://localhost:8000 in a browser, or hit the API directly:

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

Interactive API docs (Swagger) are at `/docs`.

## Project layout

```
app/
  main.py            FastAPI app: routes for /, /predict, /health
  schemas.py          Pydantic request/response models
  model_service.py    Loads the joblib pipeline, wraps predict()
  templates/
    index.html         Self-contained UI (HTML+CSS+JS, no external deps)
  artifacts/
    at_risk_lgbm_model.joblib   trained sklearn Pipeline (preprocessing + LightGBM)
requirements.txt
```

## Notes for the next phase (containerizing / AKS)

- No external network calls anywhere in the app (fonts, scripts, etc. are all
  inlined), so it'll behave the same in a locked-down cluster as it does locally.
- `/health` returns `{"status": "ok", "model_loaded": true}` once the model is
  loaded — good candidate for both liveness and readiness probes.
- The model artifact is already inside `app/artifacts/`, so a Dockerfile just
  needs to `COPY` this whole directory in; no separate model-fetch step needed.
