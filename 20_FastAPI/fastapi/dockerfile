FROM python:3.11-slim

WORKDIR /auth_demo

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /auth_demo/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8090"]