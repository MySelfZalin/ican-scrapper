FROM python:3.14-bookworm

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt && \
    playwright install --with-deps chromium

COPY . .

CMD ["python3", "main.py"]
