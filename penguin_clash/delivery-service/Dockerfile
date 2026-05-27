FROM python:3.11-slim

WORKDIR /app

# 1. Copiar la lógica compartida de autenticación JWT de esta subcarpeta
COPY ./auth_shared.py /app/auth_shared.py

# 2. Copiar e instalar las dependencias aisladas del servicio de envíos
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copiar el resto del código modular (app.py, routes.py, models.py, config.py)
COPY . /app/

# 4. Comando de ejecución para arrancar el servidor Flask de logística
CMD ["python", "app.py"]