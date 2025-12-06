FROM python:3.11-slim
WORKDIR /app
COPY monitoring-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY monitoring-service /app/monitoring-service
ENV PYTHONPATH=/app
EXPOSE 9000
CMD ["uvicorn","monitoring-service.app:app","--host","0.0.0.0","--port","9000"]
