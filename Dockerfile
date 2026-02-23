FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
RUN python manage.py collectstatic --noinput

CMD ["python", "main.py" ]
