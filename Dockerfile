FROM python:3.11-slim

WORKDIR /app

# 必要ファイルをコンテナにコピー
COPY disbot_koyeb.py ./
# 初期化用ファイル（必要に応じて）
COPY schedules.json ./
COPY requirements.txt ./

# パッケージをインストール
RUN pip install --no-cache-dir -r requirements.txt

# ポートは公開しない（Koyeb ヘルスチェック無効化）
# EXPOSE なし

# 実行
CMD ["python", "disbot_koyeb.py"]
