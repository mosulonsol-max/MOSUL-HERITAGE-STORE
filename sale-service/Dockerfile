FROM python:3.12-slim

WORKDIR /app
COPY core.py server.py auction.py readiness.py delivery.py ./
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY products ./products

RUN useradd --create-home --uid 10001 sale && mkdir -p /app/data /app/private \
    && chown -R sale:sale /app

USER sale
ENV PYTHONUNBUFFERED=1 SALE_BIND=0.0.0.0 PORT=8080
EXPOSE 8080

CMD ["python", "server.py"]
