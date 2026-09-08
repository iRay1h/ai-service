# Este Dockerfile no lo necesitas todavia para desarrollo local.
# Sirve para cuando quieran agregar este microservicio a su carpeta docker/
# y levantarlo junto con el backend y la base de datos.

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
