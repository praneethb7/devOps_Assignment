# Distroless runtime: no shell, no package manager, minimal CVE surface.
# That is a security control as much as a size optimisation - the image
# scanning stage has far less to find.
FROM python:3.12-slim AS build
WORKDIR /src
COPY requirements-dev.txt .
RUN pip install --no-cache-dir --target /deps -r requirements-dev.txt
COPY app ./app
COPY tests ./tests
COPY pytest.ini .
RUN BOOKING_SIGNING_KEY=build-time-only PYTHONPATH=/deps:. /deps/bin/pytest

FROM gcr.io/distroless/python3-debian12:nonroot AS runtime
ARG APP_VERSION=dev
WORKDIR /app
COPY --from=build /src/app ./app
ENV PORT=8000 APP_VERSION=${APP_VERSION} PYTHONPATH=/app
USER nonroot
EXPOSE 8000
ENTRYPOINT ["python", "-m", "app.server"]
