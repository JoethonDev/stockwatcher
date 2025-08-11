FROM python:3.12-alpine

RUN apk add --no-cache gcc musl-dev libpq-dev postgresql-dev

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "stockwatcher.wsgi:application"]
