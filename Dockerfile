FROM python:3.10-slim

# 環境変数
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 作業ディレクトリ作成
WORKDIR /app

# 依存ファイルをコピー
COPY requirements.txt .

# パッケージをインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリコードをコピー
COPY . .

# 実行コマンド
CMD ["python", "disbot_koyeb.py"]
