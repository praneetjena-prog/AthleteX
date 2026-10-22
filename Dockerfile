# ==============================================================
# AthleteX - Bauhaus / Neo-Brutalist Sports Telemetry Cockpit
# Production Dockerfile for Google Cloud Run / Render / Railway
# ==============================================================

FROM python:3.11-slim

# Environment flags for optimal Python & Streamlit execution
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    STREAMLIT_SERVER_PORT=8080 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Layer 1: Install Python packages (cached unless requirements change)
COPY streamlit_app/requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Layer 2: Copy application code and certs
COPY streamlit_app/ ./streamlit_app/

# Expose port (Cloud Run, Render, and Railway route to $PORT)
EXPOSE 8080

# Health check probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl --fail http://localhost:8080/_stcore/health || exit 1

# Launch Streamlit pointing to the main Cockpit application
CMD ["streamlit", "run", "streamlit_app/app.py", "--server.port=8080", "--server.address=0.0.0.0"]
