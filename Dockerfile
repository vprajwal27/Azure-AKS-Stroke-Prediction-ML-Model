FROM python:3.12-slim

# LightGBM's compiled extension (lib_lightgbm.so) is dynamically linked
# against libgomp at runtime. python:3.12-slim will not include it by default

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Copy and install dependencies first so Docker can cache this layer
# and skip reinstalling everything when only app code changes.

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Run as a non-root user.
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /code
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]