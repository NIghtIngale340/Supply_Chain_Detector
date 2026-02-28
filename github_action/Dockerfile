FROM python:3.11-slim

WORKDIR /action

COPY scan_requirements.py /action/scan_requirements.py
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh && pip install --no-cache-dir requests

ENTRYPOINT ["/entrypoint.sh"]
