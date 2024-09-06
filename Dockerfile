FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential libpq-dev

COPY requirements.txt .


RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

ENV DATABASE_URL='postgresql://XXXXXXXXXXXXXXXXXXXXXXXX'



COPY . .


CMD ["uvicorn", "main.main:app", "--host", "0.0.0.0", "--port", "8000"]
