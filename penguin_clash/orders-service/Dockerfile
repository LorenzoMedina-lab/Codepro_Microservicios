FROM python:3.11-slim

WORKDIR /app

COPY ./auth_shared.py /app/auth_shared.py
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app/

CMD ["python", "app.py"]