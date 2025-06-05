FROM python:3.11-slim

WORKDIR /app

# 必要ファイルをコンテナにコピー
COPY disbot_koyeb.py ./
COPY schedules.json ./   # 初期化用、不要なら削除可
COPY requirements.txt ./

# ライブラリをインストール
RUN pip install --no-cache-dir -r requirements.txt

# ⚠️ ポートは明示的に公開しない（KoyebのTCPヘルスチェック対象にしない）
# EXPOSE 8000 ← これを削除または記述しないことでヘルスチェック無効化

# Botの起動コマンド
CMD ["python", "disbot_koyeb.py"]
