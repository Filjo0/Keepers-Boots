FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt ./
COPY THIRD_PARTY_NOTICES.txt ./
COPY LICENSE ./
RUN pip install --no-cache-dir -r requirements.txt
COPY keepers_boots ./keepers_boots
COPY web ./web
COPY docs/api.schema.json ./docs/api.schema.json
COPY docs/knowledge/keeper-principles.md ./docs/knowledge/keeper-principles.md
COPY data/agent-recordings ./data/agent-recordings
RUN useradd --uid 10001 --create-home keeper
USER keeper
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"
CMD ["python", "-m", "keepers_boots.api", "--host", "0.0.0.0", "--agents", "recorded"]
