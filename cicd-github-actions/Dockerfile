# Multi-stage: the build stage never reaches the runtime image.
FROM python:3.12-slim AS build
WORKDIR /src
COPY requirements-dev.txt .
RUN pip install --no-cache-dir --target /deps -r requirements-dev.txt
COPY app ./app
COPY tests ./tests
COPY pytest.ini .
# Tests run during the image build, so a broken image cannot be produced.
RUN PYTHONPATH=/deps:. /deps/bin/pytest

FROM python:3.12-slim AS runtime
ARG APP_VERSION=dev
WORKDIR /app
# Run as a non-root user.
RUN useradd --create-home --uid 10001 yatri
COPY --from=build /src/app ./app
USER yatri
ENV PORT=8000 APP_VERSION=${APP_VERSION}
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/health')"
CMD ["python", "-m", "app.main"]
