# Monitoring Service

Install dependencies and run the service.

Commands:

python -m pip install -r monitoring-service/requirements.txt

uvicorn monitoring-service.app:app --host 0.0.0.0 --port 9000
