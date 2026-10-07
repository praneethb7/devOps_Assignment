FROM python:3.12-slim
WORKDIR /app
COPY app.py .
RUN useradd --create-home --uid 10001 yatri
USER yatri
EXPOSE 8000
CMD ["python", "app.py"]
