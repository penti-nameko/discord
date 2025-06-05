FROM python:3.11-slim

WORKDIR /app

COPY disbot_koyeb.py ./
COPY schedules.json ./
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "disbot_koyeb.py"]
