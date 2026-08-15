# syntax=docker/dockerfile:1

FROM python:3.12-slim

# The same Python version as local development and CI, so behaviour cannot
# differ between the three environments (GUIDE NFR-15).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv/fairshare

# Dependencies are installed before the source is copied so that editing code
# does not invalidate the cached dependency layer (GUIDE D-3).
COPY requirements.txt ./
RUN python -m pip install --upgrade pip && pip install -r requirements.txt

COPY app ./app

# The application never needs root, so it does not run as root (GUIDE D-4).
RUN useradd --create-home --uid 1000 fairshare && chown -R fairshare:fairshare /srv/fairshare
USER fairshare

EXPOSE 8000

# Uses the standard library rather than adding curl to the image.
HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/').read()"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
