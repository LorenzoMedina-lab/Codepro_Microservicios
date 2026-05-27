FROM python:3.11-slim

WORKDIR /app

# 1. Copiar la lógica compartida de autenticación que está en la raíz
COPY ./auth_shared.py /app/auth_shared.py

# 2. Copiar e instalar las dependencias específicas de este servicio
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copiar el resto del código modular del servicio (app.py, routes.py, etc.)
COPY . /app/

# 4. Comando para arrancar la aplicación Flask
CMD ["python", "app.py"]