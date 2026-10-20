FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV PORT=8080
# Private Cloud Run service reached through `gcloud run services proxy`, so the browser Origin is
# localhost while Host is *.run.app; Streamlit's CORS/XSRF checks would reject that.
CMD streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true \
    --server.enableCORS=false --server.enableXsrfProtection=false --browser.gatherUsageStats=false
