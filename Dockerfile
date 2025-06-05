FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 必要なライブラリを追加
RUN apt-get update && apt-get install -y gcc libffi-dev build-essential python3-dev

WORKDIR /app

COPY requirements.txt .

# pip周りをアップグレード
RUN pip install --upgrade pip setuptools wheel

# ライブラリインストール
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "disbot_koyeb.py"]
