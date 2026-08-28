FROM mcr.microsoft.com/playwright/python:v1.62.0-noble

ARG UID=1000
ARG GID=1000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data && chown -R ${UID}:${GID} /app

USER ${UID}:${GID}

CMD ["python", "main.py"]